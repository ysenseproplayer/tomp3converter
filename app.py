import os
import sys
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.downloader import YoutubeDownloader
from src.converter import AudioConverter
from src.utils import sanitize_filename, format_file_size
from src.exceptions import DownloadError, ConversionError
from config.settings import DOWNLOAD_DIR, LOGGING_CONFIG
import logging.config

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# In-memory task store
tasks = {}
task_id_counter = 0
tasks_lock = threading.Lock()

def process_download(task_id, url, format_type, quality):
    """Background task to download and convert YouTube video"""
    try:
        with tasks_lock:
            tasks[task_id]["status"] = "downloading"
            tasks[task_id]["progress"] = 0

        if format_type == 'mp4':
            # MP4 download (video + audio)
            output_template = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
            downloader = YoutubeDownloader(output_template)
            
            # Update ydl opts for video
            downloader.ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best'
            downloader.ydl_opts['merge_output_format'] = 'mp4'
            
            # Progress hook
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                        downloaded = d.get('downloaded_bytes', 0)
                        if total > 0:
                            progress = int((downloaded / total) * 100)
                            with tasks_lock:
                                tasks[task_id]["progress"] = progress
                    except:
                        pass
            
            downloader.ydl_opts['progress_hooks'] = [progress_hook]
            downloaded_file = downloader.download(url)
            
            with tasks_lock:
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["progress"] = 100
                tasks[task_id]["filename"] = os.path.basename(downloaded_file)
                tasks[task_id]["file_path"] = downloaded_file
                tasks[task_id]["file_size"] = format_file_size(os.path.getsize(downloaded_file))
        else:
            # Audio download
            output_template = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
            downloader = YoutubeDownloader(output_template)
            
            # Progress hook
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                        downloaded = d.get('downloaded_bytes', 0)
                        if total > 0:
                            progress = int((downloaded / total) * 100)
                            with tasks_lock:
                                tasks[task_id]["progress"] = progress
                    except:
                        pass
            
            downloader.ydl_opts['progress_hooks'] = [progress_hook]
            downloaded_file = downloader.download(url)
            
            with tasks_lock:
                tasks[task_id]["status"] = "converting"
                tasks[task_id]["progress"] = 50

            # Convert to selected audio format
            base_name = os.path.splitext(downloaded_file)[0]
            output_file = os.path.join(DOWNLOAD_DIR, sanitize_filename(f"{os.path.basename(base_name)}.{format_type}"))
            converter = AudioConverter()
            converter.convert_to_mp3(downloaded_file, output_file)  # Reuse, it works for any format via pydub
            
            with tasks_lock:
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["progress"] = 100
                tasks[task_id]["filename"] = os.path.basename(output_file)
                tasks[task_id]["file_path"] = output_file
                tasks[task_id]["file_size"] = format_file_size(os.path.getsize(output_file))
            
            # Cleanup original file
            if os.path.abspath(downloaded_file) != os.path.abspath(output_file):
                converter.cleanup(downloaded_file)
            
    except (DownloadError, ConversionError) as e:
        with tasks_lock:
            tasks[task_id]["status"] = "error"
            tasks[task_id]["message"] = str(e)
    except Exception as e:
        logger.exception(f"Unexpected error in download task")
        with tasks_lock:
            tasks[task_id]["status"] = "error"
            tasks[task_id]["message"] = str(e)

@app.route('/')
def index():
    return render_template('index.html', page='mp3', title='YouTube to MP3 Downloader - Free Online Tool', description='Convert YouTube videos to MP3 for free. High quality audio downloads with our fast, easy-to-use online converter.')

@app.route('/youtube-to-mp4')
def mp4():
    return render_template('mp4.html', page='mp4', title='YouTube to MP4 Downloader - Free Online Tool', description='Download YouTube videos as MP4 in HD quality. Free, fast, and easy-to-use online video downloader.')

@app.route('/api/download', methods=['POST'])
def start_download():
    global task_id_counter
    
    data = request.get_json()
    url = data.get('url')
    format_type = data.get('format', 'mp3')
    quality = data.get('quality', '192')
    
    if not url:
        return jsonify({'status': 'error', 'message': 'URL is required'}), 400
    
    with tasks_lock:
        task_id = str(task_id_counter)
        task_id_counter += 1
        tasks[task_id] = {
            'status': 'starting',
            'progress': 0,
            'url': url
        }
    
    # Start background thread
    thread = threading.Thread(target=process_download, args=(task_id, url, format_type, quality))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'task_id': task_id})

@app.route('/api/status/<task_id>')
def get_status(task_id):
    with tasks_lock:
        task = tasks.get(task_id)
    
    if not task:
        return jsonify({'status': 'error', 'message': 'Task not found'}), 404
    
    return jsonify(task)

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    # Add FFmpeg to PATH
    ffmpeg_bin = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg-master-latest-win64-gpl', 'bin')
    if os.path.exists(ffmpeg_bin):
        os.environ['PATH'] = ffmpeg_bin + os.pathsep + os.environ.get('PATH', '')
    
    app.run(debug=True, host='0.0.0.0', port=5000)
