#!/usr/bin/env python3
"""
Batch Audio Compressor for Speech
Supports MP3, MP4, and MPEG files with speech-optimized compression.
"""

import os
import sys
import argparse
import subprocess
import zipfile
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# File size limits in bytes
MP3_MAX_SIZE = 50 * 1024 * 1024  # 50 MB
MP4_MPEG_MAX_SIZE = 100 * 1024 * 1024  # 100 MB

# Supported extensions
SUPPORTED_EXTENSIONS = {'.mp3', '.mp4', '.mpeg', '.mpg'}

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible."""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

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
    except Exception as e:
        print(f"Warning: Could not determine duration for {file_path}: {e}")
        return None

def calculate_optimal_bitrate(duration):
    """
    Calculate optimal bitrate based on audio duration.
    Target: 1-3 MB output file size
    """
    if duration is None:
        return 20  # Default bitrate
    
    # Target size range in bytes
    target_min = 1 * 1024 * 1024  # 1 MB
    target_max = 3 * 1024 * 1024  # 3 MB
    
    # Calculate bitrate in kbps
    # bitrate (kbps) = (target_size_bytes * 8) / (duration_seconds * 1000)
    bitrate_min = (target_min * 8) / (duration * 1000)
    bitrate_max = (target_max * 8) / (duration * 1000)
    
    # Use middle of the range
    optimal_bitrate = (bitrate_min + bitrate_max) / 2
    
    # Clamp to 16-24 kbps range for speech optimization
    return max(16, min(24, optimal_bitrate))

def validate_file(file_path):
    """Validate file type and size."""
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        return False, f"File not found: {file_path}"
    
    # Check extension
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: {path.suffix}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
    
    # Check file size
    file_size = path.stat().st_size
    if path.suffix.lower() == '.mp3':
        if file_size > MP3_MAX_SIZE:
            return False, f"MP3 file exceeds 50 MB limit: {path.name}"
    else:  # MP4 or MPEG
        if file_size > MP4_MPEG_MAX_SIZE:
            return False, f"File exceeds 100 MB limit: {path.name}"
    
    return True, None

def compress_audio(input_file, output_dir, temp_dir):
    """
    Compress a single audio file with speech-optimized settings.
    Returns: (success, input_file, output_file, error_message)
    """
    input_path = Path(input_file)
    
    # Validate file
    is_valid, error_msg = validate_file(input_path)
    if not is_valid:
        return False, input_file, None, error_msg
    
    # Determine if we need to extract audio first (MP4/MPEG)
    needs_extraction = input_path.suffix.lower() in {'.mp4', '.mpeg', '.mpg'}
    
    try:
        # Get duration for bitrate optimization
        duration = get_audio_duration(input_path)
        bitrate = calculate_optimal_bitrate(duration)
        
        if needs_extraction:
            # Two-step process: extract audio, then compress
            temp_mp3 = Path(temp_dir) / f"{input_path.stem}_temp.mp3"
            
            # Step 1: Extract audio from video
            extract_cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-y',  # Overwrite output file
                str(temp_mp3)
            ]
            
            subprocess.run(extract_cmd, 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE, 
                         check=True)
            
            # Step 2: Compress the extracted audio
            source_file = temp_mp3
        else:
            source_file = input_path
        
        # Create output filename
        output_file = Path(output_dir) / f"{input_path.stem}_compressed.mp3"
        
        # Compression command with speech-optimized settings
        compress_cmd = [
            'ffmpeg',
            '-i', str(source_file),
            '-ar', '16000',  # 16 kHz sample rate
            '-ac', '1',  # Mono
            '-b:a', f'{int(bitrate)}k',  # Calculated bitrate
            '-acodec', 'libmp3lame',
            '-y',  # Overwrite output file
            str(output_file)
        ]
        
        subprocess.run(compress_cmd, 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        
        return True, input_file, output_file, None
        
    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}"
        return False, input_file, None, error_msg
    except Exception as e:
        return False, input_file, None, str(e)

def create_zip_archive(files, output_zip):
    """Create a ZIP archive from the list of files."""
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            zipf.write(file_path, Path(file_path).name)

def process_files(input_files, output_zip='compressed_audio.zip', max_workers=4):
    """
    Process multiple audio files concurrently.
    Returns: (success_count, failure_count, results)
    """
    if not check_ffmpeg():
        print("Error: FFmpeg is not installed or not in PATH.")
        print("Please install FFmpeg: https://ffmpeg.org/download.html")
        return 0, 0, []
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / 'compressed'
        output_dir.mkdir(exist_ok=True)
        
        results = []
        compressed_files = []
        
        print(f"\nProcessing {len(input_files)} file(s)...\n")
        
        # Process files concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(compress_audio, f, output_dir, temp_dir): f 
                for f in input_files
            }
            
            for future in as_completed(future_to_file):
                success, input_file, output_file, error = future.result()
                results.append({
                    'input': input_file,
                    'output': output_file,
                    'success': success,
                    'error': error
                })
                
                if success:
                    compressed_files.append(output_file)
                    input_size = Path(input_file).stat().st_size / (1024 * 1024)
                    output_size = Path(output_file).stat().st_size / (1024 * 1024)
                    reduction = ((input_size - output_size) / input_size) * 100
                    print(f"✓ {Path(input_file).name}: {input_size:.2f} MB → {output_size:.2f} MB ({reduction:.1f}% reduction)")
                else:
                    print(f"✗ {Path(input_file).name}: {error}")
        
        # Create ZIP archive if there are compressed files
        if compressed_files:
            print(f"\nCreating ZIP archive: {output_zip}")
            create_zip_archive(compressed_files, output_zip)
            zip_size = Path(output_zip).stat().st_size / (1024 * 1024)
            print(f"Archive created: {zip_size:.2f} MB")
        
        success_count = sum(1 for r in results if r['success'])
        failure_count = len(results) - success_count
        
        return success_count, failure_count, results

def main():
    parser = argparse.ArgumentParser(
        description='Batch Audio Compressor for Speech (MP3, MP4, MPEG)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s audio1.mp3 audio2.mp3 audio3.mp3
  %(prog)s *.mp3 *.mp4 -o my_compressed.zip
  %(prog)s audio.mp3 -w 8  # Use 8 workers
        """
    )
    
    parser.add_argument('files', nargs='+', help='Input audio/video files (MP3, MP4, MPEG)')
    parser.add_argument('-o', '--output', default='compressed_audio.zip', 
                       help='Output ZIP file name (default: compressed_audio.zip)')
    parser.add_argument('-w', '--workers', type=int, default=4,
                       help='Number of concurrent workers (default: 4)')
    
    args = parser.parse_args()
    
    # Expand file paths (handles wildcards on Windows)
    input_files = []
    for pattern in args.files:
        matches = list(Path('.').glob(pattern)) if '*' in pattern else [Path(pattern)]
        input_files.extend([str(f) for f in matches if f.is_file()])
    
    if not input_files:
        print("Error: No valid input files found.")
        sys.exit(1)
    
    print(f"Batch Audio Compressor for Speech")
    print(f"=" * 50)
    print(f"Input files: {len(input_files)}")
    print(f"Workers: {args.workers}")
    print(f"Output: {args.output}")
    
    success_count, failure_count, results = process_files(
        input_files, 
        args.output, 
        args.workers
    )
    
    print(f"\n{'=' * 50}")
    print(f"Processing complete!")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    
    if failure_count > 0:
        print(f"\nFailed files:")
        for result in results:
            if not result['success']:
                print(f"  - {Path(result['input']).name}: {result['error']}")
    
    sys.exit(0 if failure_count == 0 else 1)

if __name__ == '__main__':
    main()
