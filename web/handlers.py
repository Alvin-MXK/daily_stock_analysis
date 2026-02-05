# -*- coding: utf-8 -*-
"""
===================================
Web 处理器层 - 请求处理
===================================

职责：
1. 处理各类 HTTP 请求
2. 调用服务层执行业务逻辑
3. 返回响应数据

处理器分类：
- PageHandler: 页面请求处理
- ApiHandler: API 接口处理
"""

from __future__ import annotations

import json
import re
import logging
from http import HTTPStatus
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING

from web.services import get_config_service, get_analysis_service
from web.templates import (
    render_config_page, render_history_page, 
    render_fund_list_page, render_fund_detail_page, 
    render_market_review_list_page, render_market_review_detail_page,
    render_system_status_page, render_error_page, render_toast
)
from src.enums import ReportType

if TYPE_CHECKING:
    from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


# ============================================================
# 响应辅助类
# ============================================================

class Response:
    """HTTP 响应封装"""
    
    def __init__(
        self,
        body: bytes,
        status: HTTPStatus = HTTPStatus.OK,
        content_type: str = "text/html; charset=utf-8"
    ):
        self.body = body
        self.status = status
        self.content_type = content_type
    
    def send(self, handler: 'BaseHTTPRequestHandler') -> None:
        """发送响应到客户端"""
        handler.send_response(self.status)
        handler.send_header("Content-Type", self.content_type)
        handler.send_header("Content-Length", str(len(self.body)))
        handler.end_headers()
        handler.wfile.write(self.body)


class JsonResponse(Response):
    """JSON 响应封装"""
    
    def __init__(
        self,
        data: Dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK
    ):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        super().__init__(
            body=body,
            status=status,
            content_type="application/json; charset=utf-8"
        )


class HtmlResponse(Response):
    """HTML 响应封装"""
    
    def __init__(
        self,
        body: bytes,
        status: HTTPStatus = HTTPStatus.OK
    ):
        super().__init__(
            body=body,
            status=status,
            content_type="text/html; charset=utf-8"
        )


# ============================================================
# 页面处理器
# ============================================================

