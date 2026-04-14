from flask import Flask, request, jsonify
import sqlite3
import time

app = Flask(__name__)

conn = sqlite3.connect("m3.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    balance INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    sender TEXT,
    receiver TEXT,
    amount INTEGER,
    time INTEGER
)
""")

conn.commit()

def get_user():
    data = request.get_data(as_text=True).strip()
    if not data:
        return None
    return data

@app.route('/')
def home():
    return "M3 SERVER LIVE"

@app.route('/register', methods=['POST'])
def register():
    try:
        user = get_user()
        if not user:
            return "OK"

        cur.execute("SELECT id FROM users WHERE id=?", (user,))
        exists = cur.fetchone()

        if not exists:
            cur.execute("INSERT INTO users (id, balance) VALUES (?, ?)", (user, 1000))
            conn.commit()

        return "OK"
    except Exception as e:
        print("REGISTER ERROR:", e)
        return "OK"

@app.route('/balance', methods=['POST'])
def balance():
    try:
        user = get_user()
        if not user:
            return "0"

        cur.execute("SELECT balance FROM users WHERE id=?", (user,))
        result = cur.fetchone()

        if result:
            return str(result[0])

        return "0"
    except Exception as e:
        print("BALANCE ERROR:", e)
        return "0"

@app.route('/pay', methods=['POST'])
def pay():
    try:
        data = request.get_data(as_text=True).split("|")
        sender = data[0]
        receiver = data[1]
        amount = int(data[2])
    except:
        return "ERROR"

    try:
        cur.execute("SELECT balance FROM users WHERE id=?", (sender,))
        bal = cur.fetchone()

        if bal and bal[0] >= amount:
            cur.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, sender))
            cur.execute("INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0)", (receiver,))
            cur.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, receiver))

            cur.execute(
                "INSERT INTO transactions VALUES (?,?,?,?)",
                (sender, receiver, amount, int(time.time()))
            )

            conn.commit()
            return "SUCCESS"

        return "FAIL"
    except Exception as e:
        print("PAY ERROR:", e)
        return "ERROR"

@app.route('/stats', methods=['GET'])
def stats():
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT SUM(amount) FROM transactions")
    volume = cur.fetchone()[0] or 0

    return jsonify({"users": users, "volume": volume})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
