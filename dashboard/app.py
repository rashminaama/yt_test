from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from config import config
from src import pipeline, storage

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        valid_user = username == config.DASHBOARD_USERNAME
        valid_password = bool(config.DASHBOARD_PASSWORD_HASH) and check_password_hash(
            config.DASHBOARD_PASSWORD_HASH, password
        )
        if valid_user and valid_password:
            session["logged_in"] = True
            return redirect(url_for("index"))
        flash("Invalid username or password")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    conn = storage.get_connection()
    try:
        videos = storage.get_recent_videos(conn)
    finally:
        conn.close()
    return render_template("index.html", videos=videos)


@app.route("/send-now", methods=["POST"])
@login_required
def send_now():
    try:
        result = pipeline.run_pipeline()
        if result["status"] == "skipped":
            flash("A pipeline run is already in progress — try again shortly.")
        else:
            flash(f"Sent! {result['video_count']} trending videos fetched and emailed.")
    except Exception as exc:
        flash(f"Send failed: {exc}")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
