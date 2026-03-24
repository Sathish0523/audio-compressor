# 🎵 Speech-Optimized Audio Compression System

![Python](https://img.shields.io/badge/Python-3.7+-blue)
![Flask](https://img.shields.io/badge/Flask-API-green)
![FFmpeg](https://img.shields.io/badge/FFmpeg-AudioProcessing-orange)
![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen)

🚀 A production-grade full-stack application for compressing audio and video files into efficient, speech-optimized formats using Flask and FFmpeg.


## 🔥 Key Highlights

* ⚡ Batch audio compression with multi-threading
* 🎯 Intelligent bitrate optimization (1–3 MB target size)
* 🌐 Full-stack web interface with drag-and-drop upload
* 🔄 Supports MP3, MP4, MPEG (automatic audio extraction)
* 📦 ZIP archive download for compressed files
* 🧠 Optimized for speech (16 kHz, mono, 16–24 kbps)


## 🛠️ Tech Stack

* **Backend:** Flask (Python)
* **Frontend:** HTML, CSS, JavaScript
* **Processing Engine:** FFmpeg
* **Concurrency:** ThreadPoolExecutor
* **API:** REST API for file processing


## 🚀 Quick Start

### 1️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 2️⃣ Start the server

```bash
python app.py
```

### 3️⃣ Open browser

```
http://localhost:5000
```


## ⚙️ Features

* Multi-format Support: MP3, MP4, MPEG
* Speech Optimization: 16 kHz, mono, low bitrate
* Intelligent Compression: Auto bitrate based on duration
* Batch Processing with concurrent execution
* File Validation (size + format)
* ZIP packaging for output
* CLI + Web interface support
* 

## 💻 Command-Line Usage

```bash
python compress.py audio1.mp3 audio2.mp3
```

```bash
python compress.py *.mp3 -o output.zip
```

```bash
python compress.py audio.mp3 video.mp4 -w 8
```


## 📊 Compression Settings

* Sample Rate: 16 kHz
* Channels: Mono
* Bitrate: 16–24 kbps
* Target Size: 1–3 MB


## 🔧 How It Works

1. Validate input files
2. Extract audio (if video input)
3. Analyze duration using ffprobe
4. Calculate optimal bitrate
5. Compress using FFmpeg
6. Package into ZIP
7. Return downloadable output


## 📁 Project Structure

```
audio-compressor/
├── app.py
├── compress.py
├── index.html
├── script.js
├── style.css
├── requirements.txt
├── README.md
```


## 🎯 Use Cases

* Podcast compression
* Lecture recordings
* Voice notes optimization
* Storage reduction
* Audio extraction from videos


## 🔒 Privacy & Security

* ✅ 100% local processing
* ✅ No cloud upload
* ✅ Secure file handling


## 🚀 Future Enhancements

* Cloud deployment (AWS / Render)
* Real-time progress tracking
* User authentication
* More format support


## 👨‍💻 Author

Sathish Kumar
Electronics and Communication Engineer | Aspiring Software Developer

---

## ⭐ If you like this project

Give it a ⭐ on GitHub — it helps a lot!
