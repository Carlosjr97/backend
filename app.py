from flask import Flask, request, jsonify
import mercadopago
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

@app.route("/criar-pagamento", methods=["POST"])
def criar_pagamento():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"erro": "Email é obrigatório"}), 400

    pagamento = sdk.payment().create({
        "transaction_amount": 5.00,
        "description": "Planilha de Treino para Emagrecimento",
        "payment_method_id": "pix",
        "payer": {
            "email": email
        }
    })

    response = pagamento["response"]

    return jsonify({
        "payment_id": response["id"],
        "qr_code": response["point_of_interaction"]["transaction_data"]["qr_code"],
        "qr_code_base64": response["point_of_interaction"]["transaction_data"]["qr_code_base64"]
    })

if __name__ == "__main__":
    app.run(debug=True)
