# 小说文本转语音项目

这是一个将小说文本转换为语音的 Web 应用程序。使用 Edge TTS 进行文本到语音的转换，支持实时进度显示和音频播放功能。

## 功能特点

- 支持中文文本转语音
- 实时显示朗读进度
- 自动分段处理长文本
- 支持不同角色的语音区分
- Web 界面操作简单直观

## 安装要求

- Python 3.7+
- pip（Python 包管理器）

## 依赖安装

```bash
# 创建并激活虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装依赖包
pip install quart hypercorn edge-tts soundfile numpy
```

## 运行方法

1. 确保已安装所有依赖
2. 运行应用程序：
```bash
python run.py
```
3. 打开浏览器访问：`http://localhost:5000`

## 使用说明

1. 在网页文本框中输入要转换的小说文本
2. 点击"转换"按钮
3. 等待转换完成
4. 使用网页播放器控制音频播放

## 项目结构

- `run.py`: 应用程序入口
- `app.py`: 主应用逻辑
- `novel_to_speech.py`: 文本解析和语音转换核心功能
- `templates/`: HTML 模板文件
- `static/`: 静态资源文件
  - `audio/`: 生成的音频文件存储目录
