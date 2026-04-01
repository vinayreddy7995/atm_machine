from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
#  DATA  (replace with a real database later)
# ─────────────────────────────────────────────
accounts = {
    "1234": {
        "pin": "5678",
        "name": "Arjun Sharma",
        "balance": 24850.50,
        "transactions": [
            {"desc": "UPI Credit",      "amount":  5000,  "type": "credit", "date": "28 Mar"},
            {"desc": "Amazon Pay",       "amount": -1299,  "type": "debit",  "date": "27 Mar"},
            {"desc": "Salary",           "amount": 45000,  "type": "credit", "date": "25 Mar"},
            {"desc": "Swiggy",           "amount":  -450,  "type": "debit",  "date": "24 Mar"},
            {"desc": "ATM Withdrawal",   "amount": -2000,  "type": "debit",  "date": "22 Mar"},
        ],
    },
    "5678": {
        "pin": "1234",
        "name": "Priya Nair",
        "balance": 8200.00,
        "transactions": [
            {"desc": "Rent Paid",        "amount": -8000,  "type": "debit",  "date": "01 Mar"},
            {"desc": "Freelance Credit", "amount": 12000,  "type": "credit", "date": "15 Mar"},
        ],
    },
}

pin_attempts = {}   # card_number -> attempt count

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def today():
    return datetime.now().strftime("%d %b")


# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/insert_card", methods=["POST"])
def insert_card():
    data = request.json
    card = data.get("card_number", "")
    if card in accounts:
        return jsonify({"success": True, "message": "Card accepted"})
    return jsonify({"success": False, "message": "Card not found. Try: 1234 or 5678"})


@app.route("/api/verify_pin", methods=["POST"])
def verify_pin():
    data = request.json
    card = data.get("card_number", "")
    pin  = data.get("pin", "")

    attempts = pin_attempts.get(card, 0)
    if attempts >= 3:
        return jsonify({"success": False, "blocked": True, "message": "Card blocked"})

    if card not in accounts:
        return jsonify({"success": False, "message": "Card not found"})

    if accounts[card]["pin"] == pin:
        pin_attempts[card] = 0
        acc = accounts[card]
        return jsonify({
            "success": True,
            "name":    acc["name"],
            "balance": acc["balance"],
        })
    else:
        pin_attempts[card] = attempts + 1
        left = 3 - pin_attempts[card]
        blocked = left <= 0
        return jsonify({
            "success": False,
            "blocked": blocked,
            "message": f"Wrong PIN. {left} attempt(s) remaining.",
        })


@app.route("/api/balance", methods=["POST"])
def balance():
    data = request.json
    card = data.get("card_number", "")
    if card not in accounts:
        return jsonify({"success": False, "message": "Not authenticated"})
    return jsonify({"success": True, "balance": accounts[card]["balance"]})


@app.route("/api/withdraw", methods=["POST"])
def withdraw():
    data   = request.json
    card   = data.get("card_number", "")
    amount = float(data.get("amount", 0))

    if card not in accounts:
        return jsonify({"success": False, "message": "Not authenticated"})
    if amount <= 0:
        return jsonify({"success": False, "message": "Invalid amount"})
    if amount > accounts[card]["balance"]:
        return jsonify({"success": False, "message": "Insufficient funds"})

    accounts[card]["balance"] -= amount
    accounts[card]["transactions"].insert(0, {
        "desc":   "ATM Withdrawal",
        "amount": -amount,
        "type":   "debit",
        "date":   today(),
    })
    return jsonify({"success": True, "new_balance": accounts[card]["balance"]})


@app.route("/api/deposit", methods=["POST"])
def deposit():
    data   = request.json
    card   = data.get("card_number", "")
    amount = float(data.get("amount", 0))

    if card not in accounts:
        return jsonify({"success": False, "message": "Not authenticated"})
    if amount <= 0:
        return jsonify({"success": False, "message": "Invalid amount"})

    accounts[card]["balance"] += amount
    accounts[card]["transactions"].insert(0, {
        "desc":   "ATM Deposit",
        "amount": amount,
        "type":   "credit",
        "date":   today(),
    })
    return jsonify({"success": True, "new_balance": accounts[card]["balance"]})


@app.route("/api/mini_statement", methods=["POST"])
def mini_statement():
    data = request.json
    card = data.get("card_number", "")
    if card not in accounts:
        return jsonify({"success": False, "message": "Not authenticated"})
    return jsonify({"success": True, "transactions": accounts[card]["transactions"][:5]})


@app.route("/api/change_pin", methods=["POST"])
def change_pin():
    data    = request.json
    card    = data.get("card_number", "")
    old_pin = data.get("old_pin", "")
    new_pin = data.get("new_pin", "")

    if card not in accounts:
        return jsonify({"success": False, "message": "Not authenticated"})
    if accounts[card]["pin"] != old_pin:
        return jsonify({"success": False, "message": "Current PIN is incorrect"})
    if len(new_pin) != 4 or not new_pin.isdigit():
        return jsonify({"success": False, "message": "PIN must be exactly 4 digits"})

    accounts[card]["pin"] = new_pin
    return jsonify({"success": True, "message": "PIN changed successfully"})


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n╔══════════════════════════════╗")
    print("║   SBI Bank ATM  —  v1.0    ║")
    print("╠══════════════════════════════╣")
    print("║  Open: http://127.0.0.1:5000 ║")
    print("║  Test cards:                 ║")
    print("║    Card 1234  PIN 5678       ║")
    print("║    Card 5678  PIN 1234       ║")
    print("╚══════════════════════════════╝\n")
    app.run(debug=True)