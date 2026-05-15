"""简单的鉴权中间件"""

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from app.core.config import settings


# 简单的 admin 密码（后续改数据库存）
ADMIN_PASSWORD = "nesttalk2026"


def admin_auth_middleware(request: Request, call_next):
    """后台页面基础鉴权"""
    path = request.url.path

    # 只拦截页面请求（非 API）
    if path.startswith("/api/") or path in ("/login", "/api/health"):
        return call_next(request)

    # 检查 cookie
    token = request.cookies.get("nesttalk_admin")
    if token != ADMIN_PASSWORD:
        # 如果是页面请求，重定向到登录页
        if not path.startswith("/api/"):
            return RedirectResponse(url="/login", status_code=302)
        raise HTTPException(status_code=401, detail="Unauthorized")

    return call_next(request)
