import os
import time

import yt_dlp


class MultipleFileDownloader:
    def __init__(self, ffmpeg_path):
        self.ffmpeg_path = ffmpeg_path
        self.stop_download = False
        self.ydl = None  # Store the YoutubeDL instance for later cleanup
        self.start_time = None  # Track the start time of the download
        self.expected_duration = 120  # Set an expected duration for the download (in seconds)

    def download_audio_from_csv(self, csv_file, output_path, progress_var, completion_label, enable_buttons):
        self.stop_download = False  # Reset the stop flag

        # Load URLs from the CSV file
        with open(csv_file, 'r') as f:
            urls = f.read().splitlines()

        self._download_audio_files(urls, output_path, progress_var, completion_label, enable_buttons)

    def download_selected_audio(self, selected_urls, output_path, progress_var, completion_label, enable_buttons):
        """Download selected audio files based on a list of selected URLs."""
        self.stop_download = False  # Reset the stop flag

        if selected_urls:
            self._download_audio_files(selected_urls, output_path, progress_var, completion_label, enable_buttons)
        else:
            completion_label.configure(text="No songs selected for download.")

    def _download_audio_files(self, urls, output_path, progress_var, completion_label, enable_buttons):
        """Internal method to handle downloading a list of URLs."""
        total_urls = len(urls)
        completion_label.configure(text="Downloading...")

        for index, url in enumerate(urls):
            if self.stop_download:
                completion_label.configure(text="Download stopped.")
                break

            self.start_time = time.time()  # Record the start time for the current file

            def progress_hook(d):
                if self.stop_download:
                    raise yt_dlp.utils.DownloadError(
                        "Download stopped by user")  # Use yt-dlp's own exception for stopping

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
                    completion_label.configure(
                        text=f"Downloading file {index + 1} / {total_urls} --- {percentage:.2f}% ---"
                    )

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
                progress_var.set(100)  # Set to 100% when the file finishes
                time.sleep(0.5)  # Optional: Brief pause for the user to see the 100% status
                progress_var.set(0)  # Reset progress to 0% for the next file
            except yt_dlp.utils.DownloadError:
                completion_label.configure(text=f"Download stopped for file {index + 1}.")
                break
            except Exception as e:
                print(f"Error downloading {url}: {e}")
                completion_label.configure(text=f"Download failed for file {index + 1}.")

        if not self.stop_download:
            completion_label.configure(text="All downloads complete!")

        enable_buttons()  # Re-enable buttons after all downloads complete or if stopped
        self.cleanup()  # Ensure cleanup of resources

    def stop(self):
        self.stop_download = True  # Set the stop flag to True
        if self.ydl:
            self.ydl.abort()  # Attempt to abort the download gracefully
        self.cleanup()  # Perform resource cleanup

    def cleanup(self):
        """Release resources to allow file deletion."""
        self.ydl = None
