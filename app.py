import os
import psycopg2
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

def get_db():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS keys (key_text TEXT PRIMARY KEY, hwid TEXT, expires_at TIMESTAMP)')
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/create_key', methods=['POST'])
def create_key():
    data = request.json
    key_text = data.get('คีย์')
    hours = data.get('ชั่วโมง')
    expires_at = datetime.now() + timedelta(hours=hours)
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO keys (key_text, hwid, expires_at) VALUES (%s, %s, %s)', (key_text, None, expires_at))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'สถานะ': 'สร้างคีย์สำเร็จ'})

@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    key_text = data.get('คีย์')
    hwid = data.get('รหัสเครื่อง')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT hwid, expires_at FROM keys WHERE key_text = %s', (key_text,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return jsonify({'สถานะ': 'ไม่พบคีย์ในระบบ'}), 404
        
    db_hwid, expires_at = row
    
    if type(expires_at) == str:
        expires_at = datetime.fromisoformat(expires_at)
        
    if datetime.now() > expires_at:
        return jsonify({'สถานะ': 'คีย์หมดอายุ'}), 403
        
    if db_hwid is None:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('UPDATE keys SET hwid = %s WHERE key_text = %s', (hwid, key_text))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'สถานะ': 'ใช้งานได้'})
        
    if db_hwid != hwid:
        return jsonify({'สถานะ': 'รหัสเครื่องไม่ตรงกัน'}), 403
        
    return jsonify({'สถานะ': 'ใช้งานได้'})

@app.route('/reset_hwid', methods=['POST'])
def reset_hwid():
    data = request.json
    key_text = data.get('คีย์')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE keys SET hwid = NULL WHERE key_text = %s', (key_text,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'สถานะ': 'รีเซ็ตรหัสเครื่องสำเร็จ'})

@app.route('/get_all_keys', methods=['GET'])
def get_all_keys():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT key_text, hwid, expires_at FROM keys')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    keys_list = []
    for row in rows:
        keys_list.append({
            'คีย์': row[0],
            'รหัสเครื่อง': row[1] if row[1] else 'ว่าง',
            'วันหมดอายุ': str(row[2])
        })
    return jsonify(keys_list)

@app.route('/delete_key', methods=['POST'])
def delete_key():
    data = request.json
    key_text = data.get('คีย์')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM keys WHERE key_text = %s', (key_text,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'สถานะ': 'ลบคีย์สำเร็จ'})

@app.route('/delete_expired_keys', methods=['POST'])
def delete_expired_keys():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM keys WHERE expires_at < NOW()')
    deleted_count = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'สถานะ': f'ลบคีย์ที่หมดอายุแล้วจำนวน {deleted_count} คีย์ สำเร็จ'})

