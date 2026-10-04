# Cubes Epic Media Tools (CEMT)

This program purpose is to convert stuff or things from sites into your device without having to go on
those convert to websites and get like 10 billion redirects to like some bs and let it take 50% of your time.

**[Download the Latest Release here](../../releases/latest)**

---

### Web Downloader
* You can download videos from a ton of sites,
* heres the [list of sites that are supported](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) in the web downloader
* The main ones being Youtube, Tiktok, Bilibili, Instagram, Twitch, and Vimeo,

### Spotify to MP3
* You can paste in a spotify album/track/playlist link
* Do note this does not bypass the Spotify DRM it only does a workaround by downloading a youtube video based on the song metadata.
* IF YOU GET a wrong song please use the Multiple Matches option to choose manually from the candidates.

### SoundCloud Downloader
* This can work with the web downloader but use this tab to have the album cover art and overall more customization.

### File Converter
* Convert files into other stuff

### GIF Converter
* Convert video files into gifs
* Customize FPS, width, and looping.

### Activity
* Keeps track of your downloads

---

## Tech Stack n Dependencies

* **Python 3.x**
* **CustomTkinter** (UI)
* **yt-dlp** (Media downloading engine)
* **ffmpeg** (Conversion and metadata embedding engine)
* **Pillow** (Image handling for the UI logo)

---

## How to Run from Source Code

### Required Tools
1. Install **Python 3.8 or higher** from [python.org](https://www.python.org/).
2. Download the latest **`yt-dlp.exe`** from the [official yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp/releases).
3. Download **`ffmpeg.exe`** (Essentials build) from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or the official ffmpeg website.

### Installation Steps
1. Install **Python 3.8 or higher** from [python.org](https://www.python.org/). *(Check "Add Python to PATH" during install).*
2. Clone or download this repository.
3. Download `yt-dlp.exe` and `ffmpeg.exe` and place them in the **same folder** as `CEMT.py`.
4. Open your terminal in that folder and install dependencies:
   ```bash
   pip install -r requirements.txt
