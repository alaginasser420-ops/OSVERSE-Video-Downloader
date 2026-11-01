# OSVERSE Video Downloader

A local-first web interface for downloading publicly accessible videos using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Features

- Arabic, responsive web interface
- Video metadata preview (title, thumbnail, uploader, duration)
- Best available quality or up to 1080p / 720p / 480p / 360p
- MP3 audio extraction
- Progress display and download link
- yt-dlp support for many websites, including supported X and Reddit URLs

> Platform support changes over time. A site may require cookies/login, block automated requests, or change its player. No downloader can guarantee every URL or every quality.

## Requirements

- Windows 10/11
- Python 3.10 or newer (64-bit recommended)
- FFmpeg for merging separate audio/video streams and MP3 extraction
- Git (optional, for cloning and publishing)

## Run on Windows with Git Bash

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/OSVERSE-Video-Downloader.git
cd OSVERSE-Video-Downloader
```

If you have downloaded the ZIP from GitHub instead, extract it and use `cd` to enter the project folder.

### 2. Create and activate a virtual environment

```bash
py -3 -m venv .venv
source .venv/Scripts/activate
```

If `py` is not recognized, install Python from https://www.python.org/downloads/ and enable **Add Python to PATH**.

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install FFmpeg

Install FFmpeg and make sure `ffmpeg -version` works in Git Bash. One Windows option is:

```bash
winget install Gyan.FFmpeg
```

Close and reopen Git Bash after installation, then check:

```bash
ffmpeg -version
```

### 5. Start the app

```bash
python app.py
```

Open this address in your browser:

http://127.0.0.1:5000

Stop the server with `Ctrl+C`.

## Publish to your GitHub account

Create an empty repository on GitHub named `OSVERSE-Video-Downloader` (do not initialize it with a README), then run inside the project folder:

```bash
git init
git add .
git commit -m "Initial OSVERSE Video Downloader"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/OSVERSE-Video-Downloader.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username.

## Updating yt-dlp

Video sites frequently change. Update the downloader when a site stops working:

```bash
python -m pip install -U yt-dlp
```

Then restart the app.

## Security notes

- The development server binds to `127.0.0.1` only. Keep it local; do not expose it to the public internet as-is.
- URL validation rejects local/private network addresses as a basic SSRF mitigation. This is not a substitute for a hardened public service.
- Do not add `debug=True` or bind to `0.0.0.0` on an untrusted network.
- Use only for videos you own, have permission to download, or are otherwise legally allowed to save. Respect platform terms, copyright, privacy, and access controls.
- The project does not bypass DRM, paywalls, private-account restrictions, or other access controls.

## Troubleshooting

**`ffmpeg is not installed`:** install FFmpeg, reopen the terminal, and run `ffmpeg -version`.

**A URL is unsupported:** update yt-dlp, then retry. Some sites require browser cookies or login; this starter app intentionally does not import browser cookies.

**HTTP 403 / sign-in required:** the platform may restrict automated downloads. Do not attempt to bypass access controls. Try an authorized export or official download option.

**No formats available:** the source may not expose a downloadable format, or the platform may be blocking the request.

## License

MIT. See `LICENSE`.
