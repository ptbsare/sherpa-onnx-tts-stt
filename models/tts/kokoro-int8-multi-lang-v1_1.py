import sherpa_onnx
import os
import model_utils


def load(cli_args):
    tts_model = "kokoro-int8-multi-lang-v1_1"
    tts_model_dir = os.environ.get("TTS_MODEL_DIR", "/tts-models")

    model_utils.fetch_tts_model(tts_model_dir, tts_model)

    return sherpa_onnx.OfflineTts(
        sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                    model=os.path.join(tts_model_dir, tts_model, "model.int8.onnx"),
                    voices=os.path.join(tts_model_dir, tts_model, "voices.bin"),
                    lexicon=f"{tts_model_dir}/{tts_model}/lexicon-zh.txt,{tts_model_dir}/{tts_model}/lexicon-us-en.txt",
                    tokens=os.path.join(tts_model_dir, tts_model, "tokens.txt"),
                    data_dir=os.path.join(tts_model_dir, tts_model, "espeak-ng-data"),
                    dict_dir=os.path.join(tts_model_dir, tts_model, "dict"),
                ),
                provider=cli_args.provider,
                num_threads=cli_args.tts_thread_num,
                debug=cli_args.debug,
            ),
            rule_fsts=f"{tts_model_dir}/{tts_model}/phone-zh.fst,{tts_model_dir}/{tts_model}/date-zh.fst,{tts_model_dir}/{tts_model}/number-zh.fst",
            max_num_sentences=1,
        )
    )
