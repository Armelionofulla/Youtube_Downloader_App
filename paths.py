import os

# Get the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define paths to the executables
DRIVER_PATH = os.path.join(BASE_DIR, 'drivers/chrome-driver', 'chromedriver.exe')
FFMPEG_PATH = os.path.join(BASE_DIR, 'drivers/ffmpeg-driver', 'ffmpeg.exe')
