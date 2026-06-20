import os
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

tasks = {}
task_id_counter = 0
tasks_lock = threading.Lock()


def process_download(task_id, url, format_type, quality):
    try:
        with tasks_lock:
            tasks[task_id] = {'status': 'downloading', 'progress': 0}

        def progress_hook(d):
            if d['status'] == 'downloading':
                try:
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total > 0:
                        progress = int((downloaded / total) * 100)
                        with tasks_lock:
                            tasks[task_id]['progress'] = progress
                except Exception:
                    pass

        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [progress_hook],
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }

        if format_type == 'mp4':
            ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best'
            ydl_opts['merge_output_format'] = 'mp4'
        else:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_type,
                'preferredquality': quality,
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type != 'mp4':
                base, _ = os.path.splitext(filename)
                for ext in ['.mp3', '.m4a', '.wav', '.flac']:
                    candidate = base + ext
                    if os.path.exists(candidate):
                        filename = candidate
                        break

        with tasks_lock:
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['progress'] = 100
            tasks[task_id]['filename'] = os.path.basename(filename)
            tasks[task_id]['file_size'] = format_file_size(os.path.getsize(filename))

    except Exception as e:
        with tasks_lock:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['message'] = str(e)


def format_file_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


@app.route('/')
def index():
    return render_template('index.html', page='mp3', title='YouTube to MP3 Downloader', description='Convert YouTube videos to MP3 for free')


@app.route('/youtube-to-mp4')
def mp4():
    return render_template('mp4.html', page='mp4', title='YouTube to MP4 Downloader', description='Download YouTube videos to MP4 for free')


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

    threading.Thread(target=process_download, args=(task_id, url, format_type, quality), daemon=True).start()
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
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
