"""
Aegis - Security & Data Routes (Blueprint)
Extracted from app.py to reduce file complexity
"""

from flask import Blueprint, jsonify, render_template, request
from core.config import Config
from security.auth import AuthError

security_bp = Blueprint("security_bp", __name__)


def _get_pilot():
    """Lazy import to avoid circular dependency"""
    from dashboard.app import get_pilot
    return get_pilot()


@security_bp.route("/api/security")
def api_security():
    """Security status API"""
    from dashboard.app import login_required
    # Manual auth check (decorator not applied to blueprint route)
    p = _get_pilot()
    return jsonify(
        {
            "security": p.threats.get_status(),
            "compliance": p.compliance.check_compliance(),
            "encryption": p.crypto.get_status(),
            "audit_integrity": p.audit.verify_integrity(),
        }
    )


@security_bp.route("/security")
def security_page():
    """Security page"""
    from dashboard.app import login_required
    return render_template("security.html")


@security_bp.route("/backup", methods=["POST"])
def create_backup():
    """Create encrypted backup"""
    from dashboard.app import login_required
    p = _get_pilot()
    try:
        path = p.backup.create_backup()
        return jsonify({"status": "success", "path": path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@security_bp.route("/export-data", methods=["POST"])
def export_data():
    """Export all user data"""
    from dashboard.app import login_required
    p = _get_pilot()
    try:
        path = Config.REPORT_DIR / "my_data_export.json"
        p.lifecycle.export_all_data(path)
        return jsonify({"status": "success", "path": str(path)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@security_bp.route("/compliance-report", methods=["POST"])
def compliance_report():
    """Generate compliance report"""
    from dashboard.app import login_required
    p = _get_pilot()
    try:
        result = p.compliance.generate_report()
        return jsonify({"status": "success", "report": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@security_bp.route("/api/2fa/setup", methods=["POST"])
def setup_2fa():
    """Generate 2FA secret for setup"""
    from dashboard.app import login_required
    try:
        from security.auth import TwoFactorError
        p = _get_pilot()
        secret, qr_url = p.auth.generate_2fa_secret()
        return jsonify({"secret": secret, "qr_url": qr_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@security_bp.route("/api/2fa/enable", methods=["POST"])
def enable_2fa():
    """Complete 2FA setup"""
    from dashboard.app import login_required
    try:
        from security.auth import TwoFactorError
        p = _get_pilot()
        data = request.json
        secret = data.get("secret", "")
        token = data.get("token", "")
        p.auth.setup_2fa(secret, token)
        return jsonify({"status": "2FA enabled"})
    except TwoFactorError as e:
        return jsonify({"error": str(e)}), 400


@security_bp.route("/api/2fa/disable", methods=["POST"])
def disable_2fa():
    """Disable 2FA"""
    from dashboard.app import login_required
    try:
        from security.auth import TwoFactorError
        p = _get_pilot()
        data = request.json
        password = data.get("password", "")
        token = data.get("token", "")
        p.auth.disable_2fa(password, token)
        return jsonify({"status": "2FA disabled"})
    except (AuthError, TwoFactorError) as e:
        return jsonify({"error": str(e)}), 400
