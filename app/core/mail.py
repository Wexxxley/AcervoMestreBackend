# app/core/mail.py
import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv

load_dotenv()

# Configuração que pega do .env
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_activation_email(email_to: EmailStr, token: str):
    """Envia o e-mail com o token de ativação."""

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    activation_link = f"{frontend_url}/activate-account?token={token}"

    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Bem-vindo ao Acervo Mestre!</h2>
        <p>Um gestor criou sua conta.</p>
        <p>Para definir sua senha e liberar seu acesso, clique no botão abaixo:</p>
        <a href="{activation_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Ativar Conta</a>
        <p>Ou use este token diretamente: <b>{token}</b></p>
        <br>
        <p><small>Este link expira em 24 horas.</small></p>
    </div>
    """

    message = MessageSchema(
        subject="Convite de Acesso - Acervo Mestre",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)