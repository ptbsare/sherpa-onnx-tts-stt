# Home Assistant Add-on: Sherpa Onnx TTS/STT

## Installation

Follow these steps to get the add-on installed on your system:

1. Navigate in your Home Assistant frontend to **Settings** -> **Add-ons** -> **Add-on store**.
2. Add the store https://github.com/ptbsare/home-assistant-addons
2. Find the "Sherpa Onnx TTS/STT" add-on and click it.
3. Click on the "INSTALL" button.

## How to use

After this add-on is installed and running, it will be automatically discovered
by the Wyoming integration in Home Assistant. To finish the setup,
click the following my button:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=wyoming)

Alternatively, you can install the Wyoming integration manually, see the
[Wyoming integration documentation](https://www.home-assistant.io/integrations/wyoming/)
for more information.

## Models

STT Models are automatically downloaded from [STT Model list on Github](https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models) and put into `/stt-models`.

TTS Models are automatically downloaded from [TTS Model list on Github](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models) and put into `/tts-models`.

## Configuration

### Option: `language`

DOCKER ENV LANGUAGE

Default language to use. eg. en default:zh-CN

### Option: `speed`

DOCKER ENV SPEED

TTS Speech Speed. eg. 1.0

### Option: `stt_model`

DOCKER ENV STT_MODEL

Name of the builtin model to use. eg. 
```
sherpa-onnx-paraformer-zh-2023-03-28
sherpa-onnx-paraformer-zh-small-2024-03-09
```
default: sherpa-onnx-paraformer-zh-2023-03-28
See the [models](#models) section for more details.

### Option: `stt_use_int8_onnx_model`

DOCKER ENV STT_USE_INT8_ONNX_MODEL

Enable int8 model to reduce memery usage. default: True

### Option: `stt_builtin_auto_convert_number`

DOCKER ENV STT_BUILTIN_AUTO_CONVERT_NUMBER

Enable STT auto convert Chinese numbers(eg. 一二三) to Arabic numerals (eg. 123) for better Hass intent compatibility. default: False

### Option: `stt_thread_num`

DOCKER ENV STT_THREAD_NUM

Number of Threads for TTS. default: 3

### Option: `stt_use_online_processing`

DOCKER ENV STT_USE_ONLINE_PROCESSING

Enable online/streaming STT processing for lower latency. default: False
    
### Option: `tts_model`

DOCKER ENV TTS_MODEL

Name of the builtin model to use. eg.
```
matcha-icefall-zh-baker
vits-melo-tts-zh_en
kokoro-int8-multi-lang-v1_1
```
default: matcha-icefall-zh-baker
### Option: `tts_thread_num`

DOCKER ENV TTS_THREAD_NUM

Number of Threads for TTS. default. 3

### Option: `tts_speaker_sid`

DOCKER ENV TTS_SPEAKER_SID

TTS Speaker ID. default. 0

### Option: `debug`

DOCKER ENV DEBUG

Enable debug logging. default. False

### Option: `custom_stt_model`

DOCKER ENV CUSTOM_STT_MODEL

For advanced users only. If you want to use stt models other than builtin stt models, please specify `custom_stt_model` and `custom_stt_model_eval`

`custom_stt_model` is name of the model to use. eg. sherpa-onnx-zipformer-cantonese-2024-03-13

Container will download the model from github and extract the model files to /stt-models/$CUSTOM_STT_MODEL/ folder.

See the [models](#models) section for list of models from github.

### Option: `custom_stt_model_eval`

DOCKER ENV CUSTOM_TTS_MODEL_EVAL

For advanced users only. If you want to use stt models other than builtin stt models, please specify `custom_stt_model` and `custom_stt_model_eval`

`custom_stt_model_eval` is python eval expression for building the model at runtime, this string is passed to the python `eval()` function. eg.

Similar to `custom_tts_model_eval` below.
Goto the [Sherpa Onnx repo STT Python examples](https://github.com/k2-fsa/sherpa-onnx/blob/master/python-api-examples/offline-decode-files.py) for more information.

### Option: `custom_tts_model`

DOCKER ENV CUSTOM_TTS_MODEL

For advanced users only. If you want to use tts models other than builtin tts models, please specify `custom_tts_model` and `custom_tts_model_eval`

`custom_tts_model` is name of the model to use. eg. vits-cantonese-hf-xiaomaiiwn

Container will download the model from github and extract the model files to /tts-models/$CUSTOM_TTS_MODEL/ folder.

See the [models](#models) section for list of models from github.

### Option: `custom_tts_model_eval`

DOCKER ENV CUSTOM_TTS_MODEL_EVAL

For advanced users only. If you want to use tts models other than builtin tts models, please specify `custom_tts_model` and `custom_tts_model_eval`

`custom_tts_model_eval` is python eval expression for building the model at runtime, this string is passed to the python `eval()` function. eg. 
```python
sherpa_onnx.OfflineTts(
sherpa_onnx.OfflineTtsConfig(
model=sherpa_onnx.OfflineTtsModelConfig(
kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
model="/tts-models/kokoro-multi-lang-v1_1/model.onnx",
voices="/tts-models/kokoro-multi-lang-v1_1/voices.bin",
lexicon="/tts-models/kokoro-multi-lang-v1_1/lexicon-zh.txt,/tts-models/kokoro-multi-lang-v1_1/lexicon-us-en.txt",
tokens="/tts-models/kokoro-multi-lang-v1_1/tokens.txt",
data_dir="/tts-models/kokoro-multi-lang-v1_1/espeak-ng-data",
dict_dir="/tts-models/kokoro-multi-lang-v1_1/dict",
),
provider="cpu",
num_threads=3,
debug=True,
),
rule_fsts="/tts-models/kokoro-multi-lang-v1_1/phone-zh.fst,/tts-models/kokoro-multi-lang-v1_1/date-zh.fst,/tts-models/kokoro-multi-lang-v1_1/number-zh.fst",                 
max_num_sentences=1,
)
)
```
Goto the [Sherpa Onnx repo TTS Python examples](https://github.com/k2-fsa/sherpa-onnx/blob/master/python-api-examples/offline-tts.py) for more information.

## Openai-format TTS/STT api support
Experimental Support for Openai-format TTS/STT api  IP:10500/v1/audio/speech IP:10500/v1/audio/transcriptions
添加Openai TTS/STT 实验性支持，实现了两个接口  IP:10500/v1/audio/speech IP:10500/v1/audio/transcriptions

## Examples
### Docker
```docker
DSM Container Manager:

services:
  certimate:
    image: ghcr.io/ptbsare/home-assistant-addons/amd64-addon-sherpa-onnx-tts-stt:latest
    container_name: sherpa-onnx-tts-stt
    environment:
      LANGUAGE: "zh-CN"
      STT_MODEL: "sherpa-onnx-paraformer-zh-2023-03-28"
      SPEED: "1.2"
      STT_USE_INT8_ONNX_MODEL: "True"
      STT_THREAD_NUM: "3"
      TTS_MODEL: "matcha-icefall-zh-baker"
      TTS_THREAD_NUM: "3"
      TTS_SPEAKER_SID: "0"
      DEBUG: "True"
    ports:
      - 10400:10400
    restart: unless-stopped
```
### CUSTOM TTS MODELS(For advanced users only)
```docker
services:
  certimate:
    image: ghcr.io/ptbsare/home-assistant-addons/amd64-addon-sherpa-onnx-tts-stt:0.2.8
    container_name: sherpa-onnx-tts-stt
    environment:
      LANGUAGE: "zh-CN"

      STT_USE_INT8_ONNX_MODEL: "True"
      STT_THREAD_NUM: "8"

      CUSTOM_TTS_MODEL: "vits-melo-tts-zh_en"
      CUSTOM_TTS_MODEL_EVAL: |
        sherpa_onnx.OfflineTts(
          sherpa_onnx.OfflineTtsConfig(
          model=sherpa_onnx.OfflineTtsModelConfig(
          vits=sherpa_onnx.OfflineTtsVitsModelConfig(
          model="/tts-models/vits-melo-tts-zh_en/model.onnx",
          lexicon="/tts-models/vits-melo-tts-zh_en/lexicon.txt",
          tokens="/tts-models/vits-melo-tts-zh_en/tokens.txt",
          dict_dir="/tts-models/vits-melo-tts-zh_en/dict",
          ),
         provider="cpu",
         num_threads=8,
          debug=True,
          ),
          rule_fsts="/tts-models/vits-melo-tts-zh_en/phone.fst,/tts-models/vits-melo-tts-zh_en/date.fst,/tts-models/vits-melo-tts-zh_en/number.fst",                 
          max_num_sentences=1,
          )
        )
      DEBUG: "True"
    ports:
      - 10400:10400
    restart: unless-stopped
```
### CUSTOM STT MODELS(For advanced users only)(Cantonese STT)
```docker
定义模型例子（粤语stt例子）（Docker/高阶用户）
language: zh-CN
speed: 1
stt_model: custom_stt_model
stt_use_int8_onnx_model: true
stt_thread_num: 3
tts_model: vits-melo-tts-zh_en
tts_thread_num: 3
tts_speaker_sid: 0
debug: true
custom_stt_model: sherpa-onnx-zipformer-cantonese-2024-03-13
custom_stt_model_eval: |-
  sherpa_onnx.OfflineRecognizer.from_transducer(      
    encoder="/stt-models/sherpa-onnx-zipformer-cantonese-2024-03-13/encoder-epoch-45-avg-35.int8.onnx",      
    decoder="/stt-models/sherpa-onnx-zipformer-cantonese-2024-03-13/decoder-epoch-45-avg-35.int8.onnx",      
    joiner="/stt-models/sherpa-onnx-zipformer-cantonese-2024-03-13/joiner-epoch-45-avg-35.int8.onnx",      
    tokens="/stt-models/sherpa-onnx-zipformer-cantonese-2024-03-13/tokens.txt",
    num_threads=3,
    decoding_method="greedy_search",
    provider="cpu",
    sample_rate=16000,
    feature_dim=80,
    debug=True
  )
```