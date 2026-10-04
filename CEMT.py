import os
import re
import json
import urllib.request
import subprocess
import sys
import threading
import time
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# config
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

APP_BG = "#4e575b"
CARD_BG = "#2d2a39"
CARD_BG_2 = "#211f2b"
BORDER = "#253241"
TEXT = "#F3F4F6"
SUBTEXT = "#8B98A8"
ACCENT = "#394555"
ACCENT_HOVER = "#2E3846"
GREEN = "#394555"
GREEN_HOVER = "#2E3846"
SPOTIFY = "#1DB954"
SPOTIFY_HOVER = "#1AA34A"
SOUNDCLOUD = "#FF5500"
SOUNDCLOUD_HOVER = "#E04B00"
RED = "#EF4444"

def get_bundle_dir():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_ytdlp_path():
    base_dir = get_bundle_dir()
    bundled = os.path.join(base_dir, "yt-dlp.exe")
    return bundled if os.path.exists(bundled) else "yt-dlp"

def get_ffmpeg_path():
    base_dir = get_bundle_dir()
    bundled = os.path.join(base_dir, "ffmpeg.exe")
    return bundled if os.path.exists(bundled) else "ffmpeg"

def get_activity_log_path():
    return os.path.join(os.path.expanduser("~"), ".cemt_activity.json")

