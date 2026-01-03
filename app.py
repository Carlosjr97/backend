from flask import Flask, request, jsonify
from flask_cors import CORS
import mercadopago
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)

# Mercado Pago
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
if not MP_ACCESS_TOKEN:
    raise Exception("MP_ACCESS_TOKEN não encontrado")

sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

# 🔹 Armazena pagamentos (simples para início)
pagamentos = {}

# ===============================
# CRIAR PAGAMENTO PIX
# ===============================
@app.route("/criar-pagamento", methods=["POST"])
def criar_pagamento():
    data = request.get_json()

    if not data:
        return jsonify({"erro": "JSON inválido"}), 400

    email = data.get("email")
    if not email:
        return jsonify({"erro": "Email é obrigatório"}), 400

    try:
        pagamento = sdk.payment().create({
            "transaction_amount": 5.00,
            "description": "Planilha de Treino para Emagrecimento",
            "payment_method_id": "pix",
            "payer": {
                "email": email
            }
        })

        response = pagamento.get("response")

        if not response or "point_of_interaction" not in response:
            return jsonify({"erro": "Erro ao gerar Pix"}), 500

        payment_id = response["id"]
        transaction_data = response["point_of_interaction"]["transaction_data"]

        # 🔹 Salva pagamento
        pagamentos[payment_id] = {
            "email": email,
            "status": "pending"
        }

        return jsonify({
            "payment_id": payment_id,
            "qr_code": transaction_data["qr_code"]
        })

    except Exception as e:
        return jsonify({
            "erro": "Erro interno ao gerar Pix",
            "mensagem": str(e)
        }), 500


# ===============================
# WEBHOOK MERCADO PAGO
# ===============================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    payment_id = data.get("data", {}).get("id")

    if not payment_id or payment_id not in pagamentos:
        return "ok", 200

    pagamento = sdk.payment().get(payment_id)
    status = pagamento["response"]["status"]

    if status == "approved" and pagamentos[payment_id]["status"] != "approved":
        email = pagamentos[payment_id]["email"]

        enviar_planilha(email)

        pagamentos[payment_id]["status"] = "approved"

    return "ok", 200


# ===============================
# ENVIO DE PLANILHA POR EMAIL
# ===============================
def enviar_planilha(email):
    EMAIL_HOST = os.getenv("EMAIL_HOST")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    msg = EmailMessage()
    msg["Subject"] = "Sua planilha de treino 💪"
    msg["From"] = EMAIL_USER
    msg["To"] = email

    msg.set_content(
        "Parabéns pela compra!\n\n"
        "Segue em anexo sua planilha de treino.\n\n"
        "Bons treinos 💪🔥"
    )

    # ⚠️ A planilha deve estar no repositório
    with open("minhajornadamaisleve.xlsx", "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="minhajornadamaisleve.xlsx"
        )

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)


# ===============================
# START PARA RENDER
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

