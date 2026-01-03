from flask import Flask, request
from email_service import enviar_planilha
import os

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    # Confirma se é notificação de pagamento
    if data.get("type") in ["payment", "payment.updated"]:
        payment_id = data["data"]["id"]
        pagamento = sdk.payment().get(payment_id)

        # Se aprovado, envia a planilha
        if pagamento["response"]["status"] == "approved":
            email = pagamento["response"]["payer"]["email"]
            enviar_planilha(email)

    return "OK", 200
