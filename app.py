from flask import Flask, request, jsonify
from flask_cors import CORS
import mercadopago
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente (localmente)
load_dotenv()

app = Flask(__name__)
CORS(app)  # 🔓 Libera CORS (necessário para GitHub Pages)

# Mercado Pago SDK
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

if not MP_ACCESS_TOKEN:
    raise Exception("MP_ACCESS_TOKEN não encontrado nas variáveis de ambiente")

sdk = mercadopago.SDK(MP_ACCESS_TOKEN)


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
            return jsonify({
                "erro": "Erro ao gerar Pix",
                "detalhe": pagamento
            }), 500

        transaction_data = response["point_of_interaction"]["transaction_data"]

        return jsonify({
            "payment_id": response["id"],
            "qr_code": transaction_data["qr_code"],
        })

    except Exception as e:
        return jsonify({
            "erro": "Erro interno ao gerar Pix",
            "mensagem": str(e)
        }), 500


# 🔥 IMPORTANTE PARA O RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

