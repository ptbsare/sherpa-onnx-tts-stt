import sherpa_onnx
import os
import model_utils


def load(cli_args):
    tts_model = "vits-melo-tts-zh_en"
    tts_model_dir = os.environ.get("TTS_MODEL_DIR", "/tts-models")

    model_utils.fetch_tts_model(tts_model_dir, tts_model)

    return sherpa_onnx.OfflineTts(
        sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=os.path.join(tts_model_dir, tts_model, "model.onnx"),
                    lexicon=os.path.join(tts_model_dir, tts_model, "lexicon.txt"),
                    tokens=os.path.join(tts_model_dir, tts_model, "tokens.txt"),
                    dict_dir=os.path.join(tts_model_dir, tts_model, "dict"),
                ),
                provider=cli_args.provider,
                num_threads=cli_args.tts_thread_num,
                debug=cli_args.debug,
            ),
            rule_fsts=f"{tts_model_dir}/{tts_model}/phone.fst,{tts_model_dir}/{tts_model}/date.fst,{tts_model_dir}/{tts_model}/number.fst,{tts_model_dir}/{tts_model}/new_heteronym.fst",
            max_num_sentences=1,
        )
    )