# main
class CubesAllInOneApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("CEMT")
        self.geometry("600x750")
        self.minsize(600, 750)
        self.configure(fg_color=APP_BG)

        self.default_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(self.default_download_dir, exist_ok=True)

        self.bundle_dir = get_bundle_dir()
        self.ytdlp_path = get_ytdlp_path()
        self.ffmpeg_path = get_ffmpeg_path()

        self.global_output_dir = self.default_download_dir

        self.progress_regex = re.compile(r"(\d+(?:\.\d+)?)%")
        self.ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

        self.displayed_progress = 0.0
        self.target_progress = 0.0
        self.cancel_event = threading.Event()

        self._build_ui()
        self.after(20, self._animate_progress)

    def _browse_global_folder(self):
        selected = filedialog.askdirectory(initialdir=self.global_dir_entry.get())
        if selected:
            self.global_dir_entry.delete(0, "end")
            self.global_dir_entry.insert(0, selected)
            self.global_output_dir = selected

    def _update_global_dir(self):
        path = self.global_dir_entry.get().strip()
        if path:
            self.global_output_dir = path

    # ui
    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(20, 5))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")

        ctk.CTkLabel(title_frame, text="CEMT", font=("Segoe UI", 26, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Cubes Epic Media Tools", font=("Segoe UI", 12), text_color=SUBTEXT).pack(anchor="w")

        # Logo Image Space (Main Attraction)
        if HAS_PIL:
            logo_path = os.path.join(self.bundle_dir, "logo.png")
            if os.path.exists(logo_path):
                try:
                    logo_img = Image.open(logo_path)
                    self.logo_image = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(80, 80))
                    ctk.CTkLabel(header, image=self.logo_image, text="").pack(side="right", padx=10)
                except Exception:
                    pass

        self.status_dot = ctk.CTkLabel(header, text="Ready", font=("Segoe UI", 11, "bold"), text_color=GREEN)
        self.status_dot.pack(side="right", pady=8)

        # GLOBAL OUTPUT FOLDER
        global_folder_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER)
        global_folder_card.pack(fill="x", padx=28, pady=(0, 10))

        top_row = ctk.CTkFrame(global_folder_card, fg_color="transparent")
        top_row.pack(fill="x", padx=15, pady=(10, 5))

        self._label(top_row, "OUTPUT FOLDER", bold=True, color=TEXT).pack(side="left")
        self._label(top_row, "all downloads and conversions save here", size=10, color=SUBTEXT).pack(side="left", padx=(10, 0))

        folder_row = ctk.CTkFrame(global_folder_card, fg_color="transparent")
        folder_row.pack(fill="x", padx=15, pady=(0, 12))

        self.global_dir_entry = ctk.CTkEntry(folder_row, height=38)
        self.global_dir_entry.insert(0, self.global_output_dir)
        self.global_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(folder_row, text="Browse", width=90, height=38, command=self._browse_global_folder).pack(side="right")

        self.tabview = ctk.CTkTabview(
            self, width=650, fg_color=CARD_BG,
            segmented_button_fg_color="#0E141B",
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=ACCENT_HOVER
        )
        self.tabview.pack(fill="both", expand=True, padx=28, pady=(12, 10))

        # Social tab removed from here
        self.tab_web = self.tabview.add("Web Downloader")
        self.tab_converter = self.tabview.add("File Converter")
        self.tab_gif = self.tabview.add("GIF Converter")
        self.tab_spotify = self.tabview.add("Spotify")
        self.tab_soundcloud = self.tabview.add("SoundCloud")
        self.tab_activity = self.tabview.add("Activity")

        self._build_web_tab()
        # self._build_social_tab() removed
        self._build_converter_tab()
        self._build_gif_tab()
        self._build_spotify_tab()
        self._build_soundcloud_tab()
        self._build_activity_tab()
        self._build_bottom_progress()

    def _card(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=CARD_BG_2, corner_radius=14, border_width=1, border_color=BORDER)
        frame.pack(fill="x", padx=18, pady=8)
        return frame

    def _label(self, parent, text, size=11, bold=False, color=SUBTEXT):
        return ctk.CTkLabel(parent, text=text, font=("Segoe UI", size, "bold" if bold else "normal"), text_color=color)

    def _build_bottom_progress(self):
        self.bottom_progress_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER)
        
        top = ctk.CTkFrame(self.bottom_progress_frame, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=(10, 2))

        self.progress_status = ctk.CTkLabel(top, text="Ready", font=("Segoe UI", 11, "bold"), text_color=TEXT)
        self.progress_status.pack(side="left")

        self.cancel_btn = ctk.CTkButton(
            top, text="Cancel", width=80, height=26, fg_color=RED, hover_color="#DC2626",
            command=self._cancel_action, state="disabled"
        )
        self.cancel_btn.pack(side="right", padx=(10, 0))

        self.progress_bar = ctk.CTkProgressBar(self.bottom_progress_frame, height=9, corner_radius=8, fg_color="#202A35", progress_color=ACCENT)
        self.progress_bar.pack(fill="x", padx=15, pady=(3, 12))
        self.progress_bar.set(0)

    def _show_progress_ui(self):
        self.bottom_progress_frame.pack(fill="x", padx=28, pady=(5, 10))

    def _hide_progress_ui(self):
        self.bottom_progress_frame.pack_forget()

    def _cancel_action(self):
        self.cancel_event.set()
        self.progress_status.configure(text="Cancelling...")

    def _set_progress(self, percent, status):
        percent = max(0.0, min(100.0, float(percent)))
        self.target_progress = percent
        self.after(0, lambda: self.progress_status.configure(text=status))

    def _animate_progress(self):
        difference = self.target_progress - self.displayed_progress
        if abs(difference) > 0.05:
            self.displayed_progress += difference * 0.16
        else:
            self.displayed_progress = self.target_progress

        self.progress_bar.set(self.displayed_progress / 100.0)
        self.after(16, self._animate_progress)

    def _reset_buttons(self):
        self.cancel_event.clear()
        self.cancel_btn.configure(state="disabled")
        self.web_dl_btn.configure(state="normal", text="Download Media")
        self.convert_btn.configure(state="normal", text="Convert File")
        self.gif_convert_btn.configure(state="normal", text="Convert Video → GIF")
        self.spotify_btn.configure(state="normal", text="Match & Download MP3s")
        self.soundcloud_btn.configure(state="normal", text="Match & Download MP3s")
        self._hide_progress_ui()

    # env n http
    def _get_process_env(self):
        env = os.environ.copy()
        env["PATH"] = self.bundle_dir + os.path.pathsep + env.get("PATH", "")
        env["PYTHONUNBUFFERED"] = "1"
        return env

    def _http_get(self, url, timeout=20):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")

    # activity
    def log_activity(self, title, url, activity_type):
        log_path = get_activity_log_path()
        entry = {
            "title": title[:100],
            "url": url[:200],
            "type": activity_type,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        try:
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    data = json.load(f)
            else:
                data = []
            data.insert(0, entry)
            data = data[:500] # Keep only last 500 entries to save storage
            with open(log_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load_activity(self):
        for widget in self.activity_frame.winfo_children():
            widget.destroy()
            
        log_path = get_activity_log_path()
        if not os.path.exists(log_path):
            ctk.CTkLabel(self.activity_frame, text="No activity yet. Start downloading!", font=("Segoe UI", 14), text_color=SUBTEXT).pack(pady=40)
            return

        try:
            with open(log_path, 'r') as f:
                data = json.load(f)
        except Exception:
            data = []

        if not data:
            ctk.CTkLabel(self.activity_frame, text="No activity yet.", font=("Segoe UI", 14), text_color=SUBTEXT).pack(pady=40)
            return

        for item in data:
            row = ctk.CTkFrame(self.activity_frame, fg_color="transparent")
            row.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(row, text=f"[{item['type']}] {item['title']}", font=("Segoe UI", 12, "bold"), text_color=TEXT, anchor="w").pack(fill="x")
            ctk.CTkLabel(row, text=f"{item['date']}  •  {item['url']}", font=("Segoe UI", 11), text_color=SUBTEXT, anchor="w").pack(fill="x")
            ctk.CTkFrame(self.activity_frame, height=1, fg_color=BORDER).pack(fill="x", pady=2)

    def _clear_activity(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all activity history?"):
            log_path = get_activity_log_path()
            if os.path.exists(log_path):
                os.remove(log_path)
            self._load_activity()

    # SPOTIFY PLEASE
    def _get_spotify_cover_url(self, data):
        cover_art = self._find_key_recursive(data, "coverArt")
        if cover_art and isinstance(cover_art, dict):
            sources = cover_art.get("sources", [])
            if sources:
                sources.sort(key=lambda x: x.get("width", 0), reverse=True)
                return sources[0].get("url")
        
        def find_images(value):
            images = []
            if isinstance(value, dict):
                if "url" in value and "width" in value:
                    images.append((value["width"], value["url"]))
                for child in value.values():
                    images.extend(find_images(child))
            elif isinstance(value, list):
                for child in value:
                    images.extend(find_images(child))
            return images
        
        imgs = find_images(data)
        if imgs:
            imgs.sort(key=lambda x: x[0], reverse=True)
            return imgs[0][1]
        return None

    @staticmethod
    def _spotify_id_from_url(url, object_type):
        match = re.search(rf"spotify\.com/{object_type}/([A-Za-z0-9]+)", url, re.IGNORECASE)
        return match.group(1) if match else None

    def _spotify_type_from_url(self, url):
        match = re.search(r"spotify\.com/(track|playlist|album|artist)/[A-Za-z0-9]+", url, re.IGNORECASE)
        return match.group(1).lower() if match else None

    def _fetch_spotify_embed_json(self, object_type, spotify_id):
        embed_url = f"https://open.spotify.com/embed/{object_type}/{spotify_id}"
        html = self._http_get(embed_url)
        match = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        if not match:
            raise RuntimeError("Spotify did not expose public metadata. Make sure it is public.")
        return json.loads(match.group(1))

    def _find_key_recursive(self, value, wanted_key):
        if isinstance(value, dict):
            if wanted_key in value: return value[wanted_key]
            for child in value.values():
                result = self._find_key_recursive(child, wanted_key)
                if result is not None: return result
        elif isinstance(value, list):
            for child in value:
                result = self._find_key_recursive(child, wanted_key)
                if result is not None: return result
        return None

    def _find_all_key_recursive(self, value, wanted_key):
        results = []
        if isinstance(value, dict):
            if wanted_key in value: results.append(value[wanted_key])
            for child in value.values(): results.extend(self._find_all_key_recursive(child, wanted_key))
        elif isinstance(value, list):
            for child in value: results.extend(self._find_all_key_recursive(child, wanted_key))
        return results

    def _fetch_public_spotify_track(self, url):
        track_id = self._spotify_id_from_url(url, "track")
        if not track_id: raise ValueError("Invalid Spotify track URL.")
        data = self._fetch_spotify_embed_json("track", track_id)
        
        title = self._find_key_recursive(data, "title") or self._find_key_recursive(data, "name")
        artist = self._find_key_recursive(data, "subtitle") or self._find_key_recursive(data, "artist") or ""
        album = self._find_key_recursive(data, "album") or ""
        
        if isinstance(artist, list): artist = ", ".join(str(x) for x in artist if x)
        if isinstance(album, dict): album = album.get("name") or ""
        if not title: raise RuntimeError("Spotify did not expose this track.")
            
        return {
            "title": str(title), "artist": str(artist), "album": str(album) or str(title),
            "query": f"{artist} - {title}" if artist else str(title),
            "url": url
        }

    def _tracks_from_track_list(self, track_list, parent_cover_url=None, parent_album_name=None):
        tracks = []
        if not isinstance(track_list, list): return tracks
        for item in track_list:
            if not isinstance(item, dict): continue
            title = item.get("title") or item.get("name")
            artist = item.get("subtitle") or item.get("artist") or ""
            album = item.get("album") or ""
            
            if not title:
                nested = item.get("track")
                if isinstance(nested, dict):
                    title = nested.get("title") or nested.get("name")
                    artist = nested.get("subtitle") or nested.get("artist") or artist
                    album = nested.get("album") or album
            if not title: continue
                
            if isinstance(artist, list): artist = ", ".join(str(x) for x in artist if x)
            if isinstance(album, dict): album = album.get("name") or ""
            
            uri = item.get("uri") or (nested.get("uri") if isinstance(nested, dict) else None)
            track_url = f"https://open.spotify.com/track/{uri.split(':')[-1]}" if uri and "track" in uri else ""
                
            tracks.append({
                "title": str(title), "artist": str(artist),
                "album": str(album) or str(parent_album_name) or str(title),
                "query": f"{artist} - {title}" if artist else str(title),
                "url": track_url
            })
        return tracks

    def _fetch_public_spotify_playlist(self, url):
        playlist_id = self._spotify_id_from_url(url, "playlist")
        if not playlist_id: raise ValueError("Invalid Spotify playlist URL.")
        data = self._fetch_spotify_embed_json("playlist", playlist_id)
        playlist_name = self._find_key_recursive(data, "name") or self._find_key_recursive(data, "title") or "Spotify Playlist"
        
        tracks = []
        for track_list in self._find_all_key_recursive(data, "trackList"):
            tracks.extend(self._tracks_from_track_list(track_list, parent_album_name=playlist_name))
        if not tracks: raise RuntimeError("Playlist found, but no tracks exposed.")
        return str(playlist_name), self._deduplicate_tracks(tracks)

    def _fetch_public_spotify_album(self, url):
        album_id = self._spotify_id_from_url(url, "album")
        if not album_id: raise ValueError("Invalid Spotify album URL.")
        data = self._fetch_spotify_embed_json("album", album_id)
        album_name = self._find_key_recursive(data, "name") or self._find_key_recursive(data, "title") or "Spotify Album"
        
        tracks = []
        for track_list in self._find_all_key_recursive(data, "trackList"):
            tracks.extend(self._tracks_from_track_list(track_list, parent_album_name=album_name))
        if not tracks: raise RuntimeError("Album found, but no tracks exposed.")
        return str(album_name), self._deduplicate_tracks(tracks)

    def _extract_spotify_album_urls(self, html):
        pattern = re.compile(r"https?://open\.spotify\.com/album/([A-Za-z0-9]+)", re.IGNORECASE)
        return [match.group(1) for match in pattern.finditer(html)]

    def _fetch_public_spotify_artist(self, url):
        artist_id = self._spotify_id_from_url(url, "artist")
        if not artist_id: raise ValueError("Invalid Spotify artist URL.")
        html = self._http_get(f"https://open.spotify.com/artist/{artist_id}")
        artist_name = "Spotify Artist"
        try:
            match = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
            if match:
                data = json.loads(match.group(1))
                artist_name = self._find_key_recursive(data, "name") or artist_name
        except Exception: pass
        
        album_ids = self._extract_spotify_album_urls(html)
        if not album_ids: raise RuntimeError("No public album links found.")
        
        all_tracks = []
        for index, album_id in enumerate(album_ids, start=1):
            self._set_progress(min(25, (index / max(1, len(album_ids))) * 25), f"Reading album {index}/{len(album_ids)}...")
            try:
                _, tracks = self._fetch_public_spotify_album(f"https://open.spotify.com/album/{album_id}")
                all_tracks.extend(tracks)
            except Exception: continue
            
        if not all_tracks: raise RuntimeError("No public album tracks could be extracted.")
        return str(artist_name), self._deduplicate_tracks(all_tracks)

    def _deduplicate_tracks(self, tracks):
        result, seen = [], set()
        for track in tracks:
            title = re.sub(r"\s+", " ", str(track.get("title", "")).strip().lower())
            artist = re.sub(r"\s+", " ", str(track.get("artist", "")).strip().lower())
            key = (artist, title)
            if title and key not in seen:
                seen.add(key)
                result.append(track)
        return result

    def _safe_filename(self, value):
        value = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", value)
        value = re.sub(r"\s+", " ", value).strip().rstrip(".")
        return value[:180] or "Untitled"
    
    # match spotify with youtube thing
    def _normalize_search_text(self, value):
        value = value.lower()
        value = re.sub(r"\([^)]*\)", " ", value)
        value = re.sub(r"\[[^\]]*\]", " ", value)
        value = re.sub(r"[^a-z0-9\s]", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    def _score_youtube_result(self, result, track):
        expected_title = self._normalize_search_text(track["title"])
        expected_artist = self._normalize_search_text(track["artist"])
        title = self._normalize_search_text(result.get("title", ""))
        uploader = self._normalize_search_text(result.get("uploader", "") or result.get("channel", "") or "")
        text = title + " " + uploader
        score = 0

        if title == expected_title: score += 70
        elif expected_title in title: score += 55
        else:
            expected_words = set(expected_title.split())
            result_words = set(title.split())
            if expected_words: score += int((len(expected_words & result_words) / len(expected_words)) * 45)

        if expected_artist:
            artist_words = set(expected_artist.split())
            combined_words = set(text.split())
            if expected_artist in text: score += 35
            elif artist_words: score += int((len(artist_words & combined_words) / len(artist_words)) * 25)

        uploader_raw = (result.get("uploader", "") or result.get("channel", "") or "").lower()
        title_raw = (result.get("title", "") or "").lower()
        if "topic" in uploader_raw: score += 20
        if "vevo" in uploader_raw: score += 18
        if "official" in uploader_raw: score += 15
        if "official" in title_raw: score += 8
        if "provided to youtube" in title_raw: score += 12

        duration = result.get("duration")
        if duration:
            try:
                duration = float(duration)
                if 60 <= duration <= 600: score += 8
            except Exception: pass
        return score

    def _get_top_youtube_candidates(self, track, top_n=5):
        query = track["query"].strip()
        if not query: return []
        
        search_variants = [query, f'"{track["artist"]}" "{track["title"]}"' if track["artist"] else track["title"]]
        all_results = []
        
        for search_query in search_variants:
            cmd = [self.ytdlp_path, "--flat-playlist", "--dump-single-json", "--skip-download", "--no-warnings", "--no-playlist", f"ytsearch{top_n}:" + search_query]
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW if os.name == "nt" else 0
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=self._get_process_env(), startupinfo=startupinfo)
                stdout, stderr = process.communicate(timeout=45)
                if process.returncode == 0:
                    data = json.loads(stdout)
                    for result in data.get("entries", []):
                        if result and result.get("id"):
                            score = self._score_youtube_result(result, track)
                            all_results.append({
                                "url": result.get("webpage_url") or f"https://www.youtube.com/watch?v={result.get('id')}",
                                "title": result.get("title", "Unknown Title"),
                                "uploader": result.get("uploader") or result.get("channel", "Unknown Uploader"),
                                "score": score
                            })
            except Exception: continue
                
        seen = set()
        unique_results = []
        for res in sorted(all_results, key=lambda x: x["score"], reverse=True):
            if res["url"] not in seen:
                seen.add(res["url"])
                unique_results.append(res)
        return unique_results[:top_n]

    def _ask_for_candidate(self, track, candidates, result_holder, event):
        def create_dialog():
            dialog = ctk.CTkToplevel(self)
            dialog.title("Select YouTube Match")
            dialog.geometry("550x400")
            dialog.transient(self)
            dialog.grab_set()
            dialog.resizable(False, False)
            dialog.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() // 2) - 275
            y = self.winfo_rooty() + (self.winfo_height() // 2) - 200
            dialog.geometry(f"+{x}+{y}")
            
            ctk.CTkLabel(dialog, text=f"Multiple matches found for:\n{track.get('artist', '')} - {track.get('title', '')}\nPlease select the correct one:", font=("Segoe UI", 12, "bold"), justify="left").pack(pady=15, padx=20, anchor="w")
            
            def on_select(url):
                result_holder["url"] = url
                event.set()
                dialog.destroy()
                
            for cand in candidates[:5]:
                ctk.CTkButton(dialog, text=f"🎵 {cand['title'][:60]}\n👤 {cand['uploader'][:50]} (Score: {cand['score']})", anchor="w", height=50, command=lambda u=cand["url"]: on_select(u)).pack(fill="x", padx=20, pady=5)
            ctk.CTkButton(dialog, text="Skip this track", fg_color=RED, hover_color="#DC2626", command=lambda: on_select("SKIP")).pack(pady=15)
            dialog.protocol("WM_DELETE_WINDOW", lambda: on_select("SKIP"))
            
        self.after(0, create_dialog)

    # Soundcloud
    def _fetch_soundcloud_data(self, url):
        cmd = [self.ytdlp_path, "--dump-single-json", "--no-download", "--no-warnings", url]
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW if os.name == "nt" else 0
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=self._get_process_env(), startupinfo=startupinfo)
            stdout, stderr = process.communicate(timeout=120)
            
            if process.returncode != 0:
                raise RuntimeError(f"yt-dlp failed: {stderr}")
                
            data = json.loads(stdout)
            
            if data.get("_type") == "playlist":
                playlist_title = data.get("title", "SoundCloud Playlist")
                entries = data.get("entries", [])
                tracks = []
                for entry in entries:
                    if not entry: continue
                    tracks.append({
                        "title": entry.get("title", "Unknown Title"),
                        "artist": entry.get("uploader", "Unknown Artist"),
                        "album": entry.get("album", "") or entry.get("title", ""),
                        "url": entry.get("webpage_url") or url
                    })
                return playlist_title, tracks
            else:
                track = {
                    "title": data.get("title", "Unknown Title"),
                    "artist": data.get("uploader", "Unknown Artist"),
                    "album": data.get("album", "") or data.get("title", ""),
                    "url": data.get("webpage_url") or url
                }
                return None, [track]
        except Exception as e:
            raise RuntimeError(f"Failed to parse SoundCloud data: {str(e)}")

    # tabs
    def _build_web_tab(self):
        card = self._card(self.tab_web)
        self._label(card, "MEDIA URL (youtube, tiktok, bilibili, instagram, twitch, vimeo, etc)", bold=True).pack(anchor="w", padx=15, pady=(15, 5))
        self.web_url_entry = ctk.CTkEntry(card, height=38, placeholder_text="Paste a video or audio URL")
        self.web_url_entry.pack(fill="x", padx=15, pady=(0, 15))

        options = ctk.CTkFrame(card, fg_color="transparent")
        options.pack(fill="x", padx=15, pady=5)

        self._label(options, "FORMAT", bold=True).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.web_fmt_option = ctk.CTkOptionMenu(options, values=["BEST (Original)", "MP4 (Video)", "MP3 (Audio Only)", "WAV (Audio)"], width=220, command=self._toggle_web_quality_state)
        self.web_fmt_option.set("BEST (Original)") # Default format
        self.web_fmt_option.grid(row=1, column=0, padx=(0, 20))

        self._label(options, "MAX QUALITY", bold=True).grid(row=0, column=1, sticky="w", pady=(0, 5))
        self.web_quality_option = ctk.CTkOptionMenu(options, values=["Best Available", "2160p (4K)", "1080p (FHD)", "720p (HD)", "480p (SD)", "360p (Low)"], width=220)
        self.web_quality_option.grid(row=1, column=1)

        self.web_dl_btn = ctk.CTkButton(self.tab_web, text="Download Media", height=46, corner_radius=12, font=("Segoe UI", 13, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self._start_web_download)
        self.web_dl_btn.pack(fill="x", padx=18, pady=14)

    def _build_converter_tab(self):
        card = self._card(self.tab_converter)
        self._label(card, "SOURCE FILE", bold=True).pack(anchor="w", padx=15, pady=(15, 5))
        
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(0, 15))
        self.local_file_entry = ctk.CTkEntry(row, height=38, placeholder_text="Choose a file...")
        self.local_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(row, text="Browse", width=100, height=38, command=self._select_local_file).pack(side="right")

        self._label(card, "OUTPUT FORMAT", bold=True).pack(anchor="w", padx=15, pady=(5, 5))
        self.target_fmt_option = ctk.CTkOptionMenu(card, values=["MP3 (Audio)", "MP4 (Video)", "WAV (Audio)", "MKV (Video)", "AVI (Video)", "WEBM (Video)", "AAC (Audio)", "FLAC (Audio)", "JPG (Image)", "PNG (Image)"], width=250)
        self.target_fmt_option.pack(anchor="w", padx=15, pady=(0, 15))

        self.convert_btn = ctk.CTkButton(self.tab_converter, text="Convert File", height=46, corner_radius=12, font=("Segoe UI", 13, "bold"), fg_color=GREEN, hover_color=GREEN_HOVER, command=self._start_local_conversion)
        self.convert_btn.pack(fill="x", padx=18, pady=15)

    def _build_gif_tab(self):
        card = self._card(self.tab_gif)
        self._label(card, "VIDEO SOURCE", bold=True).pack(anchor="w", padx=15, pady=(15, 5))
        
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(0, 15))
        self.gif_input = ctk.CTkEntry(row, height=38, placeholder_text="Choose a video...")
        self.gif_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(row, text="Browse", width=100, height=38, command=self._select_gif_input).pack(side="right")

        settings = ctk.CTkFrame(card, fg_color="transparent")
        settings.pack(fill="x", padx=15, pady=5)

        self._label(settings, "FPS", bold=True).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.gif_fps = ctk.CTkOptionMenu(settings, values=["10", "12", "15", "20", "24", "30", "60"], width=150)
        self.gif_fps.set("15")
        self.gif_fps.grid(row=1, column=0, padx=(0, 15))

        self._label(settings, "QUALITY", bold=True).grid(row=0, column=1, sticky="w", pady=(0, 5))
        self.gif_quality = ctk.CTkOptionMenu(settings, values=["Low", "Medium", "High", "Very High"], width=150)
        self.gif_quality.set("High")
        self.gif_quality.grid(row=1, column=1, padx=(0, 15))

        self._label(settings, "WIDTH", bold=True).grid(row=0, column=2, sticky="w", pady=(0, 5))
        self.gif_width = ctk.CTkOptionMenu(settings, values=["Original", "480", "640", "720", "1080"], width=150)
        self.gif_width.set("640")
        self.gif_width.grid(row=1, column=2)

        self.gif_loop = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(card, text="Loop GIF continuously", variable=self.gif_loop).pack(anchor="w", padx=15, pady=12)

        self.gif_convert_btn = ctk.CTkButton(self.tab_gif, text="Convert Video → GIF", height=46, corner_radius=12, font=("Segoe UI", 13, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self._start_gif_conversion)
        self.gif_convert_btn.pack(fill="x", padx=18, pady=15)

    def _build_spotify_tab(self):
        card = self._card(self.tab_spotify)
        self._label(card, "PUBLIC SPOTIFY TRACK / PLAYLIST / ALBUM / ARTIST", bold=True).pack(anchor="w", padx=15, pady=(15, 5))
        self.spotify_entry = ctk.CTkEntry(card, height=38, placeholder_text="Paste a public Spotify track, playlist, album, artist")
        self.spotify_entry.pack(fill="x", padx=15, pady=(0, 15))

        options_row = ctk.CTkFrame(self.tab_spotify, fg_color="transparent")
        options_row.pack(fill="x", padx=18, pady=5)
        
        self.spotify_playlist_folder = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(options_row, text="Separate folder for playlists", variable=self.spotify_playlist_folder).pack(side="left", padx=15)
        
        self.spotify_include_url = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(options_row, text="Include URL in filename", variable=self.spotify_include_url).pack(side="left", padx=15)

        self.spotify_always_ask = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(options_row, text="Multiple Matches", variable=self.spotify_always_ask).pack(side="left", padx=15)

        self._label(self.tab_spotify, "YO If you get the wrong song, enable 'Multiple Matches' to manually pick the correct one.", size=10, color="#8B98A8").pack(anchor="w", padx=18, pady=(0, 5))

        self._label(self.tab_spotify, "FILENAME FORMAT", bold=True).pack(anchor="w", padx=18, pady=(5, 5))
        self.spotify_filename_format = ctk.CTkOptionMenu(self.tab_spotify, values=["Artist - Title", "Title Only", "Artist - Album - Title"], width=250)
        self.spotify_filename_format.set("Artist - Title")
        self.spotify_filename_format.pack(anchor="w", padx=18, pady=(0, 12))

        self.spotify_btn = ctk.CTkButton(self.tab_spotify, text="Match & Download MP3s", height=46, corner_radius=12, font=("Segoe UI", 13, "bold"), fg_color=SPOTIFY, hover_color=SPOTIFY_HOVER, command=self._start_spotify_download)
        self.spotify_btn.pack(fill="x", padx=18, pady=14)

    def _build_soundcloud_tab(self):
        card = self._card(self.tab_soundcloud)
        self._label(card, "SOUNDCLOUD TRACK OR PLAYLIST URL", bold=True).pack(anchor="w", padx=15, pady=(15, 5))
        self.soundcloud_entry = ctk.CTkEntry(card, height=38, placeholder_text="Paste a SoundCloud track or playlist URL")
        self.soundcloud_entry.pack(fill="x", padx=15, pady=(0, 15))

        options_row = ctk.CTkFrame(self.tab_soundcloud, fg_color="transparent")
        options_row.pack(fill="x", padx=18, pady=5)
        
        self.soundcloud_playlist_folder = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(options_row, text="Create separate folder for playlists", variable=self.soundcloud_playlist_folder).pack(side="left", padx=15)
        
        self.soundcloud_include_url = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(options_row, text="Include source URL in filename", variable=self.soundcloud_include_url).pack(side="left", padx=15)

        self._label(self.tab_soundcloud, "FILENAME FORMAT", bold=True).pack(anchor="w", padx=18, pady=(5, 5))
        self.soundcloud_filename_format = ctk.CTkOptionMenu(self.tab_soundcloud, values=["Artist - Title", "Title Only", "Artist - Album - Title"], width=250)
        self.soundcloud_filename_format.set("Artist - Title")
        self.soundcloud_filename_format.pack(anchor="w", padx=18, pady=(0, 12))

        self.soundcloud_btn = ctk.CTkButton(self.tab_soundcloud, text="Match & Download MP3s", height=46, corner_radius=12, font=("Segoe UI", 13, "bold"), fg_color=SOUNDCLOUD, hover_color=SOUNDCLOUD_HOVER, command=self._start_soundcloud_download)
        self.soundcloud_btn.pack(fill="x", padx=18, pady=14)

    def _build_activity_tab(self):
        self.activity_frame = ctk.CTkScrollableFrame(self.tab_activity, fg_color=CARD_BG_2, corner_radius=14, border_width=1, border_color=BORDER)
        self.activity_frame.pack(fill="both", expand=True, padx=18, pady=8)
        
        btn_frame = ctk.CTkFrame(self.tab_activity, fg_color="transparent")
        btn_frame.pack(fill="x", padx=18, pady=(0, 10))
        
        ctk.CTkButton(btn_frame, text="Refresh History", width=120, height=32, command=self._load_activity).pack(side="left")
        ctk.CTkButton(btn_frame, text="Clear History", width=120, height=32, fg_color=RED, hover_color="#DC2626", command=self._clear_activity).pack(side="right")
        
        self._load_activity()

    # stuff
    def _toggle_web_quality_state(self, choice):
        self.web_quality_option.configure(state="disabled" if "MP3" in choice or "WAV" in choice else "normal")

    def _select_local_file(self):
        file_path = filedialog.askopenfilename(title="Select File", filetypes=[("All Files", "*.*")])
        if file_path:
            self.local_file_entry.delete(0, "end")
            self.local_file_entry.insert(0, file_path)

    def _select_gif_input(self):
        path = filedialog.askopenfilename(title="Select Video", filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov *.webm *.wmv *.flv"), ("All Files", "*.*")])
        if path:
            self.gif_input.delete(0, "end")
            self.gif_input.insert(0, path)

    def _start_web_download(self):
        url = self.web_url_entry.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Enter a media URL first.")
            return
        if not os.path.exists(self.ytdlp_path) and self.ytdlp_path != "yt-dlp":
            messagebox.showerror("yt-dlp Missing", f"yt-dlp was not found:\n{self.ytdlp_path}")
            return

        self.cancel_event.clear()
        self.cancel_btn.configure(state="normal")
        self.web_dl_btn.configure(state="disabled", text="Downloading...")
        self._set_progress(0, "Connecting...")
        self._show_progress_ui()
        threading.Thread(target=self._run_ytdlp, args=(url,), daemon=True).start()

    def _start_local_conversion(self):
        input_file = self.local_file_entry.get().strip()
        if not input_file or not os.path.exists(input_file):
            messagebox.showwarning("Missing File", "Please select a valid file.")
            return

        self.cancel_event.clear()
        self.cancel_btn.configure(state="normal")
        self.convert_btn.configure(state="disabled", text="Converting...")
        self._set_progress(0, "Starting FFmpeg...")
        self._show_progress_ui()
        threading.Thread(target=self._run_local_ffmpeg, args=(input_file,), daemon=True).start()

    def _start_gif_conversion(self):
        input_file = self.gif_input.get().strip()
        if not input_file or not os.path.exists(input_file):
            messagebox.showwarning("Missing Video", "Please select a valid video.")
            return

        self.cancel_event.clear()
        self.cancel_btn.configure(state="normal")
        self.gif_convert_btn.configure(state="disabled", text="Creating GIF...")
        self._set_progress(0, "Preparing GIF conversion...")
        self._show_progress_ui()
        threading.Thread(target=self._run_gif_conversion, args=(input_file,), daemon=True).start()

    def _start_spotify_download(self):
        query = self.spotify_entry.get().strip()
        if not query:
            messagebox.showwarning("Missing Input", "Enter a Spotify track, playlist, album, artist, or song name.")
            return
        if not os.path.exists(self.ytdlp_path) and self.ytdlp_path != "yt-dlp":
            messagebox.showerror("yt-dlp Missing", f"yt-dlp was not found:\n{self.ytdlp_path}")
            return

        self.cancel_event.clear()
        self.cancel_btn.configure(state="normal")
        self.spotify_btn.configure(state="disabled", text="Preparing...")
        self._set_progress(0, "Reading Spotify metadata...")
        self._show_progress_ui()
        threading.Thread(target=self._process_spotify_queue, args=(query, True), daemon=True).start()

    def _start_soundcloud_download(self):
        query = self.soundcloud_entry.get().strip()
        if not query:
            messagebox.showwarning("Missing Input", "Enter a SoundCloud track or playlist URL.")
            return
        if not os.path.exists(self.ytdlp_path) and self.ytdlp_path != "yt-dlp":
            messagebox.showerror("yt-dlp Missing", f"yt-dlp was not found:\n{self.ytdlp_path}")
            return

        self.cancel_event.clear()
        self.cancel_btn.configure(state="normal")
        self.soundcloud_btn.configure(state="disabled", text="Preparing...")
        self._set_progress(0, "Reading SoundCloud metadata...")
        self._show_progress_ui()
        threading.Thread(target=self._process_soundcloud_queue, args=(query,), daemon=True).start()

    def _run_ytdlp(self, target):
        output_dir = self.global_output_dir
        success, error = self._execute_ytdlp_cmd(target, is_audio_only=False, output_dir=output_dir)
        if self.cancel_event.is_set():
            self.after(0, self._on_error, "Download cancelled by user.")
        elif success:
            self.log_activity(os.path.basename(target), target, "Web")
            self.after(0, lambda: self._on_success("Download Complete!", output_dir))
        else:
            self.after(0, lambda: self._on_error(error))

    def _run_local_ffmpeg(self, input_file):
        target_ext = self.target_fmt_option.get().split()[0].lower()
        output_dir = self.global_output_dir
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(input_file))[0] + "_converted." + target_ext)

        cmd = [self.ffmpeg_path, "-y", "-i", input_file, output_file]
        self._run_subprocess(cmd, "Converter", success_msg="Conversion Complete!", out_path=output_file)

    def _run_gif_conversion(self, input_file):
        fps = int(self.gif_fps.get())
        width = self.gif_width.get()
        quality = self.gif_quality.get()
        
        colors = 64 if quality == "Low" else 128 if quality == "Medium" else 256 if quality == "Very High" else 192
        scale = f"fps={fps},split[s0][s1];[s0]palettegen=max_colors={colors}:stats_mode=diff[p];[s1][p]paletteuse=dither=sierra2_4a"
        if width != "Original":
            scale = f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors={colors}:stats_mode=diff[p];[s1][p]paletteuse=dither=sierra2_4a"

        output_dir = self.global_output_dir
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(input_file))[0] + ".gif")

        cmd = [self.ffmpeg_path, "-y", "-i", input_file, "-vf", scale, "-loop", "0" if self.gif_loop.get() else "-1", output_file]
        self._run_subprocess(cmd, "GIF", success_msg="GIF Created!", out_path=output_file)

    def _run_subprocess(self, cmd, activity_type, success_msg="Complete!", out_path=None):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW if os.name == "nt" else 0
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=self._get_process_env(), startupinfo=startupinfo)
            
            output_lines = []
            while True:
                if self.cancel_event.is_set():
                    process.terminate()
                    try: process.wait(timeout=2)
                    except subprocess.TimeoutExpired: process.kill()
                    self.after(0, self._on_error, "Conversion cancelled by user.")
                    return
                
                line = process.stdout.readline()
                if not line and process.poll() is not None: break
                if line: output_lines.append(line)
                    
            if self.cancel_event.is_set(): return
                
            if process.returncode == 0:
                if out_path: self.log_activity(os.path.basename(out_path), out_path, activity_type)
                self.after(0, lambda: self._on_success(success_msg, out_path or self.global_output_dir))
            else:
                self.after(0, lambda: self._on_error("".join(output_lines)[-2000:] or "FFmpeg conversion failed."))
        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _execute_ytdlp_cmd(self, target, is_audio_only, output_dir=None, output_template=None, progress_callback=None, extra_args=None):
        output_dir = output_dir or self.global_output_dir
        os.makedirs(output_dir, exist_ok=True)

        cmd = [self.ytdlp_path, "--newline", "--no-colors", "--ffmpeg-location", self.bundle_dir]
        if output_template:
            cmd.extend(["-o", output_template])
        else:
            cmd.extend(["-P", output_dir, "-o", "%(title)s.%(ext)s"])
            
        if is_audio_only:
            cmd.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0", "--embed-thumbnail", "--add-metadata"])
        else:
            fmt = self.web_fmt_option.get()
            quality = self.web_quality_option.get()
            if "MP3" in fmt:
                cmd.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0", "--embed-thumbnail", "--add-metadata"])
            elif "WAV" in fmt:
                cmd.extend(["-x", "--audio-format", "wav", "--add-metadata"])
            elif "MP4" in fmt:
                if quality == "2160p (4K)": format_str = "bestvideo[height<=2160]+bestaudio/best"
                elif quality == "1080p (FHD)": format_str = "bestvideo[height<=1080]+bestaudio/best"
                elif quality == "720p (HD)": format_str = "bestvideo[height<=720]+bestaudio/best"
                elif quality == "480p (SD)": format_str = "bestvideo[height<=480]+bestaudio/best[height<=480]"
                elif quality == "360p (Low)": format_str = "bestvideo[height<=360]+bestaudio/best[height<=360]"
                else: format_str = "bestvideo+bestaudio/best"
                cmd.extend(["-f", format_str, "--remux-video", "mp4", "--embed-thumbnail", "--add-metadata"])

        if extra_args:
            cmd.extend(extra_args)
        cmd.append(target)

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW if os.name == "nt" else 0
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=self._get_process_env(), startupinfo=startupinfo)

            log_output, buffer = [], ""
            while True:
                if self.cancel_event.is_set():
                    process.terminate()
                    try: process.wait(timeout=2)
                    except subprocess.TimeoutExpired: process.kill()
                    return False, "Cancelled by user"

                char = process.stdout.read(1)
                if not char and process.poll() is not None:
                    break

                if char in ("\r", "\n"):
                    line = self.ansi_escape.sub("", buffer).strip()
                    buffer = ""
                    if line:
                        log_output.append(line)
                    if "[download]" in line:
                        match = self.progress_regex.search(line)
                        if match:
                            try:
                                val = float(match.group(1))
                                if progress_callback:
                                    progress_callback(val)
                                else:
                                    self._set_progress(val, f"Downloading: {val:.1f}%")
                            except ValueError:
                                pass
                else:
                    buffer += char

            process.wait()
            if self.cancel_event.is_set():
                return False, "Cancelled by user"
                
            if process.returncode == 0:
                return True, None
                
            error = "\n".join(log_output[-20:]) if log_output else "yt-dlp exited with an error."
            return False, error
        except Exception as e:
            return False, str(e)

    # download
    def _process_download_queue(self, tracks, collection_name, is_spotify=True):
        try:
            if not tracks:
                raise RuntimeError("No track metadata was found.")

            output_dir = os.path.abspath(os.path.expanduser(self.global_output_dir))
            playlist_folder_var = self.spotify_playlist_folder if is_spotify else self.soundcloud_playlist_folder
            if collection_name and playlist_folder_var.get():
                output_dir = os.path.join(output_dir, self._safe_filename(collection_name))
            os.makedirs(output_dir, exist_ok=True)

            total = len(tracks)
            succeeded, failed = 0, []

            for idx, track in enumerate(tracks, start=1):
                if self.cancel_event.is_set():
                    break
                    
                self._set_progress(((idx - 1) / total) * 100, f"Finding {idx}/{total}: {track['title']}")
                
                if is_spotify:
                    candidates = self._get_top_youtube_candidates(track, top_n=5)
                    if not candidates:
                        failed.append({"track": track["query"], "error": "No YouTube results found."})
                        continue
                        
                    best = candidates[0]
                    target_url = None
                    
                    always_ask = self.spotify_always_ask.get()
                    
                    if always_ask and len(candidates) > 1:
                        result_holder = {"url": None}
                        event = threading.Event()
                        self.after(0, self._ask_for_candidate, track, candidates, result_holder, event)
                        
                        while not event.is_set() and not self.cancel_event.is_set():
                            event.wait(0.5)
                            
                        if self.cancel_event.is_set():
                            break
                            
                        target_url = result_holder["url"]
                        if target_url == "SKIP":
                            failed.append({"track": track["query"], "error": "Skipped by user."})
                            continue
                        elif not target_url:
                            failed.append({"track": track["query"], "error": "No selection made."})
                            continue
                    else:
                        target_url = best["url"]
                        self._set_progress(((idx - 1) / total) * 100, f"Matched {idx}/{total} (Score: {best['score']}) • {track['title']}")
                else:
                    target_url = track["url"]
                    self._set_progress(((idx - 1) / total) * 100, f"Preparing {idx}/{total} • {track['title']}")

                if self.cancel_event.is_set():
                    break

                filename_format = self.spotify_filename_format.get() if is_spotify else self.soundcloud_filename_format.get()
                if filename_format == "Title Only":
                    filename = track["title"]
                elif filename_format == "Artist - Album - Title":
                    parts = []
                    if track["artist"]: parts.append(track["artist"])
                    if track["album"]: parts.append(track["album"])
                    parts.append(track["title"])
                    filename = " - ".join(parts)
                else:
                    filename = f"{track['artist']} - {track['title']}" if track["artist"] else track["title"]
                    
                include_url = self.spotify_include_url.get() if is_spotify else self.soundcloud_include_url.get()
                if include_url and track.get("url"):
                    safe_url = track["url"].replace("://", "_").replace("/", "_").replace("?", "_").replace("&", "_").replace("=", "_")
                    safe_url = safe_url[:100]
                    filename = f"{filename} - {safe_url}"
                    
                filename = self._safe_filename(filename)
                output_file = os.path.join(output_dir, filename + ".mp3")

                success, last_error = False, None
                for attempt in range(1, 4):
                    if self.cancel_event.is_set():
                        break
                        
                    self._set_progress(((idx - 1) / total) * 100, f"Track {idx}/{total} • Download attempt {attempt}/3 • {track['title']}")
                    
                    extra_args = ["--no-playlist"]

                    def progress_callback(percent, current=idx, current_track=track):
                        if self.cancel_event.is_set(): return
                        aggregate = (((current - 1) + (percent / 100.0)) / total) * 100.0
                        self._set_progress(aggregate, f"Track {current}/{total} • {percent:.1f}% • {current_track['title']}")

                    success, last_error = self._execute_ytdlp_cmd(
                        target_url, is_audio_only=True, output_dir=output_dir,
                        output_template=os.path.join(output_dir, filename + ".%(ext)s"), 
                        progress_callback=progress_callback, extra_args=extra_args
                    )
                    if success or self.cancel_event.is_set():
                        break
                    time.sleep(1.5)

                if success and not self.cancel_event.is_set():
                    succeeded += 1
                    self.log_activity(track.get("title", "Unknown"), track.get("url", ""), "Spotify" if is_spotify else "SoundCloud")
                elif not self.cancel_event.is_set():
                    failed.append({"track": track.get("query") or track["title"], "error": last_error or "Unknown download error."})

            if self.cancel_event.is_set():
                self.after(0, self._on_error, "Download cancelled by user.")
            else:
                self._set_progress(100, f"Finished {succeeded}/{total}")
                self.after(0, self._on_download_success, succeeded, total, output_dir, failed, is_spotify)

        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _process_spotify_queue(self, input_str, is_spotify=True):
        try:
            spotify_type = self._spotify_type_from_url(input_str)
            collection_name = None

            if spotify_type == "playlist":
                collection_name, tracks = self._fetch_public_spotify_playlist(input_str)
            elif spotify_type == "album":
                collection_name, tracks = self._fetch_public_spotify_album(input_str)
            elif spotify_type == "artist":
                collection_name, tracks = self._fetch_public_spotify_artist(input_str)
            elif spotify_type == "track":
                track = self._fetch_public_spotify_track(input_str)
                tracks = [track] if track else []
            else:
                tracks = [{"title": input_str, "artist": "", "album": "", "query": input_str, "url": ""}]

            tracks = [t for t in tracks if t and t.get("query")]
            tracks = self._deduplicate_tracks(tracks)
            self._process_download_queue(tracks, collection_name, is_spotify=True)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _process_soundcloud_queue(self, input_str):
        try:
            collection_name, tracks = self._fetch_soundcloud_data(input_str)
            self._process_download_queue(tracks, collection_name, is_spotify=False)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    # error/success thingy
    def _on_download_success(self, succeeded, total, output_dir, failed, is_spotify):
        self._reset_buttons()
        self._set_progress(100, f"Finished {succeeded}/{total}")
        self.status_dot.configure(text="Complete", text_color=GREEN)

        platform_name = "Spotify" if is_spotify else "SoundCloud"
        if failed:
            failed_preview = "\n".join(f"• {item['track']}" for item in failed[:8])
            message = f"Downloaded {succeeded}/{total} tracks.\n\n{len(failed)} track(s) could not be matched or downloaded.\n\n{failed_preview}"
            if len(failed) > 8:
                message += f"\n\n...and {len(failed) - 8} more."
            messagebox.showwarning(f"{platform_name} Finished", message)
        else:
            messagebox.showinfo(f"{platform_name} Finished", f"All {total} tracks downloaded successfully.")

        if os.path.exists(output_dir):
            try: os.startfile(output_dir)
            except Exception: pass

    def _on_success(self, message, path):
        self._reset_buttons()
        self._set_progress(100, message)
        self.status_dot.configure(text="Complete", text_color=GREEN)
        if os.path.exists(path):
            try:
                if os.path.isfile(path):
                    os.startfile(os.path.dirname(path))
                else:
                    os.startfile(path)
            except Exception: pass

    def _on_error(self, error):
        self._reset_buttons()
        self._set_progress(0, "Action failed")
        self.status_dot.configure(text="Error", text_color=RED)
        messagebox.showerror("Execution Error", "An error occurred:\n\n" + str(error)[:3000])

if __name__ == "__main__":
    app = CubesAllInOneApp()
    app.mainloop()