
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from apps.api.settings import settings
from apps.api.routers.identity import router as auth_router, profile_router, addresses_router

app = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(addresses_router)

# Health
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
