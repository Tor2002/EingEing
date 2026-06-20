from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from datetime import datetime
import json, os, uuid

app = Flask(__name__)
app.secret_key = "eingeing_secret_2024"
ADMIN_PASSWORD = "889565"
DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "images")
PROMPTPAY_ID = "1529900725119"
ACCOUNT_NAME = "ณฐมน"
song_requests = []

def load(name):
    with open(os.path.join(DATA_DIR, f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)

def save(name, data):
    with open(os.path.join(DATA_DIR, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def next_id(lst):
    return max((x.get("id",0) for x in lst), default=0) + 1

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

# PUBLIC
@app.route("/")
def home():
    return render_template("home.html", active="home", schedule=load("schedule"))

@app.route("/videos")
def videos():
    return render_template("videos.html", videos=load("videos"), active="videos")

@app.route("/songs")
def songs():
    return render_template("songs.html", songs=load("songs"), active="songs")

@app.route("/request")
def song_request_page():
    return render_template("request.html", active="request")

@app.route("/tip")
def tip():
    return render_template("tip.html", account_name=ACCOUNT_NAME, promptpay_id=PROMPTPAY_ID, active="tip")

@app.route("/api/request", methods=["POST"])
def api_request():
    d = request.get_json()
    name = d.get("name","").strip(); song = d.get("song","").strip()
    if not name or not song:
        return jsonify({"ok":False,"error":"กรุณากรอกชื่อและชื่อเพลง"}), 400
    song_requests.append({"name":name,"song":song,"artist":d.get("artist","").strip(),
        "tip":d.get("tip","").strip(),"message":d.get("message","").strip(),
        "time":datetime.now().strftime("%d/%m/%Y %H:%M")})
    return jsonify({"ok":True})

# ADMIN AUTH
@app.route("/admin", methods=["GET","POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        if request.form.get("password","") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        error = "รหัสผ่านไม่ถูกต้อง"
    return render_template("admin_login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# ADMIN DASHBOARD
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    return render_template("admin_dashboard.html", requests=song_requests, active="dashboard")

@app.route("/admin/clear", methods=["POST"])
@login_required
def admin_clear():
    song_requests.clear()
    return redirect(url_for("admin_dashboard"))

# ADMIN SONGS
@app.route("/admin/songs")
@login_required
def admin_songs():
    return render_template("admin_songs.html", songs=load("songs"), active="songs")

@app.route("/admin/songs/add", methods=["POST"])
@login_required
def admin_songs_add():
    songs = load("songs")
    songs.append({"id":next_id(songs),"title":request.form["title"].strip(),
        "artist":request.form["artist"].strip(),"era":request.form["era"]})
    save("songs", songs)
    return redirect(url_for("admin_songs"))

@app.route("/admin/songs/edit/<int:sid>", methods=["POST"])
@login_required
def admin_songs_edit(sid):
    songs = load("songs")
    for s in songs:
        if s["id"] == sid:
            s["title"]=request.form["title"].strip()
            s["artist"]=request.form["artist"].strip()
            s["era"]=request.form["era"]
            break
    save("songs", songs)
    return redirect(url_for("admin_songs"))

@app.route("/admin/songs/delete/<int:sid>", methods=["POST"])
@login_required
def admin_songs_delete(sid):
    save("songs", [s for s in load("songs") if s["id"]!=sid])
    return redirect(url_for("admin_songs"))

# ADMIN SCHEDULE
@app.route("/admin/schedule")
@login_required
def admin_schedule():
    return render_template("admin_schedule.html", schedule=load("schedule"), active="schedule")

@app.route("/admin/schedule/save", methods=["POST"])
@login_required
def admin_schedule_save():
    days = ["mon","tue","wed","thu","fri","sat","sun"]
    schedule = {}
    for day in days:
        venues   = request.form.getlist(f"{day}_venue")
        times    = request.form.getlist(f"{day}_time")
        statuses = request.form.getlist(f"{day}_status")
        schedule[day] = [{"venue":v.strip(),"time":t.strip(),"status":s}
            for v,t,s in zip(venues,times,statuses) if v.strip()]
    save("schedule", schedule)
    return redirect(url_for("admin_schedule"))

# ADMIN VIDEOS
@app.route("/admin/videos")
@login_required
def admin_videos():
    return render_template("admin_videos.html", videos=load("videos"), active="videos")

@app.route("/admin/videos/add", methods=["POST"])
@login_required
def admin_videos_add():
    videos = load("videos")
    thumb = "video_default.jpg"
    file = request.files.get("thumb_file")
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        fname = f"video_{uuid.uuid4().hex[:8]}{ext}"
        file.save(os.path.join(UPLOAD_DIR, fname))
        thumb = fname
    videos.append({"id":next_id(videos),"thumb":thumb,
        "title":request.form.get("title","").strip(),
        "venue":request.form.get("venue","").strip(),
        "date":request.form.get("date","").strip(),
        "url":request.form.get("url","").strip(),
        "color":"linear-gradient(135deg,#FDDDE6,#F9C4A8)"})
    save("videos", videos)
    return redirect(url_for("admin_videos"))

@app.route("/admin/videos/edit/<int:vid>", methods=["POST"])
@login_required
def admin_videos_edit(vid):
    videos = load("videos")
    for v in videos:
        if v["id"] == vid:
            v["title"]=request.form.get("title","").strip()
            v["venue"]=request.form.get("venue","").strip()
            v["date"]=request.form.get("date","").strip()
            v["url"]=request.form.get("url","").strip()
            file = request.files.get("thumb_file")
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1].lower()
                fname = f"video_{uuid.uuid4().hex[:8]}{ext}"
                file.save(os.path.join(UPLOAD_DIR, fname))
                v["thumb"] = fname
            break
    save("videos", videos)
    return redirect(url_for("admin_videos"))

@app.route("/admin/videos/delete/<int:vid>", methods=["POST"])
@login_required
def admin_videos_delete(vid):
    save("videos", [v for v in load("videos") if v["id"]!=vid])
    return redirect(url_for("admin_videos"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
