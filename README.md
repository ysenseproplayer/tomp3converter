# tomp3 - YouTube MP3/MP4 Downloader
A free, fast, and easy-to-use YouTube to MP3/MP4 converter with a clean, modern web interface!

## Features
- 🎵 Download YouTube videos as MP3 (with multiple bitrate options)
- 🎥 Download YouTube videos as MP4 (with multiple quality options)
- 📱 Mobile-friendly design
- 🎨 Beautiful dark purple theme
- 🚀 Fast processing
- 📝 SEO-optimized pages

## Local Development
1. Clone this repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Download FFmpeg and add it to your PATH (or use the bundled version in the original project)
4. Run the app locally:
   ```bash
   python app.py
   ```

## Deploy on Render (Easiest Option)
1. Go to [Render](https://render.com) and sign up/login
2. Click **New +** → **Web Service**
3. Connect your GitHub account and select this repo
4. Configure the service:
   - **Name**: `tomp3converter` (or your preferred name)
   - **Runtime**: `Python 3`
   - **Start Command**: `gunicorn --workers 3 --bind 0.0.0.0:$PORT app:app`
5. Add FFmpeg buildpack (go to **Environment** → **Add Buildpack**, add `https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git` and move it above the Python buildpack)
6. Click **Create Web Service**!

## Deploy on a VPS (Ubuntu/Debian)
Full instructions in the original guide, but basic steps:
1. Install Python, pip, FFmpeg, Git
2. Clone repo and install dependencies
3. Use Gunicorn as production WSGI server
4. Set up Nginx as reverse proxy
5. Add SSL with Let's Encrypt

## Important Notes
⚠️ **YouTube Terms of Service**: Downloading YouTube content may violate YouTube's Terms of Service. Only download content you have the legal right to use.

⚠️ **Resource Usage**: Processing videos/audio can use significant CPU/memory. For production use, consider scaling your resources and adding rate limiting.

## Tech Stack
- Flask (web framework)
- yt-dlp (for downloading YouTube content)
- pydub (for audio conversion)
- Gunicorn (production WSGI server)

## License
MIT License
