# 🎵 Audio Compressor - Speech Optimization

A production-grade batch audio compressor optimized for speech content. Supports MP3, MP4, and MPEG files with automatic audio extraction and intelligent bitrate optimization.

## ✨ Features

- **Multi-format Support**: MP3, MP4, and MPEG files
- **Speech Optimization**: 16 kHz sample rate, mono channel, 16-24 kbps bitrate
- **Intelligent Compression**: Auto-adjusts bitrate based on audio duration (target: 1-3 MB)
- **Batch Processing**: Process multiple files concurrently with configurable workers
- **File Validation**: Automatic size and format validation (MP3: 50 MB, MP4/MPEG: 100 MB)
- **ZIP Archive**: Compressed files packaged in a single archive
- **Web Interface**: Modern, dark-themed UI for easy file management
- **Command-line Interface**: Full-featured CLI for automation

## 📋 Requirements

### System Requirements
- **FFmpeg**: Required for audio processing
  - Download: https://ffmpeg.org/download.html
  - Must be accessible in system PATH

### Python Requirements
- Python 3.7 or higher
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## 🚀 Quick Start

### Web Application (Recommended)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Flask server:**
   ```bash
   python app.py
   ```

3. **Open your browser and go to:**
   ```
   http://localhost:5000
   ```

4. **Use the web interface:**
   - Drag and drop your audio/video files
   - Click "Compress All Files"
   - Download the compressed ZIP archive

### Command-line Usage

**Basic usage:**
```bash
python compress.py audio1.mp3 audio2.mp3 audio3.mp3
```

**With custom output name:**
```bash
python compress.py *.mp3 -o my_compressed.zip
```

**With custom worker count:**
```bash
python compress.py audio.mp3 video.mp4 -w 8
```

**Mix multiple formats:**
```bash
python compress.py audio.mp3 video.mp4 video.mpeg
```

## 📖 Usage Examples

### Example 1: Single File
```bash
python compress.py podcast.mp3
```
Output: `compressed_audio.zip` containing `podcast_compressed.mp3`

### Example 2: Multiple MP3 Files
```bash
python compress.py episode1.mp3 episode2.mp3 episode3.mp3
```

### Example 3: MP4 Video (Extract Audio)
```bash
python compress.py lecture.mp4
```
The tool will extract audio from the video and compress it.

### Example 4: Mixed Formats
```bash
python compress.py audio.mp3 video.mp4 recording.mpeg -o batch_2024.zip
```

### Example 5: Wildcard Selection
```bash
python compress.py *.mp3
```

### Example 6: High Concurrency
```bash
python compress.py *.mp3 -w 16
```
Process with 16 concurrent workers (useful for large batches).

## 🎛️ Command-line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `files` | - | Input files (required) | - |
| `--output` | `-o` | Output ZIP filename | `compressed_audio.zip` |
| `--workers` | `-w` | Number of concurrent workers | `4` |

## 📊 Compression Settings

### Audio Processing
- **Sample Rate**: 16 kHz (optimal for speech)
- **Channels**: Mono (1 channel)
- **Bitrate**: 16-24 kbps (auto-adjusted based on duration)
- **Codec**: MP3 (libmp3lame)

### File Size Limits
- **MP3 files**: Maximum 50 MB
- **MP4/MPEG files**: Maximum 100 MB

### Target Output Size
- **Goal**: 1-3 MB per compressed file
- Bitrate automatically adjusted based on audio duration to achieve target size

## 🔧 How It Works

1. **Validation**: Files are validated for format and size
2. **Audio Extraction** (MP4/MPEG): Audio track extracted from video
3. **Duration Analysis**: Audio duration measured via ffprobe
4. **Bitrate Calculation**: Optimal bitrate calculated for 1-3 MB target
5. **Compression**: FFmpeg applies speech-optimized settings
6. **Archival**: All compressed files packaged into ZIP
7. **Cleanup**: Temporary files automatically removed

## 📁 Project Structure

```
compressor/
├── app.py               # Flask web server
├── compress.py          # CLI compression script
├── index.html           # Web interface
├── style.css            # Web interface styles
├── script.js            # Web interface logic
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🐛 Troubleshooting

### "FFmpeg is not installed or not in PATH"
- Install FFmpeg: https://ffmpeg.org/download.html
- Verify installation: `ffmpeg -version`
- Add FFmpeg to system PATH

### "File exceeds size limit"
- MP3 files must be ≤ 50 MB
- MP4/MPEG files must be ≤ 100 MB
- Split or pre-compress large files

### "Unsupported file type"
- Only `.mp3`, `.mp4`, `.mpeg`, `.mpg` are supported
- Convert other formats to supported types first

### Slow processing
- Increase workers: `python compress.py files -w 8`
- Note: More workers = more CPU/memory usage

## 📝 Technical Details

### FFmpeg Commands

**For MP3 files:**
```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 -b:a 20k -acodec libmp3lame output.mp3
```

**For MP4/MPEG files (extraction):**
```bash
# Step 1: Extract audio
ffmpeg -i input.mp4 -vn -acodec libmp3lame temp.mp3

# Step 2: Compress audio
ffmpeg -i temp.mp3 -ar 16000 -ac 1 -b:a 20k -acodec libmp3lame output.mp3
```

### Bitrate Calculation
```
optimal_bitrate = ((target_size_bytes * 8) / (duration_seconds * 1000)) kbps
clamped to 16-24 kbps range
```

## 🎯 Use Cases

- **Podcast Compression**: Reduce file sizes for faster uploads/downloads
- **Speech Recording**: Optimize voice notes, lectures, interviews
- **Video Audio Extraction**: Extract and compress audio from video files
- **Batch Processing**: Handle large collections of audio files
- **Storage Optimization**: Reduce storage costs for speech archives

## 🔒 Privacy & Security

- All processing happens **locally** on your machine
- No files are uploaded to external servers
- FFmpeg processing is fully offline

## 📄 License

This project is provided as-is for educational and personal use.

## 🤝 Support

For issues or questions:
1. Verify FFmpeg is installed correctly
2. Check file formats and sizes
3. Review error messages in console output
4. Try processing files individually to isolate issues

## 🚀 Future Enhancements

Potential improvements:
- GUI desktop application
- Real-time progress visualization
- Custom compression profiles
- Batch job scheduling
- Cloud processing integration
- More audio format support

---

**Made with ❤️ for speech optimization**
