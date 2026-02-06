# -*- coding: utf-8 -*-
"""
===================================
Web 路由层 - 请求分发
===================================

职责：
1. 解析请求路径
2. 分发到对应的处理器
3. 支持路由注册和扩展
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Callable, Dict, List, Optional, TYPE_CHECKING, Tuple
from urllib.parse import parse_qs, urlparse

from web.handlers import (
    Response, HtmlResponse, JsonResponse,
    get_page_handler, get_api_handler, get_bot_handler
)
from web.templates import render_error_page

if TYPE_CHECKING:
    from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


# ============================================================
# 路由定义
# ============================================================

RouteHandler = Callable[[Dict[str, list]], Response]


class Route:
    def __init__(self, path: str, method: str, handler: RouteHandler, description: str = ""):
        self.path = path
        self.method = method.upper()
        self.handler = handler
        self.description = description


class Router:
    def __init__(self):
        self._routes: Dict[str, Dict[str, Route]] = {}
    
    def register(self, path: str, method: str, handler: RouteHandler, description: str = "") -> None:
        method = method.upper()
        if path not in self._routes: self._routes[path] = {}
        self._routes[path][method] = Route(path, method, handler, description)
        logger.debug(f"[Router] 注册路由: {method} {path}")
    
    def match(self, path: str, method: str) -> Optional[Route]:
        method = method.upper()
        routes_for_path = self._routes.get(path)
        return routes_for_path.get(method) if routes_for_path else None
    
    def dispatch(self, request_handler: 'BaseHTTPRequestHandler', method: str) -> None:
        parsed = urlparse(request_handler.path)
        path, query = parsed.path or "/", parse_qs(parsed.query)
        route = self.match(path, method)
        if route is None: self._send_not_found(request_handler, path); return
        try:
            response = route.handler(query)
            response.send(request_handler)
        except Exception as e:
            logger.error(f"[Router] 失败: {method} {path} - {e}")
            self._send_error(request_handler, str(e))
    
    def dispatch_post(self, request_handler: 'BaseHTTPRequestHandler') -> None:
        parsed = urlparse(request_handler.path)
        path = parsed.path
        content_length = int(request_handler.headers.get("Content-Length", "0") or "0")
        raw_body_bytes = request_handler.rfile.read(content_length)
        if path.startswith("/bot/"): self._dispatch_bot_webhook(request_handler, path, raw_body_bytes); return
        form_data = parse_qs(raw_body_bytes.decode("utf-8", errors="replace"))
        route = self.match(path, "POST")
        if route is None: self._send_not_found(request_handler, path); return
        try:
            response = route.handler(form_data)
            response.send(request_handler)
        except Exception as e:
            logger.error(f"[Router] POST失败: {path} - {e}")
            self._send_error(request_handler, str(e))
    
    def _dispatch_bot_webhook(self, request_handler: 'BaseHTTPRequestHandler', path: str, body: bytes) -> None:
        parts = path.strip('/').split('/')
        if len(parts) < 2: self._send_not_found(request_handler, path); return
        platform = parts[1]
        headers = {key: value for key, value in request_handler.headers.items()}
        try:
            response = get_bot_handler().handle_webhook(platform, {}, headers, body)
            response.send(request_handler)
        except Exception as e:
            logger.error(f"[Router] Bot失败: {path} - {e}")
            self._send_error(request_handler, str(e))
    
    def list_routes(self) -> List[Tuple[str, str, str]]:
        routes = []
        for path, methods in self._routes.items():
            for method, route in methods.items():
                routes.append((method, path, route.description))
        return sorted(routes, key=lambda x: (x[1], x[0]))
    
    def _send_not_found(self, request_handler: 'BaseHTTPRequestHandler', path: str) -> None:
        body = render_error_page(404, "页面未找到", f"路径 {path} 不存在")
        HtmlResponse(body, status=HTTPStatus.NOT_FOUND).send(request_handler)
    
    def _send_error(self, request_handler: 'BaseHTTPRequestHandler', message: str) -> None:
        body = render_error_page(500, "服务器内部错误", message)
        HtmlResponse(body, status=HTTPStatus.INTERNAL_SERVER_ERROR).send(request_handler)


def create_default_router() -> Router:
    router = Router()
    page_handler, api_handler = get_page_handler(), get_api_handler()
    
    router.register("/", "GET", lambda q: page_handler.handle_index(), "基金概览首页")
    router.register("/fund/detail", "GET", lambda q: page_handler.handle_fund_detail(q), "基金详情")
    router.register("/history", "GET", lambda q: page_handler.handle_history(q), "分析历史")
    router.register("/market_review", "GET", lambda q: page_handler.handle_market_review_list(q), "综合分析列表")
    router.register("/market_review/detail", "GET", lambda q: page_handler.handle_market_review_detail(q), "综合分析详情")
    router.register("/market_review/run", "GET", lambda q: page_handler.handle_run_market_review(), "执行综合分析")
    router.register("/config", "GET", lambda q: page_handler.handle_config(), "配置管理")
    router.register("/update", "POST", lambda f: page_handler.handle_update(f), "更新配置")
    router.register("/email/send_report", "POST", lambda f: page_handler.handle_send_email_report(f), "手动发送邮件报告")
    router.register("/system/status", "GET", lambda q: page_handler.handle_system_status_page(), "系统状态")
    
    router.register("/health", "GET", lambda q: api_handler.handle_health(), "API: 健康检查")
    router.register("/analysis", "GET", lambda q: api_handler.handle_analysis(q), "API: 触发分析")
    router.register("/analysis/all", "GET", lambda q: page_handler.handle_run_all_analysis(), "API: 全量分析")
    router.register("/tasks", "GET", lambda q: api_handler.handle_tasks(q), "API: 任务列表")
    router.register("/task", "GET", lambda q: api_handler.handle_task_status(q), "API: 任务状态")
    
    return router

_default_router: Router | None = None
def get_router() -> Router:
    global _default_router
    if _default_router is None: _default_router = create_default_router()
    return _default_router
