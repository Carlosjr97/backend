from flask import Flask, request, jsonify
from flask_cors import CORS
import mercadopago
import os
import json
import requests
import base64
from dotenv import load_dotenv

# ===============================
# CONFIGURAÇÃO INICIAL
# ===============================
load_dotenv()

app = Flask(__name__)
CORS(app)

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

if not MP_ACCESS_TOKEN:
    raise Exception("MP_ACCESS_TOKEN não encontrado")

if not RESEND_API_KEY:
    raise Exception("RESEND_API_KEY não encontrado")

sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

# ===============================
# PERSISTÊNCIA SIMPLES (JSON)
# ===============================
ARQUIVO_PAGAMENTOS = "pagamentos.json"

def carregar_pagamentos():
    if not os.path.exists(ARQUIVO_PAGAMENTOS):
        return {}
    with open(ARQUIVO_PAGAMENTOS, "r") as f:
        return json.load(f)

def salvar_pagamentos(pagamentos):
    with open(ARQUIVO_PAGAMENTOS, "w") as f:
        json.dump(pagamentos, f)

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

        pagamentos = carregar_pagamentos()
        pagamentos[payment_id] = {
            "email": email,
            "status": "pending"
        }
        salvar_pagamentos(pagamentos)

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
    print("🔥 WEBHOOK RECEBIDO")
    data = request.json
    print("📦 DADOS:", data)

    payment_id = (
        data.get("data", {}).get("id")
        or data.get("id")
    )

    print("🆔 PAYMENT ID:", payment_id)

    if not payment_id:
        return "ok", 200

    pagamentos = carregar_pagamentos()

    if payment_id not in pagamentos:
        print("⚠️ Payment ID não encontrado")
        return "ok", 200

    pagamento = sdk.payment().get(payment_id)
    status = pagamento["response"]["status"]

    print("📌 STATUS:", status)

    if status == "approved" and pagamentos[payment_id]["status"] != "approved":
        email = pagamentos[payment_id]["email"]
        print("📧 ENVIANDO PLANILHA PARA:", email)

        enviar_planilha(email)

        pagamentos[payment_id]["status"] = "approved"
        salvar_pagamentos(pagamentos)

    return "ok", 200

# ===============================
# ENVIO DE PLANILHA POR EMAIL (RESEND)
# ===============================
def enviar_planilha(email):
    try:
        print("📧 Enviando planilha via Resend para:", email)

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        arquivo_path = os.path.join(BASE_DIR, "minhajornadamaisleve.xlsx")

        with open(arquivo_path, "rb") as f:
            arquivo_base64 = base64.b64encode(f.read()).decode("utf-8")

        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Minha Jornada <onboarding@resend.dev>",
                "to": [email],
                "subject": "Sua planilha de treino 💪",
                "text": (
                    "Parabéns pela compra!\n\n"
                    "Segue em anexo sua planilha de treino.\n\n"
                    "Bons treinos 💪🔥"
                ),
                "attachments": [
                    {
                        "filename": "minhajornadamaisleve.xlsx",
                        "content": arquivo_base64
                    }
                ]
            }
        )

        print("📨 Resposta Resend:", response.status_code, response.text)

        if response.status_code >= 300:
            raise Exception("Erro ao enviar e-mail via Resend")

        print("✅ E-mail enviado com sucesso via Resend!")

    except Exception as e:
        print("❌ ERRO AO ENVIAR E-MAIL:", str(e))
        raise

# ===============================
# ROTA DE TESTE (REMOVER EM PRODUÇÃO)
# ===============================
@app.route("/teste-email")
def teste_email():
    enviar_planilha("cbarbosa1009@gmail.com")
    return "Email enviado com sucesso", 200

# ===============================
# START PARA RENDER
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