class PageHandler:
    """页面请求处理器"""
    
    def __init__(self):
        self.config_service = get_config_service()
    
    def handle_index(self) -> Response:
        """处理首页请求 GET / (现在显示基金列表)"""
        config_service = self.config_service
        analysis_service = get_analysis_service()
        from src.config import get_config
        config = get_config()
        
        # 获取自选股列表
        stock_list_str = config_service.get_stock_list()
        codes = [c.strip() for c in stock_list_str.split(',') if c.strip()]
        
        # 获取最新成功分析记录
        latest_analyses = analysis_service.get_latest_successful_analysis(codes)
        
        # 获取基金名称映射
        from src.analyzer import ASSET_NAME_MAP
        import efinance as ef
        
        # 优化：批量获取实时行情/估值，避免循环请求
        realtime_data = {}
        try:
            # 使用基金实时估值接口，一次性获取列表中的所有基金
            rt_df = ef.fund.get_realtime_increase_rate(codes)
            if rt_df is not None and not rt_df.empty:
                for _, row in rt_df.iterrows():
                    f_code = row['基金代码']
                    f_yield = row.get('估算涨跌幅')
                    if f_yield is not None and f_yield != '--':
                        realtime_data[f_code] = f"{float(f_yield):+.2f}%"
        except Exception as e:
            logger.debug(f"批量获取实时收益率失败: {e}")

        funds_data = []
        for code in codes:
            analysis = latest_analyses.get(code, {})
            
            # 优先使用批量获取的实时收益率，如果没有则显示 -
            prev_yield = realtime_data.get(code, "-")
            
            # 如果实时估值没拿到（可能非交易时间），尝试从数据库拿最后一次收盘收益率
            if prev_yield == "-":
                try:
                    from src.storage import get_db
                    db = get_db()
                    latest_daily = db.get_latest_data(code, days=1)
                    if latest_daily:
                        pct = latest_daily[0].pct_chg
                        if pct is not None:
                            prev_yield = f"{float(pct):+.2f}%"
                except:
                    pass

            funds_data.append({
                "code": code,
                "name": ASSET_NAME_MAP.get(code, analysis.get("name", f"基金{code}")),
                "latest_analysis": analysis,
                "prev_yield": prev_yield
            })
            
        body = render_fund_list_page(funds_data, config.schedule_time)
        return HtmlResponse(body)

    def handle_run_all_analysis(self) -> Response:
        """执行全量分析 GET /analysis/all"""
        from main import run_full_analysis
        from src.config import get_config
        import argparse
        import threading
        
        config = get_config()
        args = argparse.Namespace(
            debug=False,
            dry_run=False,
            stocks=None,
            no_notify=False,
            single_notify=True,
            workers=config.max_workers,
            no_market_review=False,
            no_context_snapshot=False
        )
        
        thread = threading.Thread(target=run_full_analysis, args=(config, args))
        thread.start()
        
        return self.handle_index()

    def handle_fund_detail(self, query: Dict[str, list]) -> Response:
        """处理基金详情页面 GET /fund/detail?code=xxx"""
        code = query.get("code", [""])[0].strip()
        if not code:
            return HtmlResponse(render_error_page(400, "缺少基金代码", "请提供有效的基金代码"))
            
        analysis_service = get_analysis_service()
        history = analysis_service.get_analysis_history(code=code, success=True, limit=1)
        latest_analysis = history[0] if history else None
        
        from src.analyzer import ASSET_NAME_MAP
        name = ASSET_NAME_MAP.get(code, latest_analysis.get("name", f"基金{code}") if latest_analysis else f"基金{code}")
        
        fund_info = {}
        performance = {}
        holdings = []
        realtime_valuation = {"value": "-", "source": "N/A", "time": "-"}
        
        try:
            import efinance as ef
            import pandas as pd
            # 1. 基本信息
            info = ef.fund.get_base_info(code)
            if info is not None:
                if isinstance(info, pd.Series): fund_info = info.to_dict()
                elif isinstance(info, pd.DataFrame) and not info.empty: fund_info = info.iloc[0].to_dict()
            
            # 2. 阶段收益率
            perf_df = ef.fund.get_period_change(code)
            if perf_df is not None and not perf_df.empty:
                for _, row in perf_df.iterrows():
                    performance[row['时间段']] = f"{row['收益率']:+.2f}%" if row['收益率'] != '--' else "-"
            
            # 3. 实时估值 (官方接口)
            try:
                rt_val_df = ef.fund.get_realtime_increase_rate(code)
                if rt_val_df is not None and not rt_val_df.empty:
                    row = rt_val_df.iloc[0]
                    val = row.get('估算涨跌幅')
                    if val is not None and val != '--':
                        realtime_valuation["value"] = f"{float(val):+.2f}%"
                        realtime_valuation["source"] = "官方实时估算"
                        realtime_valuation["time"] = row.get('估算时间', '-')
            except: pass

            # 4. 持仓明细
            try:
                pos_df = ef.fund.get_invest_position(code)
                if pos_df is not None and not pos_df.empty:
                    latest_date = pos_df['截止日期'].max()
                    current_pos = pos_df[pos_df['截止日期'] == latest_date].head(10)
                    for _, row in current_pos.iterrows():
                        holdings.append({
                            "name": row.get('股票名称', row.get('债券名称', '-')),
                            "code": row.get('股票代码', row.get('债券代码', '-')),
                            "ratio": f"{row.get('持仓比例', 0):.2f}%"
                        })
                    
                    # 模拟估值逻辑 (如果官方失效)
                    if realtime_valuation["value"] == "-":
                        sim_yield = 0.0
                        total_ratio = 0.0
                        stock_codes = [h['code'] for h in holdings if h['code'].isdigit() and len(h['code']) == 6]
                        if stock_codes:
                            stocks_rt = ef.stock.get_realtime_quotes(stock_codes)
                            if stocks_rt is not None and not stocks_rt.empty:
                                for h in holdings:
                                    s_row = stocks_rt[stocks_rt['股票代码'] == h['code']]
                                    if not s_row.empty:
                                        chg = s_row.iloc[0].get('涨跌幅', 0)
                                        ratio = float(h['ratio'].replace('%', ''))
                                        sim_yield += (float(chg) * ratio / 100)
                                        total_ratio += ratio
                                if total_ratio > 0:
                                    realtime_valuation["value"] = f"{sim_yield:+.2f}%"
                                    realtime_valuation["source"] = f"基于重仓股({latest_date})模拟"
                                    realtime_valuation["time"] = datetime.now().strftime('%H:%M:%S')
            except: pass

            hist_df = ef.fund.get_quote_history(code)
            if hist_df is not None and not hist_df.empty:
                latest_change = hist_df.iloc[0].get('涨跌幅')
                if latest_change is not None and latest_change != '--':
                    fund_info['前日收益率'] = f"{float(latest_change):+.2f}%"
        except: pass
            
        body = render_fund_detail_page(code, name, fund_info, performance, holdings, realtime_valuation, latest_analysis)
        return HtmlResponse(body)

    def handle_config(self) -> Response:
        """处理配置页面 GET /config"""
        stock_list = self.config_service.get_stock_list()
        env_filename = self.config_service.get_env_filename()
        body = render_config_page(stock_list, env_filename)
        return HtmlResponse(body)
    
    def handle_update(self, form_data: Dict[str, list]) -> Response:
        """处理配置更新 POST /update"""
        updates = {
            "STOCK_LIST": form_data.get("stock_list", [""])[0],
            "GEMINI_API_KEY": form_data.get("gemini_key", [""])[0],
            "SCHEDULE_TIME": form_data.get("schedule_time", [""])[0],
            "EMAIL_SENDER": form_data.get("email_sender", [""])[0],
            "EMAIL_PASSWORD": form_data.get("email_password", [""])[0],
            "EMAIL_RECEIVERS": form_data.get("email_receivers", [""])[0],
            "TAVILY_API_KEYS": form_data.get("tavily_key", [""])[0],
            "SERPAPI_API_KEYS": form_data.get("serpapi_key", [""])[0],
        }
        
        env_text = self.config_service.read_env_text()
        from src.config import get_config
        config = get_config()

        for key, value in updates.items():
            if not value or "*" in value: continue
            if f"{key}=" in env_text:
                env_text = re.sub(f"^{key}=.*", f"{key}={value}", env_text, flags=re.MULTILINE)
            else:
                env_text += f"\n{key}={value}"
            
            attr_name = key.lower()
            if hasattr(config, attr_name): setattr(config, attr_name, value)
            elif key == "GEMINI_API_KEY": config.gemini_api_key = value
            elif key == "TAVILY_API_KEYS": config.tavily_api_keys = [v.strip() for v in value.split(',')]
            elif key == "SERPAPI_API_KEYS": config.serpapi_keys = [v.strip() for v in value.split(',')]
            elif key == "EMAIL_RECEIVERS": config.email_receivers = [value.strip()]

        self.config_service.write_env_text(env_text)
        env_filename = self.config_service.get_env_filename()
        msg = "配置已成功更新！注意：新配置将在下一次全量分析任务启动时正式生效。"
        body = render_config_page(updates["STOCK_LIST"], env_filename, message=msg)
        return HtmlResponse(body)

    def handle_history(self, query: Dict[str, list]) -> Response:
        """处理历史记录页面 GET /history"""
        analysis_service = get_analysis_service()
        code = query.get("code", [""])[0].strip() or None
        success_str = query.get("success", [""])[0].strip().lower()
        success = True if success_str == "true" else (False if success_str == "false" else None)
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        sort_by, sort_order = query.get("sort_by", ["created_at"])[0], query.get("sort_order", ["desc"])[0]
        
        offset = (page - 1) * limit
        history = analysis_service.get_analysis_history(code=code, success=success, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order)
        total_count = analysis_service.get_history_count(code=code, success=success)
        
        body = render_history_page(history, total_count, page, limit, code, success, sort_by, sort_order)
        return HtmlResponse(body)
    
    def handle_market_review_list(self, query: Dict[str, list]) -> Response:
        """处理综合分析列表页面 GET /market_review"""
        analysis_service = get_analysis_service()
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["10"])[0])
        offset = (page - 1) * limit
        history = analysis_service.get_analysis_history(code="ALL_FUNDS", limit=limit, offset=offset, sort_by="created_at", sort_order="desc")
        total_count = analysis_service.get_history_count(code="ALL_FUNDS")
        
        body = render_market_review_list_page(history, total_count, page, limit)
        return HtmlResponse(body)

    def handle_market_review_detail(self, query: Dict[str, list]) -> Response:
        """处理综合分析详情页面 GET /market_review/detail?id=xxx"""
        record_id = query.get("id", [""])[0].strip()
        if not record_id: return HtmlResponse(render_error_page(400, "缺少记录ID", "请提供有效的记录ID"))
            
        from src.storage import get_db, AnalysisHistory
        from sqlalchemy import select
        db = get_db()
        with db.get_session() as session:
            record = session.execute(select(AnalysisHistory).where(AnalysisHistory.id == int(record_id))).scalar_one_or_none()
            if not record: return HtmlResponse(render_error_page(404, "未找到记录", "该综合分析记录不存在"))
            body = render_market_review_detail_page(record.to_dict())
            return HtmlResponse(body)

    def handle_run_market_review(self) -> Response:
        """执行综合分析 GET /market_review/run"""
        from src.config import get_config
        from main import StockAnalysisPipeline
        from src.analyzer import GeminiAnalyzer
        import uuid
        
        config = get_config()
        codes = [c.strip() for c in config.stock_list]
        pipeline = StockAnalysisPipeline(config=config)
        
        results = []
        for code in codes:
            from src.storage import get_db, AnalysisHistory
            from sqlalchemy import select, desc, and_
            db = get_db()
            with db.get_session() as session:
                record = session.execute(
                    select(AnalysisHistory)
                    .where(and_(AnalysisHistory.code == code, AnalysisHistory.success == True))
                    .order_by(desc(AnalysisHistory.created_at))
                    .limit(1)
                ).scalar_one_or_none()
                if record:
                    from dataclasses import dataclass
                    @dataclass
                    class SimpleResult:
                        code: str
                        name: str
                        operation_advice: str
                        sentiment_score: int
                        trend_prediction: str
                        analysis_summary: str
                    
                    results.append(SimpleResult(
                        code=record.code, name=record.name,
                        operation_advice=record.operation_advice,
                        sentiment_score=record.sentiment_score,
                        trend_prediction=record.trend_prediction,
                        analysis_summary=record.analysis_summary
                    ))
        
        analyzer = GeminiAnalyzer()
        summary_prompt = f"你是一位资深基金投资顾问。请根据以下 {len(results)} 只基金的最新分析结果，生成一份【持仓综合研判报告】。\n\n## 原始分析数据：\n"
        for res in results:
            summary_prompt += f"- {res.name}({res.code}): 建议={res.operation_advice}, 评分={res.sentiment_score}, 趋势={res.trend_prediction}, 总结={res.analysis_summary}\n"
        summary_prompt += "\n## 要求：\n1. **核心决策结论**：明确列出哪些基金建议【立即补仓/申购】、哪些建议【逢高减仓/赎回】、哪些建议【持续观察】。\n2. **风险/利好点睛**：用一句话总结当前持仓面临的最大风险和最大机会。\n3. **资产配置建议**：给出一个总体的仓位控制建议。\n4. **格式要求**：使用 Markdown 格式，关键信息加粗。\n"
        
        try:
            report = analyzer._call_api_with_retry(summary_prompt, {"temperature": 0.5})
            from src.storage import get_db
            db = get_db()
            class MockResult:
                def __init__(self, r): self.code, self.name, self.sentiment_score, self.operation_advice, self.trend_prediction, self.analysis_summary, self.success = "ALL_FUNDS", "持仓综合研判", 0, "综合建议", "综合趋势", r, True
                def get_sniper_points(self): return {}
            db.save_analysis_history(MockResult(report), f"market_review_{uuid.uuid4().hex[:8]}", "full", None)
        except Exception as e:
            logger.error(f"AI 汇总分析失败: {e}")
        
        return self.handle_market_review_list({"page": ["1"]})

    def handle_system_status_page(self) -> Response:
        """处理系统状态页面 GET /system/status"""
        analysis_service = get_analysis_service()
        tasks = analysis_service.list_tasks(limit=50)
        health_data = {"status": "ok", "timestamp": datetime.now().isoformat(), "service": "stock-analysis-webui"}
        body = render_system_status_page(tasks, health_data)
        return HtmlResponse(body)


