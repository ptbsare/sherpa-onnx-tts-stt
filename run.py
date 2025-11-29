# Home Assistant Add-on: sherpa-onnx-tts-stt
import logging
import os
import subprocess
import asyncio
import argparse
from functools import partial
import numpy as np
import math

from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioChunkConverter, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.info import AsrModel, AsrProgram, TtsVoice, TtsProgram, Describe, Info, Attribution
from wyoming.server import AsyncEventHandler, AsyncTcpServer
from wyoming.tts import Synthesize

import sherpa_onnx
from model_utils import initialize_models
import uvicorn
from model_container import ModelContainer
import api

_LOGGER = logging.getLogger("sherpa_onnx_addon")

class SherpaOnnxEventHandler(AsyncEventHandler):
    """Event handler for sherpa-onnx TTS and STT."""

    def __init__(
        self,
        wyoming_info: Info,
        cli_args,
        tts_model,
        stt_model,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.cli_args = cli_args
        self.wyoming_info_ = wyoming_info
        self.tts_model = tts_model
        self.stt_model = stt_model
        self.audio_converter = AudioChunkConverter(rate=16000, width=2, channels=1)

        self.is_stt_online = hasattr(self.stt_model, 'is_ready')
        self.audio = b""
        self.audio_min_len = 1024
        if self.cli_args.stt_use_online_processing and self.is_stt_online:
            _LOGGER.debug("Using online processing")

    async def handle_event(self, event: Event) -> bool:
        """Handles a single event."""
        _LOGGER.debug("Received event: %s", event)
        if Describe.is_type(event.type):
            await self.write_event(self.wyoming_info_.event())
            return True

        if Synthesize.is_type(event.type):
            synthesize = Synthesize.from_event(event)
            # Determine speaker ID
            speaker_id = self.cli_args.tts_speaker_sid # Default speaker ID from config/args
            voice_name_from_event = None
            if synthesize.voice and synthesize.voice.name:
                voice_name_from_event = synthesize.voice.name
                try:
                    speaker_id_from_event = int(voice_name_from_event)
                    speaker_id = speaker_id_from_event
                    _LOGGER.debug(f"Using speaker ID from event voice name '{voice_name_from_event}': {speaker_id}")
                except (ValueError, TypeError):
                    _LOGGER.warning(
                        f"Invalid speaker ID received in event voice name: '{voice_name_from_event}'. Falling back to default: {speaker_id}"
                    )
            else:
                _LOGGER.debug(f"No specific voice name provided in event. Using default speaker ID: {speaker_id}")


            audio = self.tts_model.generate(
                text=synthesize.text,
                sid=speaker_id,
                speed=self.cli_args.speed,
            )
            _LOGGER.debug(f"Synthesizing: {synthesize.text}")
            if isinstance(audio.samples, (list, np.ndarray)):
                audio_samples = np.array(audio.samples, dtype=np.float32)
            else:
                raise TypeError(
                    "Unexpected type for audio.samples: {}".format(type(audio.samples))
                )

            audio_samples = (audio_samples * 32767).astype(np.int16)
            audio_bytes = audio_samples.tobytes()

            await self.write_event(AudioStart(rate=audio.sample_rate, width=2, channels=1).event())
            _LOGGER.debug("Sent Audio Start")

            bytes_per_chunk = 1024
            for i in range(0, len(audio_bytes), bytes_per_chunk):
                chunk = audio_bytes[i : i + bytes_per_chunk]
                await self.write_event(
                    AudioChunk(
                        audio=chunk,
                        rate=audio.sample_rate,
                        width=2,
                        channels=1,
                    ).event()
                )
            _LOGGER.debug("Sent TTS Chunks")

            await self.write_event(AudioStop().event())
            _LOGGER.debug("Sent Audio Stop")
            return True

        elif Transcribe.is_type(event.type):
            _LOGGER.debug(f"Received Transcribe request")
            return True

        elif AudioStart.is_type(event.type):
            _LOGGER.debug(f"Received audio start event")
            audio_start = AudioStart.from_event(event)
            self.audio_recv_rate = audio_start.rate
            self.audio_min_len = int(0.15 * self.audio_recv_rate) # 150ms
            self.stream = self.stt_model.create_stream()
            self.audio = b""
            return True

        elif AudioChunk.is_type(event.type):
            audio_chunk = AudioChunk.from_event(event)

            chunk = self.audio_converter.convert(audio_chunk)
            _LOGGER.debug("Processing audio chunk...")


            if self.is_stt_online and self.cli_args.stt_use_online_processing:
                audio_array = np.frombuffer(chunk.audio, dtype=np.int16).astype(np.float32) / 32768
                self.stream.accept_waveform(self.audio_recv_rate, audio_array)
                while self.stt_model.is_ready(self.stream):
                    self.stt_model.decode_stream(self.stream)

                if self.stt_model.is_endpoint(self.stream):
                    _LOGGER.debug("Endpoint detected")
                    await self.write_event(AudioStop().event())
            else:
                self.audio += chunk.audio

            return True

        elif AudioStop.is_type(event.type):
            try:
                audio_stop = AudioStop.from_event(event)
                _LOGGER.debug("Receive audio stop: %s", audio_stop)
                result = None

                if self.audio:
                    audio_array = np.frombuffer(self.audio, dtype=np.int16).astype(np.float32) / 32768
                    # pad last buffer with silence
                    audio_array = np.pad(audio_array, (0, self.audio_min_len), 'constant')
                    self.stream.accept_waveform(self.audio_recv_rate, audio_array)

                if self.is_stt_online:
                    # Inject some silence on online models
                    tail_paddings = np.zeros(int(0.5 * self.audio_recv_rate), dtype=np.float32)
                    self.stream.accept_waveform(self.audio_recv_rate, tail_paddings)
                    self.stream.input_finished()

                    while self.stt_model.is_ready(self.stream):
                        self.stt_model.decode_stream(self.stream)

                    result = self.stt_model.get_result(self.stream)
                else:
                    self.stt_model.decode_stream(self.stream)
                    result = getattr(self.stream.result, "text")

                _LOGGER.debug(result)
            except Exception as e:
                _LOGGER.debug("Error during decoding stream, no valid text recognized: %s", e)

            if result:
                await self.write_event(Transcript(text=result).event())
                _LOGGER.debug("Final transcript on stop: %s", result)
            else:
                await self.write_event(Transcript(text='').event())
                _LOGGER.debug("Empty transcript result event.")

            return True
        return False



async def main() -> None:
    """Main entry point."""
    def bool_type(text):
        return str(text).lower() in ['true','1', 'yes']

    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", default="default", help="Wyoming pipeline")
    parser.add_argument("--language", type=str, default=os.environ.get('LANGUAGE'), help="Language for TTS")
    parser.add_argument("--speed", type=float, default=float(os.environ.get('SPEED') or 1.0), help="Speech speed")
    parser.add_argument("--stt_use_online_processing", type=bool_type, default=os.environ.get('STT_USE_ONLINE_PROCESSING', 'false'), help="Use online processing")
    parser.add_argument("--stt_model", type=str, default=os.environ.get('STT_MODEL'), help="STT model name")
    parser.add_argument("--stt_use_int8_onnx_model", type=bool_type, default=os.environ.get('STT_USE_INT8_ONNX_MODEL', 'false'), help="Use int8 STT model")
    parser.add_argument("--stt_builtin_auto_convert_number", type=bool_type, default=os.environ.get('STT_BUILTIN_AUTO_CONVERT_NUMBER', 'false'), help="Enable builtin STT number convert")
    parser.add_argument("--stt_thread_num", type=int, default=int(os.environ.get('STT_THREAD_NUM') or 2), help="STT threads")
    parser.add_argument("--tts_model", type=str, default=os.environ.get('TTS_MODEL'), help="TTS model name")
    parser.add_argument("--tts_thread_num", type=int, default=int(os.environ.get('TTS_THREAD_NUM') or 2), help="TTS threads")
    parser.add_argument("--tts_speaker_sid", type=int, default=int(os.environ.get('TTS_SPEAKER_SID') or 0), help="TTS speaker ID")
    parser.add_argument("--debug", type=bool_type, default=os.environ.get('DEBUG', 'false'), help="Enable debug logging")
    parser.add_argument("--custom_stt_model_eval", type=str, default=os.environ.get('CUSTOM_STT_MODEL_EVAL', 'null'), help="Custom STT model eval")
    parser.add_argument("--custom_tts_model_eval", type=str, default=os.environ.get('CUSTOM_TTS_MODEL_EVAL', 'null'), help="Custom TTS model eval")
    parser.add_argument("--run", type=bool_type, default=True, help="Run the main thread")
    parser.add_argument("--host", default="0.0.0.0", help="Host for Wyoming and API")
    parser.add_argument("--port", type=int, default=10400, help="Port for Wyoming")
    parser.add_argument("--api_port", type=int, default=10500, help="Port for FastAPI")
    parser.add_argument("--provider", type=str, default='cpu', help="Execution provider (cpu, cuda)")

    cli_args = parser.parse_args()

    if cli_args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        subprocess.check_output('nvidia-smi')
        _LOGGER.info('Nvidia GPU detected!')
        cli_args.provider = 'cuda'
    except Exception:
        _LOGGER.info('No Nvidia GPU in system! CPU is used by default')
        cli_args.provider = 'cpu'

    _LOGGER.info("Starting sherpa-onnx add-on...")

    # Wyoming Info
    tts_voices = []
    voice_attribution = Attribution(name="k2-fsa", url="https://github.com/k2-fsa/sherpa-onnx")
    voice_installed = True
    voice_version = "0.0.1"

    # Assuming speakers 0 to 100 based on user feedback.
    num_speakers = 101

    for i in range(num_speakers): # Loop from 0 to 100
        speaker_id_str = str(i)
        speaker_desc = f"speaker{i}"
        tts_voices.append(
            TtsVoice(
                name=speaker_id_str,
                description=speaker_desc,
                languages=[cli_args.language],
                attribution=voice_attribution,
                installed=voice_installed,
                version=voice_version,
            )
        )

    wyoming_info = Info(
        asr=[
            AsrProgram(
                name="Sherpa Onnx Offline STT", # Consider making this dynamic if possible
                description="Sherpa Onnx Offline STT.",
                attribution=Attribution(name="k2-fsa", url="https://github.com/k2-fsa/sherpa-onnx"),
                installed=True,
                version="0.0.1",
                models=[
                    AsrModel(
                        name=cli_args.stt_model if cli_args.stt_model else "default",
                        description="ASR Model.",
                        languages=[cli_args.language],
                        attribution=Attribution(name="k2-fsa", url="https://github.com/k2-fsa/sherpa-onnx"),
                        installed=True,
                        version="0.0.1",
                    )
                ],
            )
        ],
        tts=[
            TtsProgram(
                name="Sherpa Onnx Offline TTS", # Consider making this dynamic if possible
                description="Sherpa Onnx Offline TTS.",
                attribution=Attribution(name="k2-fsa", url="https://github.com/k2-fsa/sherpa-onnx"),
                installed=True,
                version="0.0.1",
                voices=tts_voices,
            )
        ],
    )
    stt_model, tts_model = initialize_models(cli_args)

    if cli_args.run:
        # Run Wyoming server in a separate task
        wyoming_server = AsyncTcpServer(cli_args.host, cli_args.port)
        wyoming_task = asyncio.create_task(
            wyoming_server.run(
                partial(
                    SherpaOnnxEventHandler,
                    wyoming_info,
                    cli_args,
                    tts_model,
                    stt_model,
                )
            )

        )

        # Run FastAPI server using uvicorn
        _LOGGER.info(f"Starting Wyoming server at {cli_args.host}:{cli_args.port}")
        _LOGGER.info(f"Starting FastAPI server at 0.0.0.0:{cli_args.api_port}")

        api._model_container = ModelContainer(stt_model=stt_model, tts_model=tts_model)

        config = uvicorn.Config(
            "api:app",
            host="0.0.0.0",
            port=cli_args.api_port,
            log_level="debug" if cli_args.debug else "info",
        )
        server = uvicorn.Server(config)

        await asyncio.gather(wyoming_task, server.serve())
        _LOGGER.info("Stopped")

if __name__ == "__main__":
    asyncio.run(main())
