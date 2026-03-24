#!/usr/bin/env python3
"""
Flask Web Application for Audio Compression
Provides a REST API for the web interface to compress audio files.
"""

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import tempfile
import shutil
from pathlib import Path
import subprocess
import json

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Configuration
UPLOAD_FOLDER = tempfile.gettempdir()
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB (increased to handle larger uploads)
ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'mpeg', 'mpg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# File size limits (100 MB per file)
MP3_MAX_SIZE = 100 * 1024 * 1024  # 100 MB
MP4_MPEG_MAX_SIZE = 100 * 1024 * 1024  # 100 MB

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_audio_duration(file_path):
    """Get audio duration in seconds using ffprobe."""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            str(file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except Exception:
        return None

def calculate_optimal_bitrate(duration):
    """Calculate optimal bitrate based on audio duration to target ~100 KB output."""
    if duration is None:
        return 12
    
    # Target output file size: ~100 KB
    target_size = 100 * 1024  # 100 KB in bytes
    
    # Calculate bitrate needed to achieve target size
    # Formula: bitrate (kbps) = (file_size_bytes * 8) / (duration_seconds * 1000)
    optimal_bitrate = (target_size * 8) / (duration * 1000)
    
    # Ensure bitrate stays within reasonable bounds (8-24 kbps for speech)
    return max(8, min(24, optimal_bitrate))

def compress_single_file(input_path, output_path, settings=None):
    """Compress a single audio file with custom settings."""
    try:
        # Use custom settings or defaults
        if settings is None:
            settings = {
                'sampleRate': 16000,
                'channels': 1,
                'bitrate': None
            }
        
        # Get duration
        duration = get_audio_duration(input_path)
        
        # Use custom bitrate if provided, otherwise calculate
        if settings.get('bitrate'):
            bitrate = settings['bitrate']
        else:
            bitrate = calculate_optimal_bitrate(duration)
        
        # Check if it's a video file
        ext = Path(input_path).suffix.lower()
        needs_extraction = ext in {'.mp4', '.mpeg', '.mpg'}
        
        if needs_extraction:
            # Extract audio first
            temp_mp3 = str(Path(input_path).parent / f"{Path(input_path).stem}_temp.mp3")
            extract_cmd = [
                'ffmpeg', '-i', str(input_path),
                '-vn', '-acodec', 'libmp3lame',
                '-y', temp_mp3
            ]
            subprocess.run(extract_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            source_file = temp_mp3
        else:
            source_file = input_path
        
        # Compress with custom settings
        compress_cmd = [
            'ffmpeg', '-i', source_file,
            '-ar', str(settings.get('sampleRate', 16000)),
            '-ac', str(settings.get('channels', 1)),
            '-b:a', f'{int(bitrate)}k',
            '-acodec', 'libmp3lame',
            '-y', str(output_path)
        ]
        subprocess.run(compress_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        # Clean up temp file if created
        if needs_extraction and os.path.exists(temp_mp3):
            os.remove(temp_mp3)
        
        return True, None
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    """Serve the main page."""
    return send_file('index.html')

@app.route('/api/compress', methods=['POST'])
def compress_files():
    """Compress uploaded files and return ZIP archive."""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    # Get custom settings from form data
    settings = {
        'sampleRate': int(request.form.get('sampleRate', 16000)),
        'channels': int(request.form.get('channels', 1)),
        'bitrate': int(request.form.get('bitrate', 0)) or None,
        'targetSize': float(request.form.get('targetSize', 2)),
        'sizeUnit': request.form.get('sizeUnit', 'MB')
    }
    
    files = request.files.getlist('files')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    # Create temporary directory for processing
    temp_dir = tempfile.mkdtemp()
    output_dir = Path(temp_dir) / 'compressed'
    output_dir.mkdir(exist_ok=True)
    
    results = []
    compressed_files = []
    
    try:
        for file in files:
            if file and allowed_file(file.filename):
                # Validate file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                ext = Path(file.filename).suffix.lower()
                max_size = MP3_MAX_SIZE if ext == '.mp3' else MP4_MPEG_MAX_SIZE
                
                if file_size > max_size:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': f'File exceeds size limit ({max_size // (1024*1024)} MB)'
                    })
                    continue
                
                # Save uploaded file
                filename = secure_filename(file.filename)
                input_path = Path(temp_dir) / filename
                file.save(str(input_path))
                
                # Compress file
                output_filename = f"{Path(filename).stem}_compressed.mp3"
                output_path = output_dir / output_filename
                
                success, error = compress_single_file(str(input_path), str(output_path), settings)
                
                if success:
                    original_size = input_path.stat().st_size
                    compressed_size = output_path.stat().st_size
                    reduction = ((original_size - compressed_size) / original_size) * 100
                    
                    compressed_files.append(str(output_path))
                    results.append({
                        'filename': file.filename,
                        'success': True,
                        'originalSize': original_size,
                        'compressedSize': compressed_size,
                        'reduction': round(reduction, 1)
                    })
                else:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': error
                    })
        
        if not compressed_files:
            return jsonify({
                'error': 'No files were successfully compressed',
                'results': results
            }), 400
        
        # Create ZIP archive
        import zipfile
        zip_path = Path(temp_dir) / 'compressed_audio.zip'
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in compressed_files:
                zipf.write(file_path, Path(file_path).name)
        
        # Return the ZIP file
        return send_file(
            str(zip_path),
            mimetype='application/zip',
            as_attachment=True,
            download_name='compressed_audio.zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Cleanup will happen when temp_dir is deleted by OS
        pass

@app.route('/api/validate', methods=['POST'])
def validate_file():
    """Validate a file without compressing."""
    data = request.json
    filename = data.get('filename')
    size = data.get('size')
    
    if not filename or size is None:
        return jsonify({'valid': False, 'error': 'Invalid request'}), 400
    
    ext = Path(filename).suffix.lower()
    
    if ext not in {'.mp3', '.mp4', '.mpeg', '.mpg'}:
        return jsonify({
            'valid': False,
            'error': f'Unsupported file type: {ext}'
        })
    
    max_size = MP3_MAX_SIZE if ext == '.mp3' else MP4_MPEG_MAX_SIZE
    
    if size > max_size:
        return jsonify({
            'valid': False,
            'error': f'File exceeds {max_size // (1024*1024)} MB limit'
        })
    
    return jsonify({'valid': True})

if __name__ == '__main__':
    print("=" * 60)
    print("Audio Compressor Web Application")
    print("=" * 60)
    print("\nServer starting...")
    print("Open your browser and go to: http://localhost:5000")
    print("\nPress CTRL+C to stop the server")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
