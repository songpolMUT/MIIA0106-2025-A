import os
import psycopg2
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

def get_db():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS keys (key_text TEXT PRIMARY KEY, hwid TEXT, expires_at TIMESTAMP)")
    conn.commit()
    cur.close()
    conn.close()

@app.route("/create_key", methods=["POST"])
def create_key():
    data = request.json
    key_text = data.get("คีย์")
    hours = data.get("ชั่วโมง")
    expires_at = datetime.now() + timedelta(hours=hours)
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO keys (key_text, hwid, expires_at) VALUES (%s, %s, %s)", (key_text, None, expires_at))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"สถานะ": "สร้างคีย์สำเร็จ"})

@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    key_text = data.get("คีย์")
    hwid = data.get("รหัสเครื่อง")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT hwid, expires_at FROM keys WHERE key_text = %s", (key_text,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return jsonify({"สถานะ": "ไม่พบคีย์ในระบบ"}), 404
        
    db_hwid, expires_at = row
    
    if type(expires_at) == str:
        expires_at = datetime.fromisoformat(expires_at)
        
    if datetime.now() > expires_at:
        return jsonify({"สถานะ": "คีย์หมดอายุ"}), 403
        
    if db_hwid is None:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE keys SET hwid = %s WHERE key_text = %s", (hwid, key_text))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"สถานะ": "ใช้งานได้"})
        
    if db_hwid != hwid:
        return jsonify({"สถานะ": "รหัสเครื่องไม่ตรงกัน"}), 403
        
    return jsonify({"สถานะ": "ใช้งานได้"})

@app.route("/reset_hwid", methods=["POST"])
def reset_hwid():
    data = request.json
    key_text = data.get("คีย์")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE keys SET hwid = NULL WHERE key_text = %s", (key_text,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"สถานะ": "รีเซ็ตรหัสเครื่องสำเร็จ"})

@app.route("/get_all_keys", methods=["GET"])
def get_all_keys():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT key_text, hwid, expires_at FROM keys")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    keys_list = []
    for row in rows:
        keys_list.append({
            "คีย์": row[0],
            "รหัสเครื่อง": row[1] if row[1] else "ว่าง",
            "วันหมดอายุ": str(row[2])
        })
    return jsonify(keys_list)

@app.route("/delete_key", methods=["POST"])
def delete_key():
    data = request.json
    key_text = data.get("คีย์")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM keys WHERE key_text = %s", (key_text,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"สถานะ": "ลบคีย์สำเร็จ"})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)