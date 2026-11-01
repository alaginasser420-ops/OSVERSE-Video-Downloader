from __future__ import annotations

import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp


def validate_public_url(url: str) -> None:
    """Accept public HTTP(S) URLs only; the app is intended for local use."""
    if not url:
        raise ValueError("أدخل رابط الفيديو أولاً.")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("الرابط يجب أن يبدأ بـ http:// أو https://")
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("روابط الأجهزة المحلية غير مسموح بها.")
    try:
        addresses = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            addresses = {
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            }
        except socket.gaierror as exc:
            raise ValueError("تعذر العثور على عنوان الموقع. تحقق من الرابط والاتصال.") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("هذا الرابط لا يشير إلى عنوان إنترنت عام، وقد تم رفضه لأسباب أمنية.")


def _base_options():
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "restrictfilenames": True,
        "windowsfilenames": True,
        "socket_timeout": 20,
        "retries": 2,
        "fragment_retries": 2,
    }


def inspect_video(url: str) -> dict:
    options = _base_options()
    options.update({"skip_download": True})
    with yt_dlp.YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=False)


def download_video(url: str, quality: str, output_dir: Path, progress_hook=None) -> Path:
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(title).150B-%(id)s.%(ext)s")

    if quality == "audio":
        format_selector = "bestaudio/best"
    elif quality == "best":
        format_selector = "bv*+ba/b"
    else:
        height = int(quality)
        format_selector = f"bv*[height<={height}]+ba/b[height<={height}]/b"

    options = _base_options()
    options.update({
        "format": format_selector,
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "progress_hooks": [progress_hook] if progress_hook else [],
    })

    if quality == "audio":
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = Path(ydl.prepare_filename(info))
        if quality == "audio":
            filename = filename.with_suffix(".mp3")
        elif not filename.exists():
            # yt-dlp may merge into a different extension/container.
            candidates = list(output_dir.glob(f"*{info.get('id', '')}*"))
            if candidates:
                filename = max(candidates, key=lambda p: p.stat().st_mtime)
        if not filename.exists():
            candidates = sorted(output_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not candidates:
                raise RuntimeError("اكتمل طلب التنزيل لكن لم يُعثر على الملف الناتج.")
            filename = candidates[0]
        return filename
