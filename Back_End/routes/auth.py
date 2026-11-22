import json
import secrets
import urllib.error
import urllib.parse
import urllib.request

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import config
from Back_End import service

auth_bp = Blueprint("auth", __name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


# ---- the only two functions that talk to Google (the tests replace them) ----

def _post_form(url, data):
    body = urllib.parse.urlencode(data).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=10) as response:
        return json.load(response)


def _get_json(url, token):
    headers = {"Authorization": "Bearer " + token}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10) as response:
        return json.load(response)


# ---- pages ----

@auth_bp.route("/login")
def login():
    if session.get("student"):
        return redirect(url_for("customer.shops"))
    return render_template("costumer/login.html", google_ready=config.GOOGLE_ENABLED,
                           demo_mode=config.DEMO_LOGIN, domain=config.ALLOWED_EMAIL_DOMAIN)


@auth_bp.route("/logout")
def logout():
    session.pop("student", None)
    return redirect(url_for("auth.login"))


def _finish_login(email):
    """Shared by Google sign-in and demo sign-in: check the domain, then log in."""
    try:
        email = service.check_student_email(email)
    except ValueError as error:
        flash(str(error))
        return redirect(url_for("auth.login"))
    session["student"] = email
    return redirect(url_for("customer.shops"))


# ---- sign in with Google (OAuth 2.0 authorization code flow) ----

def _redirect_uri():
    return config.GOOGLE_REDIRECT_URI or url_for("auth.google_callback", _external=True)


@auth_bp.route("/auth/google")
def google_start():
    if not config.GOOGLE_ENABLED:
        flash("Google sign-in is not set up on this server")
        return redirect(url_for("auth.login"))
    state = secrets.token_urlsafe(24)                  # protects against forged callbacks
    session["oauth_state"] = state
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": "openid email",
        "state": state,
        "prompt": "select_account",
        "hd": config.ALLOWED_EMAIL_DOMAIN,             # only a hint; we check the domain ourselves
    }
    return redirect(GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params))


@auth_bp.route("/auth/google/callback")
def google_callback():
    expected = session.pop("oauth_state", None)
    given = request.args.get("state", "")
    if (not config.GOOGLE_ENABLED or request.args.get("error") or not expected
            or not secrets.compare_digest(given, expected)):
        flash("Google sign-in was cancelled or could not be verified. Please try again")
        return redirect(url_for("auth.login"))
    try:
        token = _post_form(GOOGLE_TOKEN_URL, {
            "code": request.args.get("code", ""),
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": _redirect_uri(),
            "grant_type": "authorization_code",
        })
        info = _get_json(GOOGLE_USERINFO_URL, token["access_token"])
    except (OSError, KeyError, ValueError):            # no internet, bad reply, bad code
        flash("Could not sign in with Google. Please try again")
        return redirect(url_for("auth.login"))
    if not info.get("email_verified"):
        flash("Your Google email is not verified")
        return redirect(url_for("auth.login"))
    return _finish_login(info.get("email", ""))


# ---- demo sign-in (only when Google is not set up, or QUICKSERVE_DEMO_LOGIN=1) ----

@auth_bp.route("/auth/demo", methods=["POST"])
def demo_login():
    if not config.DEMO_LOGIN:
        flash("Demo sign-in is turned off")
        return redirect(url_for("auth.login"))
    return _finish_login(request.form.get("email", ""))
