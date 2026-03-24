import sqlite3
import random
import string
import datetime

def generate_key(days=0, hours=0):
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    
    expire = datetime.datetime.now() + datetime.timedelta(days=days, hours=hours)
    expire_str = expire.strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("keys.db")
    c = conn.cursor()
    c.execute("INSERT INTO licenses (key, expire_date, hwid, status) VALUES (?, ?, '', 'active')",
              (key, expire_str))
    conn.commit()
    conn.close()

    print("Key:", key)
    print("Expire:", expire_str)

# ตัวอย่าง
generate_key(days=7)      # 7 วัน
# generate_key(hours=12)  # 12 ชั่วโมง