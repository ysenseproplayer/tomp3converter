import os
import threading
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

tasks = {}
task_id_counter = 0
tasks_lock = threading.Lock()


def process_download(task_id, url, format_type, quality):
    try:
        with tasks_lock:
            tasks[task_id] = {'status': 'processing', 'progress': 25}

        # Map quality values for Cobalt API
        if format_type == 'mp4':
            # Video download: Cobalt uses correct keys from docs
            cobalt_payload = {
                'url': url,
                'downloadMode': 'auto',
                'videoQuality': quality,
                'youtubeVideoCodec': 'h264',
                'filenameStyle': 'basic'
            }
        else:
            # Audio download: Cobalt uses correct keys
            cobalt_payload = {
                'url': url,
                'downloadMode': 'audio',
                'audioFormat': format_type,
                'filenameStyle': 'basic'
            }

        cobalt_response = requests.post(
            'https://api.cobalt.tools/',
            json=cobalt_payload,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            timeout=30
        )

        print(f"Cobalt API status code: {cobalt_response.status_code}")
        print(f"Cobalt API response: {cobalt_response.text}")

        cobalt_response.raise_for_status()
        cobalt_data = cobalt_response.json()

        with tasks_lock:
            tasks[task_id]['status'] = 'downloading'
            tasks[task_id]['progress'] = 75

        status = cobalt_data.get('status')
        if status in ['success', 'redirect', 'tunnel']:
            download_url = cobalt_data['url']
            filename = cobalt_data.get('filename', f'download.{format_type}')
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)

            # Download the file
            with requests.get(download_url, stream=True, timeout=120) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0

                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = 75 + int((downloaded / total_size) * 25)
                                with tasks_lock:
                                    tasks[task_id]['progress'] = min(progress, 100)

            with tasks_lock:
                tasks[task_id]['status'] = 'completed'
                tasks[task_id]['progress'] = 100
                tasks[task_id]['filename'] = filename
                tasks[task_id]['file_size'] = format_file_size(os.path.getsize(file_path))
        else:
            raise Exception(cobalt_data.get('text', f'Unknown error from Cobalt API: {status}'))

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
