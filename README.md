# Audio Processing Tool

Audio Processing Tool 是一个功能全面的音频处理工具，支持音频上传、语音识别、音频切割、语音克隆、音频合并及字幕生成等功能，旨在为用户提供一站式音频处理解决方案。

---

## 环境配置

### 1. 创建 `.env` 文件
在项目根目录创建 `.env` 文件，填入以下内容：
```
OSS_ACCESS_KEY_ID=YOUR_OSS_ACCESS_KEY_ID
OSS_ACCESS_KEY_SECRET=YOUR_OSS_ACCESS_KEY_SECRET
DASHSCOPE_API_KEY=YOUR_DASHSCOPE_API_KEY
```

请替换为实际的 API 密钥。

---

## 部署说明

### 1. 安装依赖
运行以下命令安装所需依赖：
```
pip install -r requirements.txt
```

### 2. 运行项目
执行以下命令启动 Flask 应用：
```
python app.py
```

### 3. 访问平台
在浏览器中访问：
```
http://127.0.0.1:5000/
```

---

## 功能概述
- **音频上传**：支持多格式音频上传并统一转换。
- **语音识别**：调用 DashScope API 进行高效语音转录。
- **语音克隆**：生成个性化变声音频。
- **字幕生成**：基于音频内容自动生成 SRT 格式字幕。
- **音频合并**：支持多片段音频合并，生成完整输出。

---

## 注意事项
- 确保 `.env` 文件中配置了正确的 API 密钥。
- `.env` 文件已加入 `.gitignore`，敏感信息不会上传到Git。
