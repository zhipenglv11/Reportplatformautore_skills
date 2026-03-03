# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

app = FastAPI(
    title="AutoRe API",
    version="0.1.0",
    description="Phase 0: 最小可卖Demo"
)

# CORS 配置：从环境变量 ALLOWED_ORIGINS 读取（逗号分隔），默认允许本地开发地址
_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由(统一加api前缀)
from api import routes
from api import collection_routes
from api import declarative_skill_routes
from api import skill_orchestrator_routes

app.include_router(routes.router, prefix="/api")
app.include_router(collection_routes.router, prefix="/api")
app.include_router(declarative_skill_routes.router, prefix="/api")
app.include_router(skill_orchestrator_routes.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "AutoRe API", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

