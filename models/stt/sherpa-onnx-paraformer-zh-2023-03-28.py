import sherpa_onnx
import os
import model_utils


def load(cli_args):
    stt_model = "sherpa-onnx-paraformer-zh-2023-03-28"
    stt_model_dir = os.environ.get("STT_MODEL_DIR", "/stt-models")

    model_utils.fetch_stt_model(stt_model_dir, stt_model)

    return sherpa_onnx.OfflineRecognizer.from_paraformer(
        paraformer=os.path.join(
            stt_model_dir,
            stt_model,
            (
                "model.int8.onnx"
                if cli_args.stt_use_int8_onnx_model == True
                else "model.onnx"
            ),
        ),
        tokens=os.path.join(stt_model_dir, stt_model, "tokens.txt"),
        decoding_method="greedy_search",
        provider=cli_args.provider,
        num_threads=cli_args.stt_thread_num,  # Adjust based on your hardware
        sample_rate=16000,
        feature_dim=80,
        debug=cli_args.debug,
        rule_fsts=(
            os.path.join("/app/", "itn_zh_number.fst")
            if cli_args.stt_builtin_auto_convert_number
            else ""
        ),
    )
