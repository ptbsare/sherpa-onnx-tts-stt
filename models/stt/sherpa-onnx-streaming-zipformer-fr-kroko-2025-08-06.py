import sherpa_onnx
import os
import model_utils


def load(cli_args):
    stt_model = "sherpa-onnx-streaming-zipformer-fr-kroko-2025-08-06"
    stt_model_dir = os.environ.get("STT_MODEL_DIR", "/stt-models")

    model_utils.fetch_stt_model(stt_model_dir, stt_model)

    return sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=os.path.join(stt_model_dir, stt_model, "tokens.txt"),
        encoder=os.path.join(stt_model_dir, stt_model, "encoder.onnx"),
        decoder=os.path.join(stt_model_dir, stt_model, "decoder.onnx"),
        joiner=os.path.join(stt_model_dir, stt_model, "joiner.onnx"),
        num_threads=cli_args.stt_thread_num,
        decoding_method="greedy_search",
        sample_rate=16000,
        feature_dim=80,
        debug=cli_args.debug,
    )
