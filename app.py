from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client, Client
from flask_mail import Mail, Message

import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ---------------- AI CONFIG ----------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT = """
You are an intelligent, polite, and helpful AI chatbot designed specifically
to assist users with information related to Shri Rawatpura Sarkar University (SRU), Raipur.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT
)

# ---------------- SUPABASE CONFIG ----------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- ADMIN CONFIG ----------------
ADMIN_USERNAME = "Admin"
ADMIN_PASSWORD = "admin@123"
ADMIN_EMAIL = "ghanshyamdewangan1472@gmail.com"

# ---------------- FLASK APP ----------------
app = Flask(__name__)
CORS(app, supports_credentials=True)

# ---------------- MAIL CONFIG ----------------
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = "Transaction System"

mail = Mail(app)

# ---------------- SEND ADMIN EMAIL ----------------
def send_admin_email(tx):
    approve_url = f"http://127.0.0.1:5000/email-approve/{tx['id']}"
    reject_url = f"http://127.0.0.1:5000/email-reject/{tx['id']}"

    msg = Message(
        subject="New Transaction Approval Required",
        recipients=[ADMIN_EMAIL],
        html=f"""
        <h2>New Transaction Pending</h2>
        <p><b>Transaction ID:</b> {tx['transaction_id']}</p>
        <p><b>Requester:</b> {tx['requester']}</p>
        <p><b>Payee:</b> {tx['payee']}</p>
        <p><b>Amount:</b> ₹ {tx['amount']}</p>
        <br>
        <a href="{approve_url}">Approve</a> |
        <a href="{reject_url}">Reject</a>
        """
    )
    mail.send(msg)

# ---------------- AI CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please ask something."}), 400

    try:
        response = model.generate_content(
            user_message,
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 1024
            }
        )
        return jsonify({"reply": response.text})

    except Exception as e:
        print("GEMINI ERROR:", e)
        return jsonify({"reply": "AI service is temporarily unavailable."}), 500

# ---------------- STATIC FILES ----------------
@app.route("/<path:filename>")
def serve_html(filename):
    if filename.endswith(".html"):
        return send_from_directory(".", filename)
    return jsonify({"error": "Not Found"}), 404

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "").lower().strip()

    if role == "admin":
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return jsonify({"success": True, "role": "admin"})
        return jsonify({"success": False}), 401

    result = supabase.table("users") \
        .select("id") \
        .eq("username", username) \
        .eq("password", password) \
        .execute()

    return jsonify({"success": bool(result.data), "role": "user"}) if result.data else jsonify({"success": False}), 401

# ---------------- NEXT TRANSACTION ID ----------------
@app.route("/next-transaction-id/<username>")
def next_tid(username):
    result = supabase.table("transactions") \
        .select("transaction_id") \
        .eq("requester", username) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    next_no = int(result.data[0]["transaction_id"].split("-")[1]) + 1 if result.data else 1
    return jsonify({"next_id": f"TID-{str(next_no).zfill(3)}"})

# ---------------- ADD TRANSACTION ----------------
@app.route("/add-transaction", methods=["POST"])
def add_transaction():
    data = request.json or {}

    required = ["transaction_id", "date", "time", "requester", "amount", "amount_words"]
    for field in required:
        if not data.get(field):
            return jsonify({"success": False, "message": f"Missing field: {field}"}), 400

    payload = {
        "transaction_id": data["transaction_id"],
        "transaction_date": data["date"],
        "transaction_time": data["time"],
        "requester": data["requester"],
        "payee": data.get("payee", "-"),
        "amount": data["amount"],
        "amount_words": data["amount_words"],
        "status": "Pending"
    }

    result = supabase.table("transactions").insert(payload).execute()

    if not result.data:
        return jsonify({"success": False}), 500

    send_admin_email(result.data[0])
    return jsonify({"success": True})

# ---------------- EMAIL ACTIONS ----------------
@app.route("/email-approve/<int:tx_id>")
def email_approve(tx_id):
    supabase.table("transactions").update({"status": "Approved"}).eq("id", tx_id).execute()
    return "<h2>Transaction Approved</h2>"

@app.route("/email-reject/<int:tx_id>")
def email_reject(tx_id):
    supabase.table("transactions").update({"status": "Rejected"}).eq("id", tx_id).execute()
    return "<h2>Transaction Rejected</h2>"

# ---------------- FETCH DATA ----------------
@app.route("/get-transactions/<username>")
def get_transactions(username):
    result = supabase.table("transactions") \
        .select("*") \
        .eq("requester", username) \
        .order("created_at", desc=True) \
        .execute()
    return jsonify(result.data or [])

@app.route("/admin/pending-transactions")
def admin_pending():
    result = supabase.table("transactions") \
        .select("*") \
        .eq("status", "Pending") \
        .order("created_at", desc=True) \
        .execute()
    return jsonify(result.data or [])

@app.route("/user/history/<username>")
def user_history(username):
    result = supabase.table("transactions") \
        .select("*") \
        .eq("requester", username) \
        .in_("status", ["Approved", "Rejected"]) \
        .order("created_at", desc=True) \
        .execute()
    return jsonify(result.data or [])

@app.route("/admin/history")
def admin_history():
    result = supabase.table("transactions") \
        .select("*") \
        .in_("status", ["Approved", "Rejected"]) \
        .order("created_at", desc=True) \
        .execute()
    return jsonify(result.data or [])

@app.route("/admin/update-status", methods=["POST"])
def update_status():
    data = request.json or {}
    supabase.table("transactions") \
        .update({"status": data["status"]}) \
        .eq("id", data["id"]) \
        .execute()
    return jsonify({"success": True})

@app.route("/admin/stats")
def admin_stats():
    result = supabase.table("transactions") \
        .select("transaction_date,status") \
        .execute()
    return jsonify(result.data or [])

# ---------------- HOME ----------------
@app.route("/")
def login_page():
    return send_from_directory(".", "index.html")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)