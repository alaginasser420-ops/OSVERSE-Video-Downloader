from __future__ import annotations

import os
import threading
import uuid
from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file, abort
from downloader import inspect_video, download_video, validate_public_url

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024
app.config["JSON_SORT_KEYS"] = False

_tasks = {}
_tasks_lock = threading.Lock()


def update_task(task_id, **kwargs):
    with _tasks_lock:
        if task_id in _tasks:
            _tasks[task_id].update(kwargs)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/info")
def api_info():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    try:
        validate_public_url(url)
        info = inspect_video(url)
        return jsonify({
            "ok": True,
            "title": info.get("title") or "Untitled video",
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader") or info.get("channel") or "",
            "formats": [
                {"id": "best", "label": "أفضل جودة متاحة"},
                {"id": "1080", "label": "1080p (إن توفرت)"},
                {"id": "720", "label": "720p (إن توفرت)"},
                {"id": "480", "label": "480p (إن توفرت)"},
                {"id": "360", "label": "360p (إن توفرت)"},
                {"id": "audio", "label": "صوت MP3"}
            ]
        })
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/download")
def api_download():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    quality = (data.get("quality") or "best").strip()
    if quality not in {"best", "1080", "720", "480", "360", "audio"}:
        return jsonify({"ok": False, "error": "خيار الجودة غير صالح."}), 400
    try:
        validate_public_url(url)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    task_id = uuid.uuid4().hex
    with _tasks_lock:
        _tasks[task_id] = {
            "status": "queued", "progress": 0, "message": "تمت إضافة التنزيل إلى قائمة الانتظار",
            "filename": None, "error": None
        }

    def worker():
        update_task(task_id, status="downloading", message="جارٍ تجهيز التنزيل...")
        try:
            def hook(payload):
                status = payload.get("status")
                if status == "downloading":
                    total = payload.get("total_bytes") or payload.get("total_bytes_estimate")
                    done = payload.get("downloaded_bytes", 0)
                    pct = round(done * 100 / total, 1) if total else 0
                    update_task(task_id, progress=min(pct, 99), message="جارٍ تنزيل الفيديو...")
                elif status == "finished":
                    update_task(task_id, progress=99, message="اكتمل التنزيل، جارٍ تجهيز الملف...")

            output = download_video(url, quality, DOWNLOAD_DIR, hook)
            update_task(task_id, status="done", progress=100, message="اكتمل التنزيل",
                        filename=output.name)
        except Exception as exc:
            update_task(task_id, status="error", error=str(exc), message="تعذر إكمال التنزيل")

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok": True, "task_id": task_id})


@app.get("/api/tasks/<task_id>")
def api_task(task_id):
    with _tasks_lock:
        task = _tasks.get(task_id)
    if not task:
        return jsonify({"ok": False, "error": "مهمة التنزيل غير موجودة."}), 404
    result = dict(task)
    if result.get("status") == "done" and result.get("filename"):
        result["download_url"] = f"/api/files/{task_id}"
    return jsonify(result)


@app.get("/api/files/<task_id>")
def api_file(task_id):
    with _tasks_lock:
        task = _tasks.get(task_id)
    if not task or task.get("status") != "done" or not task.get("filename"):
        abort(404)
    path = (DOWNLOAD_DIR / task["filename"]).resolve()
    if path.parent != DOWNLOAD_DIR.resolve() or not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True, download_name=path.name)


if __name__ == "__main__":
    # Local-only by default: do not change to 0.0.0.0 unless you add authentication
    # and deploy behind a properly secured production server.
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
