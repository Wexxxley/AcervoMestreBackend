from pwdlib import PasswordHash

pwd_context = PasswordHash.recommended()

def get_password_hash(password: str) -> str:
    """Recebe a senha pura e retorna o hash para salvar no banco."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara a senha informada no login com o hash salvo no banco.
    Retorna True se forem compatíveis.
    """
    return pwd_context.verify(plain_password, hashed_password)