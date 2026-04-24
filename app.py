from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "secret123"
socketio = SocketIO(app)

# =========================
# DATABASE INIT (SAFE)
# =========================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        profile_pic TEXT DEFAULT 'default.png'
    )
    """)

    # MESSAGES (STABLE STRUCTURE)
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT,
        image TEXT,
        audio TEXT,
        timestamp TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# ONLINE USERS
# =========================
online_users = set()


# =========================
# AUTH
# =========================
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        file = request.files.get("profile_pic")
        pic = "default.png"

        if file and file.filename != "":
            pic = file.filename
            file.save("static/" + pic)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("""
        INSERT INTO users (username, password, profile_pic)
        VALUES (?, ?, ?)
        """, (username, password, pic))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                  (username, password))
        user = c.fetchone()

        conn.close()

        if user:
            session["user"] = username

            # ✅ IMPORTANT: redirect to dashboard
            return redirect("/dashboard")

        return "❌ Wrong username or password"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users")
    users = c.fetchall()

    conn.close()

    return render_template("dashboard.html", users=users)


# =========================
# CHAT PAGE
# =========================
@app.route("/chat/<user>", methods=["GET", "POST"])
def chat(user):
    if "user" not in session:
        return redirect("/login")

    sender = session["user"]
    receiver = user

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # SEND MESSAGE (TEXT + IMAGE)
    if request.method == "POST":
        message = request.form.get("message")

        image_file = request.files.get("image")
        image_name = None

        if image_file and image_file.filename != "":
            os.makedirs("static/uploads", exist_ok=True)
            image_name = image_file.filename
            image_file.save("static/uploads/" + image_name)

        time = datetime.now().strftime("%Y-%m-%d %H:%M")

        c.execute("""
        INSERT INTO messages (sender, receiver, message, image, audio, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (sender, receiver, message, image_name, None, time, "sent"))

        conn.commit()

    # LOAD CHAT
    c.execute("""
    SELECT * FROM messages
    WHERE (sender=? AND receiver=?)
    OR (sender=? AND receiver=?)
    ORDER BY id ASC
    """, (sender, receiver, receiver, sender))

    messages = c.fetchall()

    conn.close()

    return render_template("chat.html", messages=messages, user=receiver)


# =========================
# SOCKET EVENTS
# =========================
@socketio.on("user_online")
def user_online(data):
    online_users.add(data["username"])
    emit("update_users", list(online_users), broadcast=True)


@socketio.on("send_message")
def send_message(data):
    emit("receive_message", data, broadcast=True)


@socketio.on("typing")
def typing(data):
    emit("typing", data, broadcast=True)


@socketio.on("stop_typing")
def stop_typing(data):
    emit("stop_typing", data, broadcast=True)


# =========================
# RUN
# =========================
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)