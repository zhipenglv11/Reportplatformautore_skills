# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from config import settings


class UTF8CharsetMiddleware(BaseHTTPMiddleware):
    """确保 JSON 等响应带 charset=utf-8，避免中文乱码。"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        ct = response.headers.get("content-type", "")
        if "application/json" in ct and "charset=" not in ct:
            response.headers["content-type"] = "application/json; charset=utf-8"
        return response


app = FastAPI(
    title="AutoRe API",
    version="0.1.0",
    description="Phase 0: 最小可卖Demo"
)

# CORS：环境变量 ALLOWED_ORIGINS（逗号分隔）+ 正则放行本地与 Vercel 域名
_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
_origin_regex = (
    r"^http://(localhost|127\.0\.0\.1)(:\d+)?$|"
    r"^https://[\w-]+\.vercel\.app$"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_middleware(UTF8CharsetMiddleware)

# ── 数据采集域 ──
from collection.api import collection_routes
from collection.api import declarative_skill_routes
from collection.api import skill_orchestrator_routes

app.include_router(collection_routes.router, prefix="/api")
app.include_router(declarative_skill_routes.router, prefix="/api")
app.include_router(skill_orchestrator_routes.router, prefix="/api")

# ── 报告生成域 ──
from report.api import routes as report_routes

app.include_router(report_routes.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "AutoRe API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
