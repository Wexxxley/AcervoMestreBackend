from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers.userController import user_router
from app.controllers.recursoController import recurso_router
from app.controllers.authController import auth_router
from app.controllers.playlistController import playlist_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*60)
    print("\033[92mSERVIDOR INICIADO COM SUCESSO!\033[0m")
    print("📄 \033[94mSwagger UI:\033[0m   http://localhost:8000/docs")
    print("="*60 + "\n")
    
    yield 
    
    print("🛑 Desligando API...")

app = FastAPI(
    title="Acervo Mestre API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(user_router)
app.include_router(recurso_router)
app.include_router(auth_router)  
app.include_router(playlist_router)
