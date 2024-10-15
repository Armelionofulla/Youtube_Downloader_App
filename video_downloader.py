import glob
import os
import time

import yt_dlp


class VideoDownloader:
    def __init__(self, ffmpeg_path):
        self.ffmpeg_path = ffmpeg_path
        self.stop_download = False
        self.ydl = None
        self.current_output_template = None
        self.start_time = None  # To track when the download started

    def download_video(self, url, output_path, progress_var, completion_label, enable_buttons):
        self.stop_download = False  # Reset the stop flag
        self.start_time = time.time()  # Record the start time

        def progress_hook(d):
            if self.stop_download:
                raise yt_dlp.utils.DownloadError("Download stopped by user")

            if d['status'] == 'downloading':
                # Dynamically calculate progress percentage based on downloaded bytes
                if d.get('total_bytes') is not None:
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    total_bytes = d['total_bytes']
                    percentage = min(int((downloaded_bytes / total_bytes) * 100), 100)
                else:
                    elapsed_time = time.time() - self.start_time  # Calculate elapsed time
                    percentage = min(int((elapsed_time / 100) * 100), 100)  # Fallback to time-based percentage

                # Speed up the percentage fill
                progress_var.set(percentage + 5)  # Increase progress by 5% to fill faster, but cap at 100
                if percentage < 100:
                    completion_label.configure(text=f"Downloading... {percentage}%")
                else:
                    completion_label.configure(text="Downloading... 100%")

            elif d['status'] == 'finished':
                # Set progress to 100% when the download finishes
                progress_var.set(100)
                completion_label.configure(text="Download complete!")

        # Construct the output template path for potential cleanup
        self.current_output_template = os.path.join(output_path, '%(title)s.%(ext)s')

        options = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
            'ffmpeg_location': self.ffmpeg_path,
            'outtmpl': self.current_output_template,
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }],
        }

        try:
            self.ydl = yt_dlp.YoutubeDL(options)
            self.ydl.download([url])
            progress_var.set(100)
            completion_label.configure(text="Download complete!")
        except yt_dlp.utils.DownloadError:
            completion_label.configure(text="Download stopped.")
            self.cleanup_partial_files(output_path)
        except Exception as e:
            completion_label.configure(text="Download failed.")
            print(f"Error: {e}")
            self.cleanup_partial_files(output_path)
        finally:
            enable_buttons()  # Enable buttons after download completes or if there’s an error
            self.cleanup()  # Ensure cleanup of resources

    def cleanup_partial_files(self, output_path):
        """Delete all files with the same base name in the output directory."""
        if self.current_output_template:
            # Extract the base name without extension
            base_name = os.path.splitext(os.path.basename(self.current_output_template))[0]
            # Create a pattern to match files with the same base name
            pattern = os.path.join(output_path, f"{base_name}.*")  # Match all extensions
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                except OSError as e:
                    print(f"Error deleting file {file_path}: {e}")

    def stop(self):
        self.stop_download = True  # Set the stop flag to True
        if self.ydl:
            self.ydl.abort()  # Attempt to abort the download gracefully
        # Only attempt cleanup if current_output_template is valid
        if self.current_output_template:
            self.cleanup_partial_files(os.path.dirname(self.current_output_template))

    def cleanup(self):
        """Release resources to allow file deletion."""
        self.ydl = None
        self.current_output_template = None
