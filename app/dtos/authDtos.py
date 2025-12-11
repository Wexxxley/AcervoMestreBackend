from pydantic import EmailStr
from sqlmodel import SQLModel

# usuário envia para logar
class LoginRequest(SQLModel):
    email: EmailStr
    password: str

# sistema responde após login/refresh
class TokenResponse(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# usuário envia para pedir um novo token
class RefreshTokenRequest(SQLModel):
    refresh_token: str

# usuário envia para ativar a conta    
class ActivateAccountRequest(SQLModel):
    token: str
    new_password: str

# usuário envia para pedir reset de senha
class ForgotPasswordRequest(SQLModel):
    email: EmailStr    

# usuário envia para resetar a senha
class ResetPasswordRequest(SQLModel):
    token: str
    new_password: str