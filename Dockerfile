ARG BUILD_TYPE=cpu
ARG CPU_PLATFORM=python:3.11.9-slim-bullseye
ARG GPU_PLATFORM=nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Set TARGET_PLATFORM based on BUILD_TYPE
#ARG TARGET_PLATFORM
#RUN if [ "$BUILD_TYPE" = "cuda" ]; then
#    export TARGET_PLATFORM=$GPU_PLATFORM;
#else
#    export TARGET_PLATFORM=$CPU_PLATFORM;
#fi

#FROM --platform=$TARGET_PLATFORM ${TARGET_PLATFORM}
FROM ${CPU_PLATFORM}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG S6_OVERLAY_VERSION_DEFAULT="3.2.0.2"
ENV S6_OVERLAY_VERSION=${S6_OVERLAY_VERSION_DEFAULT}

# Conditional sections for GPU base image
RUN if [ "$BUILD_TYPE" = "cuda" ]; then \
    export CARGO_NET_GIT_FETCH_WITH_CLI=true; \
    export DEBIAN_FRONTEND="noninteractive"; \
    export HOME="/root"; \
    export LANG="C.UTF-8"; \
    export PIP_DISABLE_PIP_VERSION_CHECK=1; \
    export PIP_NO_CACHE_DIR=1; \
    export PIP_PREFER_BINARY=1; \
    export PS1='$(whoami)@$(hostname):$(pwd)$ '; \
    export PYTHONDONTWRITEBYTECODE=1; \
    export PYTHONUNBUFFERED=1; \
    export S6_BEHAVIOUR_IF_STAGE2_FAILS=2; \
    export S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0; \
    export S6_CMD_WAIT_FOR_SERVICES=1; \
    export YARN_HTTP_TIMEOUT=1000000; \
    export TERM="xterm-256color"; \
    export BUILD_ARCH=amd64; \
    export BASHIO_VERSION="v0.16.2"; \
    export S6_OVERLAY_VERSION="3.2.0.2"; \
    export TEMPIO_VERSION="2024.11.2"; \
    apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl jq tzdata xz-utils && \
    S6_ARCH="${BUILD_ARCH}" && \
    if [ "${BUILD_ARCH}" = "i386" ]; then S6_ARCH="i686"; \
    elif [ "${BUILD_ARCH}" = "amd64" ]; then S6_ARCH="x86_64"; \
    elif [ "${BUILD_ARCH}" = "armv7" ]; then S6_ARCH="arm"; fi && \
    curl -L -s "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" | tar -C / -Jxpf - && \
    curl -L -s "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" | tar -C / -Jxpf - && \
    curl -L -s "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-symlinks-noarch.tar.xz" | tar -C / -Jxpf - && \
    curl -L -s "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-symlinks-arch.tar.xz" | tar -C / -Jxpf - && \
    mkdir -p /etc/fix-attrs.d && \
    mkdir -p /etc/services.d && \
    curl -J -L -o /tmp/bashio.tar.gz "https://github.com/hassio-addons/bashio/archive/${BASHIO_VERSION}.tar.gz" && \
    mkdir /tmp/bashio && \
    tar zxvf /tmp/bashio.tar.gz --strip 1 -C /tmp/bashio && \
    mv /tmp/bashio/lib /usr/lib/bashio && \
    ln -s /usr/lib/bashio/bashio /usr/bin/bashio && \
    curl -L -s -o /usr/bin/tempio "https://github.com/home-assistant/tempio/releases/download/${TEMPIO_VERSION}/tempio_${BUILD_ARCH}" && \
    chmod a+x /usr/bin/tempio && \
    apt-get purge -y --auto-remove xz-utils && \
    apt-get clean && \
    rm -fr /tmp/* /var/{cache,log}/* /var/lib/apt/lists/*; \
fi

# Common environment variables - Defined once
ENV LANGUAGE='zh-CN'
ENV SPEED='1.0'
ENV STT_MODEL='sherpa-onnx-paraformer-zh-2023-03-28'
ENV STT_USE_INT8_ONNX_MODEL='True'
ENV STT_BUILTIN_AUTO_CONVERT_NUMBER='False'
ENV STT_THREAD_NUM='3'
ENV TTS_MODEL='matcha-icefall-zh-baker'
ENV TTS_THREAD_NUM='3'
ENV TTS_SPEAKER_SID='0'
ENV DEBUG='False'
ENV CUSTOM_STT_MODEL='null'
ENV CUSTOM_STT_MODEL_EVAL='null'
ENV CUSTOM_TTS_MODEL='null'
ENV CUSTOM_TTS_MODEL_EVAL='null'

# Install common packages - Defined once
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        netcat-traditional \
        tar \
        curl \
        bzip2 \
        git \
        cython3 \
        python3-pip \
        python3 \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install CUDA related packages and change sherpa-onnx installation for GPU if BUILD_TYPE is cuda
RUN if [ "$BUILD_TYPE" = "cuda" ]; then \
    apt-get update && apt-get install -y --no-install-recommends libasound2 && rm -rf /var/lib/apt/lists/*; \
    pip install --no-cache-dir numpy; \
    pip install sherpa-onnx==1.10.43+cuda -f https://k2-fsa.github.io/sherpa/onnx/cuda.html; \
elif [ "$BUILD_TYPE" = "cpu" ]; then \
    pip install --break-system-packages --no-cache-dir sherpa-onnx numpy; \
fi

# Copy root filesystem conditionally
COPY rootfs /tmp/staging_rootfs_conditional
RUN if [ "$BUILD_TYPE" = "cuda" ]; then \
    echo "BUILD_TYPE is cuda, copying full rootfs"; \
    cp -a /tmp/staging_rootfs_conditional/. / ; \
else \
    echo "BUILD_TYPE is not cuda, copying rootfs/etc"; \
    mkdir -p /etc && cp -a /tmp/staging_rootfs_conditional/etc/. /etc/ ; \
fi \
&& rm -rf /tmp/staging_rootfs_conditional

# Copy s6-overlay adjustments for GPU
COPY s6-overlay /tmp/staging_s6_overlay_conditional
RUN if [ "$BUILD_TYPE" = "cuda" ]; then \
    echo "BUILD_TYPE is cuda, copying s6-overlay"; \
    TARGET_S6_PATH="/package/admin/s6-overlay-${S6_OVERLAY_VERSION}/"; \
    mkdir -p "${TARGET_S6_PATH}" && \
    cp -a /tmp/staging_s6_overlay_conditional/. "${TARGET_S6_PATH}" ; \
else \
    echo "BUILD_TYPE is not cuda, skipping s6-overlay copy"; \
fi \
&& rm -rf /tmp/staging_s6_overlay_conditional

# Create model directories
RUN mkdir -p /stt-models && mkdir -p /tts-models && mkdir -p /tts-models/espeak-ng-data

# Download and extract builtin STT model
WORKDIR /stt-models
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-paraformer-zh-2023-03-28.tar.bz2 -o sherpa-onnx-paraformer-zh-2023-03-28.tar.bz2 && \
    tar -xf sherpa-onnx-paraformer-zh-2023-03-28.tar.bz2 && \
    rm sherpa-onnx-paraformer-zh-2023-03-28.tar.bz2

RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2 -o sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2 && \
    tar -xf sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2 && \
    rm sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2

# Download and extract builtin TTS model
WORKDIR /tts-models
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/matcha-icefall-zh-baker.tar.bz2 -o matcha-icefall-zh-baker.tar.bz2 && \
    tar -xf matcha-icefall-zh-baker.tar.bz2 && \
    rm matcha-icefall-zh-baker.tar.bz2

WORKDIR /tts-models
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-int8-multi-lang-v1_1.tar.bz2 -o kokoro-int8-multi-lang-v1_1.tar.bz2 && \
    tar -xf kokoro-int8-multi-lang-v1_1.tar.bz2 && \
    rm kokoro-int8-multi-lang-v1_1.tar.bz2

WORKDIR /tts-models
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-melo-tts-zh_en.tar.bz2 -o vits-melo-tts-zh_en.tar.bz2 && \
    tar -xf vits-melo-tts-zh_en.tar.bz2 && \
    rm vits-melo-tts-zh_en.tar.bz2

RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/vocoder-models/hifigan_v1.onnx -o hifigan_v1.onnx
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/vocoder-models/hifigan_v2.onnx -o hifigan_v2.onnx
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/vocoder-models/hifigan_v2.onnx -o hifigan_v3.onnx

# Download and extract espeak-ng-data
WORKDIR /tts-models/espeak-ng-data
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/espeak-ng-data.tar.bz2 -o espeak-ng-data.tar.bz2 && \
    tar -xf espeak-ng-data.tar.bz2 && \
    rm espeak-ng-data.tar.bz2

HEALTHCHECK --start-period=3m --interval=30m \
    CMD echo '{ "type": "describe" }' \
        | nc -w 1 localhost 10400 \
        | grep -iq "Sherpa" \
        || exit 1
# Copy the add-on code.  Crucially *before* requirements.txt, so Docker layer caching works!
COPY . /app
WORKDIR /app
RUN ls -la /app

#install
RUN pip install --break-system-packages --no-cache-dir git+https://github.com/rhasspy/wyoming.git

#EXPOSE PORTS
EXPOSE 10400 10500
RUN pip install --break-system-packages --no-cache-dir uvicorn fastapi pydantic pydub python-multipart