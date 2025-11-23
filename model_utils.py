# sherpa-onnx-tts-stt/model_utils.py
import os
import subprocess
import logging
import sherpa_onnx
import importlib
import sys

_LOGGER = logging.getLogger("sherpa_onnx_model_utils")


def _download_model(model_url, model_dir, model):
    """Downloads and extracts the model."""
    if not os.path.exists(os.path.join(model_dir, model)):
        _LOGGER.info(f"Downloading model: {model_url}")
        os.makedirs(os.path.join(model_dir, model), exist_ok=True)

        # Use curl (or wget) for download and extraction (more robust than Python libraries for large files)
        try:
            subprocess.check_call(
                [
                    "curl",
                    "-L",
                    model_url,
                    "-o",
                    os.path.join(model_dir, model, f"{model}.tar.gz"),
                ]
            )
            _LOGGER.info(f"Downloaded model: {model_url}, Extracting...")
            subprocess.check_call(
                [
                    "tar",
                    "-xvf",
                    os.path.join(model_dir, model, f"{model}.tar.gz"),
                    "-C",
                    model_dir,
                ]
            )
            os.remove(os.path.join(model_dir, model, f"{model}.tar.gz"))  # Clean up
            _LOGGER.info(f"Download and extract Done. Cleaned up.")
        except subprocess.CalledProcessError as e:
            _LOGGER.error(f"Error downloading or extracting  model: {e}")
            raise  #  Re-raise to stop add-on startup on failure
    else:
        _LOGGER.info(f"{model} model already exists.")


def fetch_stt_model(stt_model_dir, model):
    # --- STT Model ---
    stt_model_url = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{model}.tar.bz2"
    _download_model(stt_model_url, stt_model_dir, model)


def fetch_tts_model(tts_model_dir, model):
    # --- TTS Model ---
    tts_model_url = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{model}.tar.bz2"
    _download_model(tts_model_url, tts_model_dir, model)


def load_module(file):
    spec = importlib.util.spec_from_file_location("model", file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_builtin_model(model, language, project_dir, model_type):
    if model:
        return os.path.join(
            project_dir,
            "models",
            model_type,
            f"{model}.py",
        )
    elif language:
        model = os.path.join(project_dir, "models", model_type, "lang", language)
        if os.path.exists(model):
            return os.path.realpath(model)
    return None


def initialize_models(cli_args):
    """Initializes STT and TTS models based on CLI arguments."""

    stt_model_dir = "/stt-models"
    tts_model_dir = "/tts-models"
    os.environ.setdefault("STT_MODEL_DIR", "/stt-models")
    os.environ.setdefault("TTS_MODEL_DIR", "/tts-models")
    project_dir = os.path.dirname(os.path.realpath(__file__))

    # STT Initialization (adjust paths as needed for extracted model)
    try:
        if cli_args.custom_stt_model_eval != "null":
            if cli_args.stt_model:
                fetch_stt_model(stt_model_dir, cli_args.stt_model)
            stt_model = eval(cli_args.custom_stt_model_eval)
        else:
            model_file = find_builtin_model(
                cli_args.stt_model, cli_args.language, project_dir, "stt"
            )
            stt_model = load_module(model_file).load(cli_args) if model_file else None
    except Exception as e:
        _LOGGER.critical("Failed to initialize custom STT model: %s", e)
        raise

    try:
        # TTS Initialization
        if cli_args.custom_tts_model_eval != "null":
            if cli_args.tts_model:
                fetch_tts_model(tts_model_dir, cli_args.tts_model)
            tts_model = eval(cli_args.custom_tts_model_eval)
        else:
            model_file = find_builtin_model(
                cli_args.tts_model, cli_args.language, project_dir, "tts"
            )
            tts_model = load_module(model_file).load(cli_args) if model_file else None
    except Exception as e:
        _LOGGER.critical("Failed to initialize custom TTS model: %s", e)
        raise

    return stt_model, tts_model
