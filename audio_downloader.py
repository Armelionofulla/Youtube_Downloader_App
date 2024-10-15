import os
import time

import yt_dlp


class AudioDownloader:
    def __init__(self, ffmpeg_path):
        self.ffmpeg_path = ffmpeg_path
        self.stop_download = False
        self.ydl = None  # Store the YoutubeDL instance for later cleanup
        self.start_time = None  # Track the start time of the download
        self.expected_duration = 120  # Set an expected duration for the download (in seconds)

    def download_single_audio(self, url, output_path, progress_var, completion_label, enable_buttons):
        self.stop_download = False  # Reset the stop flag
        self.start_time = time.time()  # Record the start time

        def progress_hook(d):
            if self.stop_download:
                raise yt_dlp.utils.DownloadError("Download stopped by user")  # Use yt-dlp's own exception for stopping

            if d['status'] == 'downloading':
                elapsed_time = time.time() - self.start_time  # Calculate elapsed time
                if d.get('total_bytes') is not None:
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    total_bytes = d['total_bytes']
                    percentage = min(int((downloaded_bytes / total_bytes) * 100),
                                     100)  # Calculate progress percentage based on downloaded bytes
                else:
                    percentage = min(int((elapsed_time / self.expected_duration) * 100),
                                     100)  # Fallback to time-based percentage

                progress_var.set(percentage)
                completion_label.configure(text="Downloading... {:.2f}%".format(percentage))

        options = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
            'ffmpeg_location': self.ffmpeg_path,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
        }

        try:
            self.ydl = yt_dlp.YoutubeDL(options)
            self.ydl.download([url])
            progress_var.set(100)
            completion_label.configure(text="Download complete!")
        except yt_dlp.utils.DownloadError:
            completion_label.configure(text="Download stopped.")
        except Exception as e:
            completion_label.configure(text="Download failed.")
            print(f"Error: {e}")
        finally:
            enable_buttons()  # Enable buttons after download completes or if there’s an error
            self.cleanup()  # Ensure cleanup of resources

    def stop(self):
        self.stop_download = True  # Set the stop flag to True
        if self.ydl:
            self.ydl.abort()  # Attempt to abort the download gracefully
        self.cleanup()  # Perform resource cleanup

    def cleanup(self):
        """Release resources to allow file deletion."""
        self.ydl = None
