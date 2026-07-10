"""
Aegis - Settings & Models Routes (Blueprint)
Extracted from app.py to reduce file complexity
"""

import os
import re
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request
from core.config import Config

settings_bp = Blueprint("settings_bp", __name__)


def _get_pilot():
    """Lazy import to avoid circular dependency"""
    from dashboard.app import get_pilot
    return get_pilot()


@settings_bp.route("/api/metrics")
def api_metrics():
    """Prometheus-compatible metrics endpoint"""
    from dashboard.app import login_required
    try:
        from core.metrics import get_metrics
        metrics = get_metrics()
        return metrics.get_prometheus_output(), 200, {"Content-Type": "text/plain; charset=utf-8"}
    except ImportError:
        return jsonify({"error": "Metrics not available"}), 503


@settings_bp.route("/api/metrics/json")
def api_metrics_json():
    """Metrics as JSON"""
    from dashboard.app import login_required
    try:
        from core.metrics import get_metrics
        metrics = get_metrics()
        return jsonify(metrics.to_dict())
    except ImportError:
        return jsonify({"error": "Metrics not available"}), 503


@settings_bp.route("/settings")
def settings():
    """Settings page"""
    from dashboard.app import login_required
    p = _get_pilot()
    backups = p.backup.list_backups()

    available_models = []
    current_model = Config.OLLAMA_MODEL
    try:
        import requests
        r = requests.get(f"{Config.OLLAMA_HOST}/api/tags", timeout=5)
        if r.status_code == 200:
            data = r.json()
            available_models = [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        pass

    watch_folders = []
    env_path = Config.BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if line.strip().startswith("WATCH_FOLDERS="):
                    value = line.split("=", 1)[1].strip()
                    if value:
                        watch_folders = [f.strip() for f in value.split(",") if f.strip()]
                    break

    return render_template(
        "settings.html",
        backups=backups,
        available_models=available_models,
        current_model=current_model,
        watch_folders=watch_folders,
    )


@settings_bp.route("/settings/add-watch-folder", methods=["POST"])
def add_watch_folder():
    """Add a folder to the watch list"""
    from dashboard.app import login_required
    data = request.get_json()
    folder_path = data.get("path", "").strip()

    if not folder_path:
        return jsonify({"status": "error", "message": "Path cannot be empty"})

    folder_path = os.path.expanduser(folder_path)

    if not os.path.exists(folder_path):
        return jsonify({"status": "error", "message": "Folder does not exist"})

    if not os.path.isdir(folder_path):
        return jsonify({"status": "error", "message": "Path is not a directory"})

    env_path = Config.BASE_DIR / ".env"
    if not env_path.exists():
        return jsonify({"status": "error", "message": ".env file not found"})

    with open(env_path, "r") as f:
        lines = f.readlines()

    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("WATCH_FOLDERS="):
            existing = line.split("=", 1)[1].strip()
            if existing:
                folders = [f.strip() for f in existing.split(",")]
                normalized = str(Path(folder_path).resolve())
                if normalized not in [str(Path(f).resolve()) for f in folders]:
                    folders.append(folder_path)
                    line = "WATCH_FOLDERS=" + ",".join(folders) + "\n"
                else:
                    return jsonify({"status": "error", "message": "Folder already in watch list"})
            else:
                line = f"WATCH_FOLDERS={folder_path}\n"
            found = True
        new_lines.append(line)

    if not found:
        new_lines.append(f"WATCH_FOLDERS={folder_path}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)

    return jsonify({"status": "success", "message": "Folder added to watch list"})


@settings_bp.route("/api/models", methods=["GET"])
def api_get_models():
    """Get available Ollama models"""
    from dashboard.app import login_required
    import requests
    try:
        r = requests.get(f"{Config.OLLAMA_HOST}/api/tags", timeout=10)
        if r.status_code == 200:
            data = r.json()
            models = [
                {"name": m.get("name", ""), "size": m.get("size", 0)}
                for m in data.get("models", [])
            ]
            return jsonify({"status": "success", "models": models, "current": Config.OLLAMA_MODEL})
        return jsonify({"status": "error", "message": "Failed to fetch models"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@settings_bp.route("/api/models/pull", methods=["POST"])
def api_pull_model():
    """Pull a new Ollama model"""
    from dashboard.app import login_required
    import requests
    data = request.json
    model_name = data.get("model", "").strip()

    if not model_name:
        return jsonify({"status": "error", "message": "Model name required"})

    try:
        r = requests.post(f"{Config.OLLAMA_HOST}/api/pull", json={"name": model_name}, timeout=300)
        if r.status_code == 200:
            return jsonify({"status": "success", "message": f"Model '{model_name}' pulled successfully"})
        return jsonify({"status": "error", "message": "Failed to pull model"})
    except requests.exceptions.Timeout:
        return jsonify({"status": "error", "message": "Model pull timed out"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@settings_bp.route("/api/models/set", methods=["POST"])
def api_set_model():
    """Set the active Ollama model"""
    from dashboard.app import login_required
    data = request.json
    model_name = data.get("model", "").strip()

    if not model_name:
        return jsonify({"status": "error", "message": "Model name required"})

    env_path = Config.BASE_DIR / ".env"
    env_content = env_path.read_text() if env_path.exists() else ""

    if "OLLAMA_MODEL=" in env_content:
        env_content = re.sub(r"OLLAMA_MODEL=.*", f"OLLAMA_MODEL={model_name}", env_content)
    else:
        env_content += f"\nOLLAMA_MODEL={model_name}\n"

    env_path.write_text(env_content)

    return jsonify({"status": "success", "message": f"Model set to '{model_name}'"})
