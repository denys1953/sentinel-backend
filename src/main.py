from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.auth.router import router as auth_router
from src.ws.router import router as ws_router
from src.users.router import router as users_router
from src.conversations.router import router as conversations_router

swagger_params = {"persistAuthorization": True}

app = FastAPI(swagger_ui_parameters=swagger_params)

origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
]

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def main():
    return {"Status": "OK"}


app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(conversations_router, prefix="/conversations", tags=["Conversations"])
app.include_router(ws_router, tags=["WebSockets"])