# ============================================================
# API 处理器
# ============================================================

class ApiHandler:
    """API 请求处理器"""
    
    def __init__(self):
        self.analysis_service = get_analysis_service()
    
    def handle_health(self) -> Response:
        data = {"status": "ok", "timestamp": datetime.now().isoformat(), "service": "stock-analysis-webui"}
        return JsonResponse(data)
    
    def handle_analysis(self, query: Dict[str, list]) -> Response:
        code_list = query.get("code", [])
        if not code_list or not code_list[0].strip():
            return JsonResponse({"success": False, "error": "缺少必填参数: code"}, status=HTTPStatus.BAD_REQUEST)
        code = code_list[0].strip().upper()
        if not (re.match(r'^\d{6}$', code) or re.match(r'^HK\d{5}$', code) or re.match(r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$', code)):
            return JsonResponse({"success": False, "error": f"无效代码: {code}"}, status=HTTPStatus.BAD_REQUEST)
        
        report_type = ReportType.from_str(query.get("report_type", ["simple"])[0])
        save_snapshot = query.get("save_context_snapshot", [""])[0].strip().lower() in {"1", "true", "yes"}

        try:
            result = self.analysis_service.submit_analysis(code, report_type=report_type, save_context_snapshot=save_snapshot)
            return JsonResponse(result)
        except Exception as e:
            logger.error(f"[ApiHandler] 提交失败: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_analysis_history(self, query: Dict[str, list]) -> Response:
        code = query.get("code", [""])[0].strip() or None
        query_id = query.get("query_id", [""])[0].strip() or None
        days = int(query.get("days", ["30"])[0])
        limit = int(query.get("limit", ["50"])[0])
        history = self.analysis_service.get_analysis_history(code=code, query_id=query_id, days=days, limit=limit)
        return JsonResponse({"success": True, "records": history, "count": len(history)})

    def handle_tasks(self, query: Dict[str, list]) -> Response:
        limit = int(query.get("limit", ["20"])[0])
        tasks = self.analysis_service.list_tasks(limit=limit)
        return JsonResponse({"success": True, "tasks": tasks})
    
    def handle_task_status(self, query: Dict[str, list]) -> Response:
        task_id = query.get("id", [""])[0].strip()
        if not task_id: return JsonResponse({"success": False, "error": "缺少ID"}, status=HTTPStatus.BAD_REQUEST)
        task = self.analysis_service.get_task_status(task_id)
        if task is None: return JsonResponse({"success": False, "error": "不存在"}, status=HTTPStatus.NOT_FOUND)
        return JsonResponse({"success": True, "task": task})


# ============================================================
# Bot Webhook 处理器
# ============================================================

class BotHandler:
    def handle_webhook(self, platform: str, form_data: Dict[str, list], headers: Dict[str, str], body: bytes) -> Response:
        try:
            from bot.handler import handle_webhook
            webhook_response = handle_webhook(platform, headers, body)
            return JsonResponse(webhook_response.body, status=HTTPStatus(webhook_response.status_code))
        except Exception as e:
            logger.error(f"[BotHandler] 失败: {e}")
            return JsonResponse({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


# ============================================================
# 处理器工厂
# ============================================================

_page_handler: PageHandler | None = None
_api_handler: ApiHandler | None = None
_bot_handler: BotHandler | None = None

def get_page_handler() -> PageHandler:
    global _page_handler
    if _page_handler is None: _page_handler = PageHandler()
    return _page_handler

def get_api_handler() -> ApiHandler:
    global _api_handler
    if _api_handler is None: _api_handler = ApiHandler()
    return _api_handler

def get_bot_handler() -> BotHandler:
    global _bot_handler
    if _bot_handler is None: _bot_handler = BotHandler()
    return _bot_handler
