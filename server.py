from flask import Flask, request, jsonify
import sqlite3
import datetime

app = Flask(__name__)

def check_key(key, hwid):
    conn = sqlite3.connect("keys.db")
    c = conn.cursor()

    c.execute("SELECT expiry_date, hwid, status FROM licenses WHERE key=?", (key,))
    result = c.fetchone()

    if not result:
        return "invalid"

    expiry_date, saved_hwid, status = result

    if status != "active":
        return "banned"

    # เช็คหมดอายุ
    if datetime.date.today() > datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date():
        return "expired"

    # ล็อก HWID
    if saved_hwid == "":
        c.execute("UPDATE licenses SET hwid=? WHERE key=?", (hwid, key))
        conn.commit()
    elif saved_hwid != hwid:
        return "used"

    return "ok"

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    status = check_key(key, hwid)
    return jsonify({"status": status})

@app.route("/")
def home():
    return "License Server Running"

app.run(host="0.0.0.0", port=10000)