from flask import Flask, request, render_template, send_from_directory
import yt_dlp
import os
import re
import sys

app = Flask(__name__)

# --- Helpers ---
class MyLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

def safe_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name)

def reset_progress():
    global progress_line, last_id
    progress_line = ""
    last_id = None

progress_line = ""  # global tracker
last_id = None # initialization

def progress_hook(d):
    global last_id, progress_line
    current_id = d.get('info_dict', {}).get('id', None)

    if current_id != last_id:
        last_id = current_id

    if d['status'] == 'downloading':
        total = d.get('_total_bytes_str', 'unknown size')
        percent = d.get('_percent_str', '0.0%')
        speed = d.get('_speed_str', '?')
        eta = d.get('_eta_str', '?')

        progress_line = f"⬇️ {percent} of {total} at {speed} ETA {eta}"
        sys.stdout.write("\r" + progress_line.ljust(80))
        sys.stdout.flush()

    elif d['status'] == 'finished':
        progress_line = "✅ Download finished, now processing..."
        sys.stdout.write("\r" + progress_line + "\n")
        sys.stdout.flush()


def download_mp3(video_url, quality="128", save_path='downloads/'):
    reset_progress()
    os.makedirs(save_path, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(save_path, safe_filename('%(title)s')+'.%(ext)s'),
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,  # 👈 use selected quality
            },
            {
                'key': 'FFmpegMetadata',
            }
        ],
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
        'logger': MyLogger(),
        'noprogress': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
        filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(os.path.basename(filename))
        return base + ".mp3"
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def download_video(video_url, resolution="best", save_path='downloads/'):
    reset_progress()
    os.makedirs(save_path, exist_ok=True)

    # Resolution selector
    if resolution == "720":
        fmt = "bestvideo[height<=720]+bestaudio/best"
    elif resolution == "1080":
        fmt = "bestvideo[height<=1080]+bestaudio/best"
    elif resolution == "best":
        fmt = "bestvideo+bestaudio/best"
    else:
        print("⚠️ Invalid resolution choice. Defaulting to best quality.")
        fmt = "bestvideo+bestaudio/best"

    ydl_opts = {
        'format': fmt,
        'outtmpl': os.path.join(save_path, safe_filename('%(title)s')+'.%(ext)s'),
        'merge_output_format': 'mp4',   # Ensures MP4 container
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',    # Convert/merge into MP4
        },
        {
            'key': 'FFmpegMetadata',   # Embed metadata into MP4
         }],
        # Force audio re-encode to AAC
        'postprocessor_args': [
            '-c:v', 'copy',   # keep video stream untouched
            '-c:a', 'aac',    # re-encode audio to AAC
            '-b:a', '256k'    # set audio bitrate
        ],
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'quiet': True,        # suppress normal logs
        'no_warnings': True,  # suppress warnings
        'logger': MyLogger(),   # suppress all yt-dlp logs
        'noprogress': False,

    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
        filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(os.path.basename(filename))
        return base + ".mp4"
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        choice = request.form.get("choice")
        resolution = request.form.get("resolution", "best")
        quality = request.form.get("quality", "128")

        if choice == "audio":
            filename = download_mp3(url, quality=quality)
        else:
            filename = download_video(url, resolution)

        if filename is None:
            return render_template("index.html", message=None, filename=None)

        return render_template("index.html", message="✅ Download complete!", filename=filename)

    # Initial GET request — no message or filename
    reset_progress()
    return render_template("index.html", message=None, filename=None)


@app.route("/downloads/<path:filename>")
def download_file(filename):
    return send_from_directory("downloads", filename, as_attachment=True)

@app.route("/progress")
def progress():
    global progress_line
    return {"progress": progress_line}

if __name__ == "__main__":
    app.run(debug=True)




