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
        return "CONFIRM|" + sender + "|" + receiver + "|" + str(amount)

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
