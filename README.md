# Cubes Epic Media Tools (CEMT)

**Open-Source Media Suite for Windows a bit for linux**

This program purpose is to convert stuff or things from sites into your device without having to go on
those convert to websites and get like 10 billion redirects to like some bs and let it take 50% of your time.

# Download it here
**[Download the latest Windows .exe here](../../releases/latest)**

> **Security & Transparency Note:** 
> this project is open-source. the application simply provides a visual interface for `yt-dlp` and `ffmpeg`. your antivirus might flag it as a "false positive" (this is a known issue with PyInstaller). **for security, you are encouraged to read the `CEMT.py` source code and run it directly via Python.**

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

---

## Tech Stack & Dependencies

This app does not contain any malicious payloads. It relies on three standard, widely-used open-source components:

1. **Python 3.x** (The core programming language)
2. **CustomTkinter** (For the modern GUI)
3. **yt-dlp** (The engine for downloading web media)
4. **ffmpeg** (The engine for converting files and embedding metadata/cover art)

---

## How to Run from Source Code

Running from the source code confirms you are not running a virus. 👍👍

### Prerequisites
1. Install **Python 3.8 or higher** from [python.org](https://www.python.org/).
2. Download the latest **`yt-dlp.exe`** from the [official yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp/releases).
3. Download **`ffmpeg.exe`** (Essentials build) from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or the official ffmpeg website.

### Installation Steps
1. Clone or download this repository to your computer.
2. Place `yt-dlp.exe` and `ffmpeg.exe` in the **same folder** as `CEMT.py`.
3. Open your terminal/command prompt in that folder and install the GUI library:
   ```bash
   pip install customtkinter
