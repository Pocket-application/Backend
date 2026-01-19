from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware

from middleware.logging import auditoria_middleware
from routers import auth, usuarios, cuentas, categorias, flujo, transferencias, saldos

app = FastAPI(title="Sistema Financiero")

app.add_middleware(
    ProxyHeadersMiddleware,
    trusted_hosts="*"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://oscarpalomino.dev",
        "https://www.oscarpalomino.dev",
        "capacitor://localhost",
        "ionic://localhost",
        "https://localhost"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👇 Middleware correcto
app.middleware("http")(auditoria_middleware)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(cuentas.router)
app.include_router(categorias.router)
app.include_router(flujo.router)
app.include_router(transferencias.router)
app.include_router(saldos.router)

@app.get("/health")
def health():
    return {"status": "ok"}
