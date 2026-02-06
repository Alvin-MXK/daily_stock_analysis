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

def fetch_realtime_fund_gz(code: str) -> Optional[Dict[str, Any]]:
    """从天天基金接口获取实时估值"""
    import requests
    import re
    url = f"https://fundgz.1234567.com.cn/js/{code}.js"
    try:
        # 模拟浏览器请求
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=3)
        if resp.status_code == 200:
            match = re.search(r'jsonpgz\((.*)\);', resp.text)
            if match:
                return json.loads(match.group(1))
    except:
        pass
    return None


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
        
        # 并发获取实时估值数据
        import concurrent.futures
        realtime_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_code = {executor.submit(fetch_realtime_fund_gz, code): code for code in codes}
            for future in concurrent.futures.as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    data = future.result()
                    if data:
                        realtime_results[code] = data
                except:
                    pass

        funds_data = []
        for code in codes:
            analysis = latest_analyses.get(code, {})
            gz_data = realtime_results.get(code, {})
            
            # 提取实时数据
            realtime_yield = gz_data.get('gszzl', '-')
            if realtime_yield != '-':
                realtime_yield = f"{float(realtime_yield):+.2f}%"
            
            funds_data.append({
                "code": code,
                "name": ASSET_NAME_MAP.get(code, gz_data.get("name", analysis.get("name", f"基金{code}"))),
                "latest_analysis": analysis,
                "realtime_yield": realtime_yield,
                "prev_close": gz_data.get('dwjz', '-'),
                "current_price": gz_data.get('gsz', '-'),
                "refresh_time": gz_data.get('gztime', '-')
            })
            
        from web.templates import render_fund_list_page
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
        
        thread = threading.Thread(target=run_full_analysis, args=(config, args, None, True))
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
        
        # 获取实时估值
        gz_data = fetch_realtime_fund_gz(code) or {}
        
        from src.analyzer import ASSET_NAME_MAP
        name = ASSET_NAME_MAP.get(code, gz_data.get("name", latest_analysis.get("name", f"基金{code}") if latest_analysis else f"基金{code}"))
        
        fund_info = {}
        performance = {}
        realtime_valuation = {
            "value": f"{float(gz_data.get('gszzl', 0)):+.2f}%" if gz_data.get('gszzl') else "-",
            "price": gz_data.get('gsz', '-'),
            "prev_close": gz_data.get('dwjz', '-'),
            "source": "天天基金实时估算",
            "time": gz_data.get('gztime', '-')
        }
        
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
        except: pass
            
        body = render_fund_detail_page(code, name, fund_info, performance, realtime_valuation, latest_analysis)
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

    def handle_send_email_report(self, form_data: Dict[str, list]) -> Response:
        """手动发送邮件报告 POST /email/send_report"""
        try:
            from src.config import get_config
            from src.notification import NotificationService
            from src.storage import get_db, AnalysisHistory
            from sqlalchemy import select, desc, and_
            from src.analyzer import AnalysisResult
            import json
            
            config = get_config()
            db = get_db()
            notifier = NotificationService()
            
            # 获取所有自选股
            codes = [c.strip() for c in config.stock_list]
            if not codes:
                return JsonResponse({"success": False, "error": "未配置自选股列表"})
            
            # 获取每只股票最新的成功分析结果
            results = []
            with db.get_session() as session:
                for code in codes:
                    record = session.execute(
                        select(AnalysisHistory)
                        .where(and_(AnalysisHistory.code == code, AnalysisHistory.success == True))
                        .order_by(desc(AnalysisHistory.created_at))
                        .limit(1)
                    ).scalar_one_or_none()
                    
                    if record:
                        # 将数据库记录转换为 AnalysisResult 对象
                        # 注意：这里只需要部分关键字段用于生成报告
                        res = AnalysisResult(
                            code=record.code,
                            name=record.name,
                            sentiment_score=record.sentiment_score,
                            trend_prediction=record.trend_prediction,
                            operation_advice=record.operation_advice,
                            analysis_summary=record.analysis_summary
                        )
                        # 尝试解析 dashboard 数据
                        if record.raw_result:
                            try:
                                raw_data = json.loads(record.raw_result)
                                if 'dashboard' in raw_data:
                                    res.dashboard = raw_data['dashboard']
                            except:
                                pass
                        results.append(res)
            
            if not results:
                return JsonResponse({"success": False, "error": "暂无分析结果，请先执行分析"})
            
            # 生成报告并发送
            report = notifier.generate_dashboard_report(results)
            success = notifier.send_to_email(report)
            
            if success:
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "邮件发送失败，请检查配置或日志"})
                
        except Exception as e:
            logger.error(f"手动发送邮件失败: {e}")
            return JsonResponse({"success": False, "error": str(e)})

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
