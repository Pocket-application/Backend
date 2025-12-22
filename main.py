from fastapi import FastAPI
from middleware.logging import auditoria_middleware
from routers import auth, usuarios, cuentas, categorias, flujo, transferencias

app = FastAPI(title="Sistema Financiero")

app.middleware("http")(auditoria_middleware)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(cuentas.router)
app.include_router(categorias.router)
app.include_router(flujo.router)
app.include_router(transferencias.router)