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
    except:
        return "OK"

@app.route('/balance', methods=['POST'])
def balance():
    try:
        user = get_user()
        cur.execute("SELECT balance FROM users WHERE id=?", (user,))
        result = cur.fetchone()
        return str(result[0]) if result else "0"
    except:
        return "0"

@app.route('/deposit', methods=['POST'])
def deposit():
    try:
        data = request.get_data(as_text=True).split("|")
        user = data[0]
        amount = int(data[1])

        cur.execute("INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0)", (user,))
        cur.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user))

        cur.execute(
            "INSERT INTO transactions VALUES (?,?,?,?)",
            ("BANK", user, amount, int(time.time()))
        )

        conn.commit()
        return "DEPOSIT_SUCCESS"
    except:
        return "ERROR"

@app.route('/withdraw', methods=['POST'])
def withdraw():
    try:
        data = request.get_data(as_text=True).split("|")
        user = data[0]
        amount = int(data[1])

        cur.execute("SELECT balance FROM users WHERE id=?", (user,))
        bal = cur.fetchone()

        if not bal:
            return "USER_NOT_FOUND"

        if bal[0] < amount:
            return "INSUFFICIENT_FUNDS"

        cur.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, user))

        cur.execute(
            "INSERT INTO transactions VALUES (?,?,?,?)",
            (user, "BANK", amount, int(time.time()))
        )

        conn.commit()
        return "WITHDRAW_SUCCESS"
    except:
        return "ERROR"

@app.route('/pay', methods=['POST'])
def pay():
    try:
        data = request.get_data(as_text=True).split("|")
        sender = data[0]
        receiver = data[1]
        amount = int(data[2])
        confirm = data[3] if len(data) > 3 else "no"
    except:
        return "ERROR"

    if confirm != "yes":
        return f"CONFIRM|{sender}|{receiver}|{amount}"

    try:
        cur.execute("SELECT balance FROM users WHERE id=?", (sender,))
        bal = cur.fetchone()

        if not bal:
            return "USER_NOT_FOUND"

        if bal[0] < amount:
            return "INSUFFICIENT_FUNDS"

        cur.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, sender))
        cur.execute("INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0)", (receiver,))
        cur.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, receiver))

        cur.execute(
            "INSERT INTO transactions VALUES (?,?,?,?)",
            (sender, receiver, amount, int(time.time()))
        )

        conn.commit()
        return "SUCCESS"
    except:
        return "ERROR"

@app.route('/history', methods=['POST'])
def history():
    try:
        user = request.get_data(as_text=True).strip()

        cur.execute("""
        SELECT sender, receiver, amount, time
        FROM transactions
        WHERE sender=? OR receiver=?
        ORDER BY time DESC
        LIMIT 10
        """, (user, user))

        rows = cur.fetchall()

        if not rows:
            return "NONE"

        return "\n".join([f"{r[0]}->{r[1]}:{r[2]}:{r[3]}" for r in rows])
    except:
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
