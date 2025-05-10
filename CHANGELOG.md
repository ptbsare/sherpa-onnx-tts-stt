# v0.3.4
## Fix

- fix(DOCKER): Fix DOCKERFILE build failed and container not starting after upgrade.
- fix(DOCKER): 修复容器构建错误；修复升级v0.3.3之后容器以及addon均不能启动的问题

# v0.3.3
## Feature

- feat: 新增选项设置STT_BUILTIN_AUTO_CONVERT_NUMBER=True以启用内置STT模型汉字数字一二三到阿拉伯数字123的转换更好适应内置Hass Intent Fix #1
- feat: Unified CPU & GPU Dockerfile
- feat: 统一CPU/GPU DOCKERFILE构建

## Fix

- fix(api): set tts wav to 44100 for wechat bot (astrbot) compatiblity
- fix(api): 将生成的TTS语音wav比特率固定在44100以兼容微信聊天机器人astrbot的语音输出

## Documentation

- docs(CHANGELOG): update release notes


