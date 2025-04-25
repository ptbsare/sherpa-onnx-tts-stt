from fastapi import FastAPI, HTTPException, UploadFile, File, Response, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import numpy as np
import io
from typing import Optional, Any
import logging
import re
from pydub import AudioSegment  # Import pydub
#from run import model_container # Removed circular import
from model_container import ModelContainer
from pydantic import Field

# Global variable to hold the models (will be initialized in run.py)
_model_container: ModelContainer = None

def get_models() -> ModelContainer:
    # Use the global _model_container
    if _model_container is None:
      raise Exception("Model container not initialized")
    return _model_container

app = FastAPI()
_LOGGER = logging.getLogger("sherpa_onnx_api")

# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    _LOGGER.debug("Middleware called")  # Simple log message
    response = await call_next(request)
    return response

class TranscribeRequest(BaseModel):
    file: bytes
    language: Optional[str] = None


@app.post("/v1/audio/transcriptions")
async def transcribe_audio(request: Request, file: UploadFile = File(...), language: Optional[str] = None, models: ModelContainer = Depends(get_models)):
    _LOGGER.debug(f"Received request: {request.method} {request.url}")
    _LOGGER.debug(f"Headers: {request.headers}")
    try:
        contents = await file.read()
        _LOGGER.debug(f"Body (truncated): {contents[:100]}...")  # Log truncated body

        # Use pydub to read the audio file (handles format detection)
        audio = AudioSegment.from_file(io.BytesIO(contents))

        # Convert to 16kHz, mono, 16-bit PCM
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)

        # Get raw audio data as bytes
        audio_data = audio.raw_data

        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        stream = models.stt_model.create_stream()
        stream.accept_waveform(16000, audio_array)
        models.stt_model.decode_stream(stream)
        result = stream.result

        if result and result.text:
            return {"text": result.text}
        else:
            return {"text": ""}

    except Exception as e:
        _LOGGER.exception(f"Error during STT: {e}")
        raise HTTPException(status_code=500, detail=str(e))
class TTSRequest(BaseModel):
    text: str = Field(..., alias="input")
    model: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None


@app.post("/v1/audio/speech")
async def generate_speech(request: Request, tts_request: TTSRequest, models: ModelContainer = Depends(get_models)):
    _LOGGER.debug(f"Received request: {request.method} {request.url}")
    _LOGGER.debug(f"Headers: {request.headers}")
    _LOGGER.debug(f"Body: {tts_request.dict()}")

    try:
        # Use provided values or defaults
        speaker_id = 0  # Default speaker ID
        if tts_request.voice is not None:
            match = re.match(r"speaker(\d+)", tts_request.voice)
            if match:
                try:
                    speaker_id = int(match.group(1))
                    _LOGGER.debug(f"Parsed speaker ID {speaker_id} from voice '{tts_request.voice}'")
                except (ValueError, IndexError):
                    _LOGGER.warning(f"Could not parse speaker ID from voice '{tts_request.voice}', using default {speaker_id}")
            # elif tts_request.voice == "aishell3":
            #     speaker_id = 0  
            else:
                 _LOGGER.debug(f"Voice '{tts_request.voice}' did not match expected pattern 'speaker<N>-<M>', using default speaker ID {speaker_id}")

        speed = tts_request.speed if tts_request.speed is not None else 1.0
        _LOGGER.debug(f"TTS Request: text={tts_request.text}, speaker_id={speaker_id}, speed={speed}")

        audio = models.tts_model.generate(
            text=tts_request.text,
            sid=speaker_id,
            speed=speed,
        )
        if isinstance(audio.samples, (list, np.ndarray)):
            audio_samples = np.array(audio.samples, dtype=np.float32)
        else:
            raise TypeError(
                "Unexpected type for audio.samples: {}".format(type(audio.samples))
            )
        audio_samples = (audio_samples * 32767).astype(np.int16)
        audio_bytes = audio_samples.tobytes()
        original_sample_rate = int(audio.sample_rate)

        # Use pydub to handle resampling and WAV export
        try:
            # Create AudioSegment from raw bytes
            original_audio = AudioSegment(
                data=audio_bytes,
                sample_width=2,  # 16-bit
                frame_rate=original_sample_rate,
                channels=1       # Mono
            )

            # Resample to 44100 Hz if necessary
            if original_sample_rate != 44100:
                _LOGGER.debug(f"Resampling audio from {original_sample_rate} Hz to 44100 Hz")
                resampled_audio = original_audio.set_frame_rate(44100)
            else:
                _LOGGER.debug("Audio already at 44100 Hz, no resampling needed.")
                resampled_audio = original_audio # Use original if already correct rate

            # Export to an in-memory WAV file
            wav_buffer = io.BytesIO()
            resampled_audio.export(wav_buffer, format="wav")
            wav_buffer.seek(0) # Rewind buffer to the beginning for reading
            wav_data = wav_buffer.read()

            headers = {
                "Content-Type": "audio/wav",
                "Content-Security-Policy": "media-src * data: blob:;" # Added CSP header for broader compatibility
            }
            return StreamingResponse(io.BytesIO(wav_data), media_type="audio/wav", headers=headers)

        except Exception as pydub_error:
            _LOGGER.exception(f"Error during pydub processing: {pydub_error}")
            raise HTTPException(status_code=500, detail=f"Error processing audio with pydub: {pydub_error}")

    except Exception as e:
        _LOGGER.exception(f"Error during TTS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    

@app.get("/health")
async def health_check():
    return {"status": "ok"}