@app.route('/admin_app')
def admin_app():
    return '''
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Mobile Admin Panel</title>
        <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #d81b60;
                --primary-gradient: linear-gradient(90deg, #ff2a6d, #b824ea);
                --success: #00e6b8;
                --danger: #ff4d4d;
                --warning: #ffb84d;
                --bg-dark: #09050e;
                --card-bg: #140a1b;
                --border-color: #3b1d47;
                --text-main: #ffffff;
                --text-muted: #a099a5;
            }

            * { box-sizing: border-box; font-family: 'Kanit', sans-serif; }
            body { 
                background: radial-gradient(circle at top, #2b153b, var(--bg-dark)); 
                background-attachment: fixed;
                margin: 0; 
                padding: 15px; 
                color: var(--text-main); 
            }
            
            .container { max-width: 800px; margin: auto; }
            .header { text-align: center; margin-bottom: 20px; }
            .header h2 {
                color: transparent;
                background: var(--primary-gradient);
                -webkit-background-clip: text;
                background-clip: text;
                text-shadow: 0 0 10px rgba(255, 42, 109, 0.3);
                font-weight: 600;
                letter-spacing: 1px;
            }
            
            .card { 
                background: var(--card-bg); 
                border-radius: 12px; 
                padding: 20px; 
                box-shadow: 0 4px 20px rgba(0,0,0,0.5); 
                border: 1px solid var(--border-color);
                margin-bottom: 20px; 
            }
            .input-group { display: flex; flex-direction: column; gap: 10px; }
            input { 
                padding: 12px; 
                border: 1px solid var(--border-color); 
                background: #0f0714;
                color: white;
                border-radius: 8px; 
                font-size: 16px; 
                outline: none; 
                transition: 0.3s;
            }
            input:focus { 
                border-color: #ff2a6d; 
                box-shadow: 0 0 10px rgba(255, 42, 109, 0.4);
            }
            input::placeholder { color: #6a5e72; }

            .btn { 
                padding: 12px; 
                border: 1px solid transparent; 
                border-radius: 8px; 
                font-weight: 500; 
                cursor: pointer; 
                font-size: 16px; 
                width: 100%; 
                transition: 0.3s; 
            }
            .btn-primary { 
                background: var(--primary-gradient);
                color: white; 
                border: none;
                box-shadow: 0 0 15px rgba(255, 42, 109, 0.4);
            }
            .btn-primary:hover { box-shadow: 0 0 25px rgba(255, 42, 109, 0.7); }
            
            .btn-success { background: rgba(0, 230, 184, 0.1); border-color: var(--success); color: var(--success); }
            .btn-success:hover { background: var(--success); color: black; box-shadow: 0 0 15px rgba(0, 230, 184, 0.4); }
            
            .btn-danger { background: rgba(255, 77, 77, 0.1); border-color: var(--danger); color: var(--danger); }
            .btn-danger:hover { background: var(--danger); color: white; box-shadow: 0 0 15px rgba(255, 77, 77, 0.4); }
            
            .btn-warning { background: rgba(255, 184, 77, 0.1); border-color: var(--warning); color: var(--warning); }
            .btn-warning:hover { background: var(--warning); color: black; box-shadow: 0 0 15px rgba(255, 184, 77, 0.4); }
            
            .btn:active { transform: scale(0.98); }

            .key-list { display: flex; flex-direction: column; gap: 15px; }
            .key-item { 
                background: var(--card-bg); 
                border-radius: 12px; 
                padding: 15px; 
                border: 1px solid var(--border-color);
                border-left: 5px solid var(--primary); 
                box-shadow: 0 4px 10px rgba(0,0,0,0.3); 
            }
            .key-info { margin-bottom: 12px; }
            .key-name { 
                font-weight: 600; 
                font-size: 18px; 
                color: #ff2a6d; 
                text-shadow: 0 0 8px rgba(255, 42, 109, 0.5);
            }
            .key-detail { font-size: 14px; color: var(--text-muted); margin: 4px 0; }
            .key-detail b { color: #d4c5db; }

            .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            .badge-expired { 
                background: rgba(255, 77, 77, 0.2); 
                color: var(--danger); 
                border: 1px solid var(--danger);
                box-shadow: 0 0 5px rgba(255, 77, 77, 0.3);
            }
            
            .action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
            .action-grid .btn { padding: 8px; font-size: 14px; }

            .refresh-area { display: flex; gap: 10px; margin-top: 20px; }

            @media (min-width: 600px) {
                .input-group { flex-direction: row; }
                .input-group input { flex: 2; }
                .input-group .btn { flex: 1; }
            }
        </style>
    </head>
    <body>

    <div class="container">
        <div class="header">
            <h2>ADMIN CONTROL PANEL</h2>
        </div>

        <div class="card">
            <div class="input-group">
                <input type="text" id="keyInput" placeholder="ชื่อคีย์ (Key Name)">
                <input type="number" id="hoursInput" placeholder="ชั่วโมง (Hours)">
                <button class="btn btn-primary" onclick="createKey()">สร้างคีย์</button>
            </div>
        </div>

        <div id="keyList" class="key-list">
        </div>

        <div class="refresh-area">
            <button class="btn btn-success" onclick="fetchKeys()">รีเฟรชข้อมูล</button>
            <button class="btn btn-danger" onclick="deleteExpiredKeys()">ลบคีย์หมดอายุ</button>
        </div>
    </div>

    <script>
        const SERVER_URL = "https://zerostore-oowt.onrender.com";

        function formatThaiTime(expireStr) {
            if (!expireStr) return "N/A";
            try {
                let dt = new Date(expireStr.replace(" ", "T") + "Z");
                return dt.toLocaleString('th-TH', { 
                    year: 'numeric', month: 'short', day: 'numeric',
                    hour: '2-digit', minute: '2-digit'
                });
            } catch (e) { return expireStr; }
        }

        async function fetchKeys() {
            const keyList = document.getElementById("keyList");
            keyList.innerHTML = "<p style='text-align:center; color: var(--text-muted);'>กำลังโหลดข้อมูล...</p>";
            
            try {
                const response = await fetch(`${SERVER_URL}/get_all_keys`);
                const data = await response.json();
                keyList.innerHTML = "";
                const now = new Date();

                data.forEach(item => {
                    const key = item["คีย์"];
                    const hwid = item["รหัสเครื่อง"] || "ว่าง";
                    const rawExpire = item["วันหมดอายุ"];
                    const expireFormatted = formatThaiTime(rawExpire);
                    
                    let isExpired = false;
                    if (rawExpire) {
                        let dt = new Date(rawExpire.replace(" ", "T") + "Z");
                        if (dt < now) isExpired = true;
                    }

                    const div = document.createElement("div");
                    div.className = "key-item";
                    div.style.borderLeftColor = isExpired ? "var(--danger)" : "#b824ea";
                    
                    div.innerHTML = `
                        <div class="key-info">
                            <div class="key-name" style="${isExpired ? 'color: var(--danger); text-shadow: 0 0 8px rgba(255,77,77,0.5);' : ''}">${key} ${isExpired ? '<span class="badge badge-expired">EXPIRED</span>' : ''}</div>
                            <div class="key-detail"><b>HWID:</b> ${hwid}</div>
                            <div class="key-detail"><b>Expires:</b> ${expireFormatted}</div>
                        </div>
                        <div class="action-grid">
                            <button class="btn btn-warning" onclick="resetHWID('${key}')">ล้างเครื่อง</button>
                            <button class="btn btn-danger" onclick="deleteKey('${key}')">ลบทิ้ง</button>
                        </div>
                    `;
                    keyList.appendChild(div);
                });
            } catch (error) {
                keyList.innerHTML = "<p style='color:var(--danger); text-align:center; font-weight:bold;'>เชื่อมต่อเซิร์ฟเวอร์ไม่ได้</p>";
            }
        }

        async function createKey() {
            const key = document.getElementById("keyInput").value;
            const hours = document.getElementById("hoursInput").value;
            if(!key || !hours) return alert("กรุณากรอกข้อมูล");
            
            try {
                const res = await fetch(`${SERVER_URL}/create_key`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ "คีย์": key, "ชั่วโมง": parseInt(hours) })
                });
                const result = await res.json();
                alert(result["สถานะ"]);
                fetchKeys();
            } catch (e) { alert("ล้มเหลว"); }
        }

        async function resetHWID(key) {
            if(!confirm(`ล้างเครื่องคีย์ ${key}?`)) return;
            await fetch(`${SERVER_URL}/reset_hwid`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ "คีย์": key })
            });
            fetchKeys();
        }

        async function deleteKey(key) {
            if(!confirm(`ลบคีย์ ${key}?`)) return;
            await fetch(`${SERVER_URL}/delete_key`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ "คีย์": key })
            });
            fetchKeys();
        }

        async function deleteExpiredKeys() {
            if(!confirm("ยืนยันที่จะลบคีย์ที่หมดอายุทั้งหมด?")) return;
            try {
                const res = await fetch(`${SERVER_URL}/delete_expired_keys`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                });
                const result = await res.json();
                alert(result["สถานะ"]);
                fetchKeys(); 
            } catch (e) { 
                alert("เกิดข้อผิดพลาดในการเชื่อมต่อ"); 
            }
        }

        window.onload = fetchKeys;
    </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
