import csv
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from audio_downloader import AudioDownloader
from paths import DRIVER_PATH, FFMPEG_PATH
from playlist_downloader import MultipleFileDownloader
from video_downloader import VideoDownloader
from youtube_link_fetcher import open_youtube_and_fetch_links

# Set up CustomTkinter theme to dark
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  # Base theme, you can customize it further

# Instantiate downloader classes
audio_downloader = AudioDownloader(FFMPEG_PATH)
video_downloader = VideoDownloader(FFMPEG_PATH)
multiple_file_downloader = MultipleFileDownloader(FFMPEG_PATH)


def fetch_and_download_mp3(url, folder_path):
    if url and folder_path.get():
        csv_file = open_youtube_and_fetch_links(url, DRIVER_PATH)
        if csv_file:
            # Open a new window for song selection
            open_song_selection_window(csv_file, folder_path)
        else:
            messagebox.showerror("Error", "Error fetching YouTube links.")
    else:
        messagebox.showerror("Error", "Please enter a valid URL and select a folder.")


def open_song_selection_window(csv_file, folder_path):
    # Create a new window
    song_window = ctk.CTkToplevel(root)
    song_window.title("Select Songs to Download")
    song_window.geometry("500x500")

    # Add a canvas and scrollbar for scrollable content
    canvas = tk.Canvas(song_window)
    scrollbar = tk.Scrollbar(song_window, orient="vertical", command=canvas.yview)
    scrollable_frame = ctk.CTkFrame(canvas)

    # Configure the canvas
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Layout the canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Read the CSV file and create a checkbox for each song
    checkboxes = []
    song_titles = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            song_title, song_url = row[0], row[1]
            song_titles.append(song_title)
            var = tk.BooleanVar()
            checkbox = ctk.CTkCheckBox(scrollable_frame, text=song_title, variable=var)
            checkbox.pack(pady=5, anchor="w")
            checkboxes.append((var, song_url))  # Store both checkbox variable and URL

    # Select All button
    def select_all():
        for var, _ in checkboxes:
            var.set(True)

    select_all_button = ctk.CTkButton(scrollable_frame, text="Select All", command=select_all)
    select_all_button.pack(pady=0)

    # Download button
    def download_selected_songs():
        selected_songs = [url for var, url in checkboxes if var.get()]
        if selected_songs:
            # Disable buttons
            disable_buttons()

            # Start download in a new thread for better responsiveness
            threading.Thread(
                target=multiple_file_downloader.download_selected_audio,
                args=(selected_songs, folder_path.get(), progress_var, completion_label, enable_buttons)
            ).start()

            # Delete CSV file after download
            os.remove(csv_file)
            song_window.destroy()  # Close the selection window
        else:
            messagebox.showwarning("No Selection", "Please select at least one song.")

    download_button = ctk.CTkButton(scrollable_frame, text="Download", command=download_selected_songs)
    download_button.pack(pady=5)

    # Enable touchpad and mouse scrolling
    song_window.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))


def download_single_mp3(url, folder):
    if url and folder.get():
        # Disable buttons
        disable_buttons()

        # Reset progress and completion message
        progress_var.set(0)
        completion_label.configure(text="")

        # Start download in a new thread for better responsiveness
        threading.Thread(
            target=audio_downloader.download_single_audio,
            args=(url, folder.get(), progress_var, completion_label, enable_buttons)
        ).start()
    else:
        messagebox.showerror("Error", "Please enter a valid URL and select a folder.")


def download_mp4(url, folder):
    if url and folder.get():
        # Disable buttons
        disable_buttons()

        # Reset progress and completion message
        progress_var.set(0)
        completion_label.configure(text="")

        # Start download in a new thread for better responsiveness
        threading.Thread(
            target=video_downloader.download_video,
            args=(url, folder.get(), progress_var, completion_label, enable_buttons)
        ).start()
    else:
        messagebox.showerror("Error", "Please enter a valid URL and select a folder.")


def stop_downloading():
    audio_downloader.stop()  # Stop any ongoing audio download
    multiple_file_downloader.stop()  # Stop any ongoing playlist download
    video_downloader.stop()  # Stop any ongoing video download
    messagebox.showinfo("Stopped", "Download process stopped.")
    progress_var.set(0)


def clear_all_fields():
    url_entry.delete(0, tk.END)
    folder_path.set("")
    progress_var.set(0)
    completion_label.configure(text="")
    folder_path_display.configure(text="")


def show_context_menu(event):
    context_menu.tk_popup(event.x_root, event.y_root)


def paste_url():
    url_entry.insert(tk.END, root.clipboard_get())


def choose_folder():
    selected_folder = filedialog.askdirectory()
    if selected_folder:
        folder_path.set(selected_folder)
        folder_path_display.configure(text=selected_folder)
        folder_button.grid_remove()


def disable_buttons():
    download_mp3_button.configure(state=tk.DISABLED)
    download_mp4_button.configure(state=tk.DISABLED)
    fetch_mp3_button.configure(state=tk.DISABLED)


def enable_buttons():
    download_mp3_button.configure(state=tk.NORMAL)
    download_mp4_button.configure(state=tk.NORMAL)
    fetch_mp3_button.configure(state=tk.NORMAL)


# Setup UI components
root = ctk.CTk()
root.geometry("380x450")
root.title("YouTube Downloader")

# Create a context menu
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Paste URL", command=paste_url)

# URL entry setup
url_label = ctk.CTkLabel(root, text="Enter YouTube URL:")
url_label.pack(pady=5)

url_entry = ctk.CTkEntry(root, width=350)
url_entry.pack(pady=5)
# Bind the right-click event to show the context menu
url_entry.bind("<Button-3>", show_context_menu)

# Folder selection setup
folder_path = tk.StringVar()
folder_button = ctk.CTkButton(root, text="Choose Folder", command=choose_folder)
folder_button.pack(pady=5)

folder_path_display = ctk.CTkLabel(root, text="")
folder_path_display.pack(pady=5)

# Progress bar setup
progress_var = tk.DoubleVar()
progress_bar = ctk.CTkProgressBar(root, variable=progress_var, height=30)  # Increased height
progress_bar.pack(pady=5)

completion_label = ctk.CTkLabel(root, text="")
completion_label.pack(pady=5)

# Buttons setup
download_mp3_button = ctk.CTkButton(root, text="Download MP3",
                                    command=lambda: download_single_mp3(url_entry.get(), folder_path))
download_mp3_button.pack(pady=7)

download_mp4_button = ctk.CTkButton(root, text="Download Video",
                                    command=lambda: download_mp4(url_entry.get(), folder_path))
download_mp4_button.pack(pady=7)

fetch_mp3_button = ctk.CTkButton(root, text="Download Playlist",
                                 command=lambda: fetch_and_download_mp3(url_entry.get(), folder_path))
fetch_mp3_button.pack(pady=7)

stop_button = ctk.CTkButton(root, text="Stop Downloading", command=stop_downloading)
stop_button.pack(pady=7)

clear_button = ctk.CTkButton(root, text="Clear", command=clear_all_fields)
clear_button.pack(pady=7)

# Start the Tkinter main loop
root.mainloop()
