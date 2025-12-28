from flask import session, redirect, url_for
from config import ADMIN_USERNAME

def is_admin():
    return session.get("admin") == ADMIN_USERNAME

def admin_required():
    if not is_admin():
        return redirect(url_for("admin_login"))
