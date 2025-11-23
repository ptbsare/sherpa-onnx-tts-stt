import sherpa_onnx
import os
import model_utils


def load(cli_args):
    tts_model = "matcha-icefall-zh-baker"
    tts_model_dir = os.environ.get("TTS_MODEL_DIR", "/tts-models")

    model_utils.fetch_tts_model(tts_model_dir, tts_model)

    return sherpa_onnx.OfflineTts(
        sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                matcha=sherpa_onnx.OfflineTtsMatchaModelConfig(
                    acoustic_model=os.path.join(
                        tts_model_dir, tts_model, "model-steps-3.onnx"
                    ),
                    vocoder=os.path.join(tts_model_dir, "hifigan_v2.onnx"),
                    lexicon=os.path.join(tts_model_dir, tts_model, "lexicon.txt"),
                    tokens=os.path.join(tts_model_dir, tts_model, "tokens.txt"),
                    data_dir=os.path.join(tts_model_dir, "espeak-ng-data"),
                    dict_dir=os.path.join(tts_model_dir, tts_model, "dict"),
                ),
                provider=cli_args.provider,  # or "cuda" if you have a GPU
                num_threads=cli_args.tts_thread_num,  # Adjust as needed
                debug=cli_args.debug,  # Set to True for debugging output
            ),
            rule_fsts=f"{tts_model_dir}/{tts_model}/phone.fst,{tts_model_dir}/{tts_model}/date.fst,{tts_model_dir}/{tts_model}/number.fst",  # Example rule FSTs, adjust path if needed
            max_num_sentences=1,
        )
    )
