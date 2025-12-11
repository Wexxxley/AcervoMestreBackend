import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from pathlib import Path
import base64
from dotenv import load_dotenv

load_dotenv()

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
    """Envia o e-mail com a logo embutida via Base64 e design ajustado."""

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    activation_link = f"{frontend_url}/activate-account?token={token}"

    current_dir = Path(__file__).resolve().parent
    logo_path = current_dir.parent.parent / "public" / "logoam.png"
    
    encoded_logo = ""
    
    if logo_path.is_file():
        with open(logo_path, "rb") as image_file:
            encoded_logo = base64.b64encode(image_file.read()).decode('utf-8')
    else:
        print(f"ERRO: Imagem não encontrada em {logo_path}")

    img_src = f"data:image/png;base64,{encoded_logo}" if encoded_logo else "https://via.placeholder.com/200x60?text=Logo"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Ativação de Conta</title>
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #e9ecef; margin: 0; padding: 0; }}
            
            .container {{ 
                max-width: 600px; 
                margin: 40px auto; 
                background-color: #ffffff; 
                border-radius: 8px; 
                overflow: hidden; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
            }}
            
            /* CABEÇALHO: Fundo branco para contraste com o logo + Borda verde */
            .header {{ 
                background-color: #ffffff; 
                padding: 30px 20px; 
                text-align: center; 
                border-bottom: 4px solid #4CAF50;
            }}
            
            .logo {{ 
                max-height: 70px; 
                width: auto; 
                display: block;
                margin: 0 auto;
            }}
            
            .content {{ 
                padding: 40px 30px; 
                text-align: center; 
                color: #555555; 
            }}
            
            h2 {{ color: #2c3e50; margin-top: 0; font-size: 24px; }}
            
            p {{ font-size: 16px; line-height: 1.6; margin-bottom: 20px; }}
            
            .button {{ 
                display: inline-block; 
                background-color: #4CAF50; 
                color: #ffffff; 
                padding: 15px 30px; 
                text-decoration: none; 
                border-radius: 6px; 
                font-weight: bold; 
                font-size: 16px; 
                margin: 25px 0; 
                box-shadow: 0 2px 5px rgba(76, 175, 80, 0.3);
            }}
            
            /* TOKEN BOX: Estilo tracejado antigo restaurado */
            .token-container {{
                margin-top: 30px;
                text-align: left;
            }}
            
            .token-label {{
                font-size: 14px;
                color: #888;
                margin-bottom: 8px;
                text-align: center;
                display: block;
            }}
            
            .token-box {{ 
                background-color: #f8f9fa; 
                border: 2px dashed #cccccc; 
                padding: 15px; 
                font-family: 'Consolas', 'Courier New', monospace; 
                font-size: 14px; 
                color: #333; 
                text-align: center;
                word-break: break-all; /* Importante para o token não quebrar o layout */
                border-radius: 4px;
            }}
            
            .footer {{ 
                background-color: #f8f9fa; 
                padding: 20px; 
                text-align: center; 
                font-size: 12px; 
                color: #999; 
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="{img_src}" alt="Logo Acervo Mestre" class="logo">
            </div>

            <div class="content">
                <h2>Bem-vindo ao Acervo Mestre!</h2>
                
                <p>
                    Olá! Você foi convidado a acessar nossa plataforma.
                    Para garantir sua segurança, clique no botão abaixo para definir sua senha.
                </p>

                <a href="{activation_link}" class="button">Definir Senha e Ativar</a>

                <div class="token-container">
                    <span class="token-label">Ou copie o token abaixo manualmente:</span>
                    <div class="token-box">
                        {token}
                    </div>
                </div>

                <p style="font-size: 13px; color: #999; margin-top: 30px;">
                    Este link expira em 24 horas.
                </p>
            </div>

            <div class="footer">
                <p>&copy; 2025 Acervo Mestre - Plataforma Educacional</p>
                <p>Se você não esperava por este e-mail, por favor ignore.</p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Convite de Acesso - Acervo Mestre",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    
    
async def send_reset_password_email(email_to: EmailStr, token: str):
    """Envia o e-mail de recuperação de senha mantendo o design system do projeto."""

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    # Ajuste a rota do front aqui se for diferente (ex: /recover-password)
    reset_link = f"{frontend_url}/reset-password?token={token}"

    current_dir = Path(__file__).resolve().parent
    logo_path = current_dir.parent.parent / "public" / "logoam.png"
    
    encoded_logo = ""
    
    if logo_path.is_file():
        with open(logo_path, "rb") as image_file:
            encoded_logo = base64.b64encode(image_file.read()).decode('utf-8')
    else:
        print(f"ERRO: Imagem não encontrada em {logo_path}")

    img_src = f"data:image/png;base64,{encoded_logo}" if encoded_logo else "https://via.placeholder.com/200x60?text=Logo"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Recuperação de Senha</title>
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #e9ecef; margin: 0; padding: 0; }}
            
            .container {{ 
                max-width: 600px; 
                margin: 40px auto; 
                background-color: #ffffff; 
                border-radius: 8px; 
                overflow: hidden; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
            }}
            
            .header {{ 
                background-color: #ffffff; 
                padding: 30px 20px; 
                text-align: center; 
                border-bottom: 4px solid #4CAF50;
            }}
            
            .logo {{ 
                max-height: 70px; 
                width: auto; 
                display: block;
                margin: 0 auto;
            }}
            
            .content {{ 
                padding: 40px 30px; 
                text-align: center; 
                color: #555555; 
            }}
            
            h2 {{ color: #2c3e50; margin-top: 0; font-size: 24px; }}
            
            p {{ font-size: 16px; line-height: 1.6; margin-bottom: 20px; }}
            
            .button {{ 
                display: inline-block; 
                background-color: #4CAF50; 
                color: #ffffff; 
                padding: 15px 30px; 
                text-decoration: none; 
                border-radius: 6px; 
                font-weight: bold; 
                font-size: 16px; 
                margin: 25px 0; 
                box-shadow: 0 2px 5px rgba(76, 175, 80, 0.3);
            }}
            
            .token-container {{
                margin-top: 30px;
                text-align: left;
            }}
            
            .token-label {{
                font-size: 14px;
                color: #888;
                margin-bottom: 8px;
                text-align: center;
                display: block;
            }}
            
            .token-box {{ 
                background-color: #f8f9fa; 
                border: 2px dashed #cccccc; 
                padding: 15px; 
                font-family: 'Consolas', 'Courier New', monospace; 
                font-size: 14px; 
                color: #333; 
                text-align: center;
                word-break: break-all;
                border-radius: 4px;
            }}
            
            .footer {{ 
                background-color: #f8f9fa; 
                padding: 20px; 
                text-align: center; 
                font-size: 12px; 
                color: #999; 
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="{img_src}" alt="Logo Acervo Mestre" class="logo">
            </div>

            <div class="content">
                <h2>Recuperação de Senha</h2>
                
                <p>
                    Recebemos uma solicitação para redefinir a senha da sua conta.
                    Se foi você, clique no botão abaixo para criar uma nova senha.
                </p>

                <a href="{reset_link}" class="button">Redefinir Senha</a>

                <div class="token-container">
                    <span class="token-label">Ou utilize o token abaixo:</span>
                    <div class="token-box">
                        {token}
                    </div>
                </div>

                <p style="font-size: 13px; color: #999; margin-top: 30px;">
                    Este link é válido por 30 minutos.
                </p>
            </div>

            <div class="footer">
                <p>&copy; 2025 Acervo Mestre - Plataforma Educacional</p>
                <p>Se você não solicitou esta alteração, ignore este e-mail.</p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Redefinição de Senha - Acervo Mestre",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)