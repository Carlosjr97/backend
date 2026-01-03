import smtplib
from email.message import EmailMessage
import os

def enviar_planilha(email_destino):
    try:
        print("📧 Enviando planilha para:", email_destino)

        msg = EmailMessage()
        msg["Subject"] = "Sua planilha de treino chegou 💪"
        msg["From"] = os.getenv("EMAIL_USER")
        msg["To"] = email_destino

        msg.set_content("Obrigado pela compra! Sua planilha está em anexo.")

        with open("minhajornadamaisleve.xlsx", "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename="minhajornadamaisleve.xlsx"
            )

        with smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT", 587))) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            smtp.send_message(msg)

        print("✅ E-mail enviado com sucesso!")

    except Exception as e:
        print("❌ Erro ao enviar e-mail:", str(e))
