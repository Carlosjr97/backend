import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

def enviar_planilha(email_destino):
    msg = EmailMessage()
    msg["Subject"] = "Sua planilha de treino chegou 💪"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = email_destino

    msg.set_content("Obrigado pela compra! Sua planilha está em anexo.")

    with open("planilha/minhajornadamaisleve.xlsx", "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="planilha_treino.xlsx"
        )

    with smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT"))) as smtp:
        smtp.starttls()
        smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        smtp.send_message(msg)
