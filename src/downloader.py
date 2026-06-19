import yt_dlp
import os
import logging
from .exceptions import DownloadError

logger = logging.getLogger(__name__)

class YoutubeDownloader:
    def __init__(self, output_path):
        self.output_path = output_path
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': self.output_path,
            'quiet': True,
            'no_warnings': True,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'retries': 10,
            'fragment_retries': 10,
            'continue': True,
            'no_check_certificate': True,
        }

    def download(self, url):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # Check if the file was converted to MP3 (if we had a postprocessor) - but we removed it, so just return filename
                # Alternatively, check if the file exists, if not try .mp3
                if not os.path.exists(filename):
                    base, _ = os.path.splitext(filename)
                    for ext in ['.mp3', '.m4a', '.webm', '.wav']:
                        candidate = base + ext
                        if os.path.exists(candidate):
                            filename = candidate
                            break
            logger.info(f"Successfully downloaded: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to download {url}: {str(e)}")
            raise DownloadError(f"Failed to download {url}: {str(e)}")
