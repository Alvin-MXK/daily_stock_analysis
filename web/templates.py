# -*- coding: utf-8 -*-
"""
===================================
Web 模板层 - HTML 页面生成
===================================

职责：
1. 生成 HTML 页面
2. 管理 CSS 样式
3. 提供可复用的页面组件
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Optional, List, Dict, Any


# ============================================================
# CSS 样式定义
# ============================================================

BASE_CSS = """
:root {
    --primary: #2563eb;
    --primary-hover: #1d4ed8;
    --bg: #f8fafc;
    --card: #ffffff;
    --text: #1e293b;
    --text-light: #64748b;
    --border: #e2e8f0;
    --success: #10b981;
    --error: #ef4444;
    --warning: #f59e0b;
    --info: #3b82f6;
    --nav-bg: #1e293b;
    --nav-text: #ffffff;
}

* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: var(--bg);
    color: var(--text);
    margin: 0;
    padding: 0;
    min-height: 100vh;
}

.navbar {
    background-color: var(--nav-bg);
    color: var(--nav-text);
    padding: 0.75rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.navbar-brand {
    font-size: 1.1rem;
    font-weight: 700;
    text-decoration: none;
    color: white;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    white-space: nowrap;
}

.navbar-nav {
    display: flex;
    gap: 0.5rem;
    list-style: none;
    margin: 0;
    padding: 0;
    overflow-x: auto;
}

.nav-link {
    color: rgba(255,255,255,0.7);
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s;
    padding: 0.5rem 0.75rem;
    border-radius: 0.375rem;
    white-space: nowrap;
}

.nav-link:hover {
    color: white;
    background: rgba(255,255,255,0.1);
}

.nav-link.active {
    color: white;
    background: var(--primary);
}

.main-content {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 2rem;
}

.container {
    background: var(--card);
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    width: 100%;
    max-width: 800px;
}

/* 统一按钮样式 */
button, .btn {
    background-color: var(--primary);
    color: white;
    border: none;
    padding: 0.6rem 1.2rem;
    border-radius: 0.5rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    font-size: 0.9rem;
    border: 1px solid transparent;
}

button:hover, .btn:hover {
    background-color: var(--primary-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}

button:active, .btn:active {
    transform: translateY(0);
}

button:disabled, .btn:disabled {
    background-color: var(--text-light);
    cursor: not-allowed;
    transform: none;
    opacity: 0.6;
}

.btn-success { background-color: var(--success); }
.btn-success:hover { background-color: #059669; }

.btn-error { background-color: var(--error); }
.btn-error:hover { background-color: #dc2626; }

.btn-outline {
    background-color: transparent;
    border-color: var(--border);
    color: var(--text);
}
.btn-outline:hover {
    background-color: #f8fafc;
    border-color: var(--primary);
    color: var(--primary);
}

/* Table Styles */
.data-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
    font-size: 0.875rem;
}

.data-table th, .data-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
}

.data-table th {
    background-color: #f8fafc;
    font-weight: 600;
    color: var(--text-light);
    cursor: pointer;
}

.data-table tr:hover {
    background-color: #fdfdfd;
}

.sort-icon::after { content: ' ↕'; opacity: 0.3; font-size: 0.7rem; }
.sort-asc::after { content: ' ↑'; opacity: 1; }
.sort-desc::after { content: ' ↓'; opacity: 1; }

.search-box {
    width: 100%;
    padding: 0.6rem 1rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
}

.badge {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-success { background-color: #dcfce7; color: #166534; }
.badge-error { background-color: #fee2e2; color: #991b1b; }
.badge-warning { background-color: #fef3c7; color: #92400e; }
.badge-info { background-color: #dbeafe; color: #1e40af; }

/* Task/History Cards */
.task-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.task-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: #fff;
    border-radius: 0.75rem;
    border: 1px solid var(--border);
    transition: all 0.2s;
}

.task-card:hover {
    border-color: var(--primary);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}

.task-card.completed { border-left: 4px solid var(--success); }
.task-card.failed { border-left: 4px solid var(--error); }

.task-status {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    flex-shrink: 0;
    font-weight: bold;
}

.completed .task-status { background: #dcfce7; color: #166534; }
.failed .task-status { background: #fee2e2; color: #991b1b; }

.task-main { flex: 1; min-width: 0; }
.task-title { display: flex; align-items: center; gap: 0.5rem; font-weight: 700; margin-bottom: 0.25rem; }
.task-title .code { font-family: monospace; color: var(--primary); background: #eff6ff; padding: 0.1rem 0.4rem; border-radius: 0.25rem; font-size: 0.85rem; }
.task-meta { display: flex; gap: 1rem; font-size: 0.75rem; color: var(--text-light); }

.task-result { text-align: right; }
.task-score { display: block; font-size: 0.7rem; color: var(--text-light); margin-top: 0.25rem; }

.task-detail {
    background: #fff;
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 0.75rem 0.75rem;
    padding: 1.5rem;
    margin-top: -0.75rem;
    margin-bottom: 1rem;
}

/* Report Sections */
.report-section { margin-top: 1.5rem; border-top: 1px solid #f1f5f9; padding-top: 1rem; }
.report-section-title { font-size: 1rem; font-weight: 800; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.4rem; color: var(--text); }
.report-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
.report-card { background: #f8fafc; border: 1px solid var(--border); border-radius: 0.5rem; padding: 1rem; }
.mini-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.mini-table th, .mini-table td { padding: 0.4rem; border: 1px solid var(--border); text-align: left; }
.mini-table th { background: #f1f5f9; font-weight: 600; width: 40%; }
.check-list { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem; }
.check-item { font-size: 0.8rem; display: flex; align-items: center; gap: 0.3rem; color: var(--text-light); }
.one-sentence-box { border-left: 3px solid var(--primary); padding-left: 0.75rem; margin: 0.75rem 0; font-style: italic; font-size: 0.9rem; color: var(--text-light); }
.highlight-box { padding: 0.1rem 0.3rem; border-radius: 0.2rem; font-weight: 600; font-size: 0.85rem; }

.pagination { display: flex; justify-content: center; gap: 0.5rem; margin-top: 2rem; }
.page-btn { padding: 0.4rem 0.8rem; border: 1px solid var(--border); background: white; border-radius: 0.375rem; text-decoration: none; color: var(--text); font-size: 0.85rem; }
.page-btn.active { background: var(--primary); color: white; border-color: var(--primary); }

.code-badge { background: #f1f5f9; padding: 0.2rem 0.4rem; border-radius: 0.25rem; font-family: monospace; color: var(--primary); }
.form-group { margin-bottom: 1.5rem; }
label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
textarea, input[type="text"], input[type="password"] { width: 100%; padding: 0.75rem; border: 1px solid var(--border); border-radius: 0.5rem; font-size: 0.9rem; }
.text-muted { font-size: 0.75rem; color: var(--text-light); margin-top: 0.4rem; }
.footer { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--border); text-align: center; color: var(--text-light); font-size: 0.8rem; }

/* Performance Grid */
.perf-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 0.75rem;
    margin-top: 1rem;
}
.perf-item {
    background: #fff;
    border: 1px solid var(--border);
    padding: 0.5rem;
    border-radius: 0.5rem;
    text-align: center;
}
.perf-label { font-size: 0.7rem; color: var(--text-light); margin-bottom: 0.25rem; }
.perf-value { font-weight: 700; font-size: 0.9rem; }

/* Toast Notification */
.toast {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);
    background: white;
    border-left: 4px solid var(--success);
    padding: 1rem 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    opacity: 0;
    z-index: 1000;
}

.toast.show {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
}

/* Spinner */
.spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: spin 0.75s linear infinite;
    vertical-align: middle;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
"""


# ============================================================
# 页面组件渲染
# ============================================================

def render_dashboard_html(raw_result: str | Dict[str, Any]) -> str:
    """
    将 AI 返回的原始 JSON 结果渲染为精美的决策仪表盘 HTML
    """
    try:
        raw = json.loads(raw_result) if isinstance(raw_result, str) else raw_result
        if 'dashboard' not in raw:
            return f"<div class='task-hint'>无法解析仪表盘数据</div>"
        
        db = raw['dashboard']
        core = db.get('core_conclusion', {})
        pos_adv = core.get('position_advice', {})
        dp = db.get('data_perspective', {})
        ts = dp.get('trend_status', {})
        pp = dp.get('price_position', {})
        intel = db.get('intelligence', {})
        risks = "".join([f"<li>{html.escape(r)}</li>" for r in intel.get('risk_alerts', [])])
        positives = "".join([f"<li>{html.escape(p)}</li>" for p in intel.get('positive_catalysts', [])])
        bp = db.get('battle_plan', {})
        sp = bp.get('sniper_points', {})
        cl = "".join([f"<li class='check-item'>{html.escape(i)}</li>" for i in bp.get('action_checklist', [])])

        return f"""
        <div class="report-section">
            <div class="report-section-title">📰 重要信息速览</div>
            <div class="report-grid">
                <div class="report-card" style="background: #fef2f2; border-color: #fecaca;">
                    <div style="color: #991b1b; font-weight: bold; margin-bottom: 0.5rem;">🚩 风险警报</div>
                    <ul style="margin: 0; padding-left: 1.2rem; font-size: 0.8rem; color: #7f1d1d;">{risks or '<li>暂无明显风险</li>'}</ul>
                </div>
                <div class="report-card" style="background: #f0fdf4; border-color: #bbf7d0;">
                    <div style="color: #166534; font-weight: bold; margin-bottom: 0.5rem;">✨ 利好催化</div>
                    <ul style="margin: 0; padding-left: 1.2rem; font-size: 0.85rem; color: #14532d;">{positives or '<li>暂无明显利好</li>'}</ul>
                </div>
            </div>
            <div class="report-card">
                <div style="font-weight: bold; margin-bottom: 0.4rem; font-size: 0.85rem;">📣 最新动态</div>
                <div style="font-size: 0.8rem; color: var(--text-light);">{html.escape(intel.get('latest_news', '暂无最新动态'))}</div>
            </div>
        </div>
        <div class="report-section">
            <div class="report-section-title">📌 核心结论</div>
            <div class="report-card">
                <div style="font-weight: bold; font-size: 1rem; color: var(--primary);">{core.get('signal_type', '⚪ 观望信号')}</div>
                <div class="one-sentence-box">决策：{html.escape(core.get('one_sentence', '-'))}</div>
                <div style="font-size: 0.8rem; font-weight: bold; margin-bottom: 0.5rem;">⏰ 时效性：{core.get('time_sensitivity', '不急')}</div>
                <table class="mini-table">
                    <thead><tr><th>持仓情况</th><th>操作建议</th></tr></thead>
                    <tbody>
                        <tr><td>🆕 空仓者</td><td>{html.escape(pos_adv.get('no_position', '-'))}</td></tr>
                        <tr><td>💼 持仓者</td><td>{html.escape(pos_adv.get('has_position', '-'))}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        <div class="report-section">
            <div class="report-section-title">📊 数据透视</div>
            <div class="report-card">
                <div style="margin-bottom: 0.75rem; font-size: 0.85rem;"><strong>均线排列：</strong> {html.escape(ts.get('ma_alignment', '-'))} <span class="badge badge-info" style="font-size: 0.7rem;">强度: {ts.get('trend_score', 0)}</span></div>
                <table class="mini-table">
                    <tbody>
                        <tr><th>当前净值</th><td>{pp.get('current_price', '-')}</td></tr>
                        <tr><th>MA5 支撑</th><td>{pp.get('ma5', '-')}</td></tr>
                        <tr><th>乖离率 (MA5)</th><td><span style="color: {'#ef4444' if pp.get('bias_ma5', 0) > 3 else '#10b981'}; font-weight: bold;">{pp.get('bias_ma5', 0)}%</span> ({pp.get('bias_status', '-')})</td></tr>
                        <tr><th>压力位</th><td>{pp.get('resistance_level', '-')}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        <div class="report-section">
            <div class="report-section-title">🎯 作战计划</div>
            <div class="report-card">
                <table class="mini-table" style="margin-bottom: 0.75rem;">
                    <tbody>
                        <tr><th>🎯 理想买入</th><td style="color: #059669; font-weight: bold;">{sp.get('ideal_buy', '-')}</td></tr>
                        <tr><th>🛑 止损位</th><td style="color: #dc2626;">{sp.get('stop_loss', '-')}</td></tr>
                        <tr><th>🎁 目标位</th><td style="color: var(--primary);">{sp.get('take_profit', '-')}</td></tr>
                    </tbody>
                </table>
                <div style="background: #f8fafc; padding: 0.6rem; border-radius: 0.4rem; font-size: 0.8rem; line-height: 1.5;">
                    <strong>💰 仓位建议：</strong> {bp.get('position_strategy', {}).get('suggested_position', '-')}<br>
                    <strong>📝 策略：</strong> {html.escape(bp.get('position_strategy', {}).get('entry_plan', '-'))}
                </div>
            </div>
            <div class="report-card" style="margin-top: 0.75rem;">
                <div style="font-weight: bold; margin-bottom: 0.5rem; font-size: 0.85rem;">✅ 决策检查清单</div>
                <ul class="check-list">{cl or '<li>暂无清单数据</li>'}</ul>
            </div>
        </div>
        """
    except Exception as e:
        return f"<div class='badge badge-error'>渲染仪表盘失败: {str(e)}</div>"


# ============================================================
# 页面渲染函数
# ============================================================

def render_base(
    title: str,
    content: str,
    extra_css: str = "",
    extra_js: str = "",
    active_nav: str = "overview"
) -> str:
    """
    渲染基础 HTML 模板
    """
    nav_overview_active = " active" if active_nav == "overview" else ""
    nav_history_active = " active" if active_nav == "history" else ""
    nav_market_active = " active" if active_nav == "market" else ""
    nav_config_active = " active" if active_nav == "config" else ""
    nav_status_active = " active" if active_nav == "status" else ""
    
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>{BASE_CSS}{extra_css}</style>
</head>
<body>
  <nav class="navbar">
    <a href="/" class="navbar-brand">📊 智能基金分析</a>
    <ul class="navbar-nav">
      <li><a href="/" class="nav-link{nav_overview_active}">基金概览</a></li>
      <li><a href="/history" class="nav-link{nav_history_active}">分析历史</a></li>
      <li><a href="/market_review" class="nav-link{nav_market_active}">综合分析</a></li>
      <li><a href="/config" class="nav-link{nav_config_active}">配置管理</a></li>
      <li><a href="/system/status" class="nav-link{nav_status_active}">系统状态</a></li>
    </ul>
  </nav>
  <div class="main-content">
    {content}
  </div>
  {extra_js}
</body>
</html>"""


def render_fund_list_page(
    funds_data: List[Dict[str, Any]],
    schedule_time: Optional[str] = None
) -> bytes:
    """
    渲染基金概览首页
    """
    rows = []
    for fund in funds_data:
        code, name = fund['code'], fund['name']
        analysis = fund.get('latest_analysis') or {}
        advice, score, trend, time_str = analysis.get('operation_advice', '-'), analysis.get('sentiment_score', '-'), analysis.get('trend_prediction', '-'), analysis.get('created_at', '-')
        if time_str != '-':
            try: time_str = datetime.fromisoformat(time_str).strftime('%m-%d %H:%M')
            except: pass
        advice_class = "badge-info"
        if '买' in advice or '加仓' in advice: advice_class = "badge-success"
        elif '卖' in advice or '减仓' in advice: advice_class = "badge-error"
        elif '持有' in advice: advice_class = "badge-warning"
        
        prev_yield = fund.get('prev_yield', '-')
        yield_style = ""
        if '+' in prev_yield: yield_style = "color: #ef4444; font-weight: bold;"
        elif '-' in prev_yield: yield_style = "color: #10b981; font-weight: bold;"

        rows.append(f'<tr data-code="{code}" data-name="{name}"><td><code class="code-badge">{code}</code></td><td><a href="/fund/detail?code={code}" style="color: var(--primary); text-decoration: none; font-weight: 600;">{name}</a></td><td><span style="{yield_style}">{prev_yield}</span></td><td><span class="badge {advice_class}">{advice}</span></td><td><strong>{score}</strong></td><td>{trend}</td><td class="text-muted">{time_str}</td></tr>')
    
    content = f"""
  <div class="container" style="max-width: 1100px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h2>📋 场外基金概览</h2>
        <button type="button" class="btn btn-success" onclick="confirmAllAnalysis()">🚀 全量分析</button>
    </div>
    <p class="subtitle">管理当前配置的 {len(funds_data)} 只场外基金及其最新分析状态</p>
    
    <input type="text" id="fund_search" class="search-box" placeholder="搜索基金名称或代码..." onkeyup="filterFunds()">
    <div style="overflow-x: auto;"><table class="data-table" id="fund_table"><thead><tr><th onclick="sortTable(0)">代码 <span class="sort-icon"></span></th><th onclick="sortTable(1)">基金名称 <span class="sort-icon"></span></th><th onclick="sortTable(2)">前日收益 <span class="sort-icon"></span></th><th onclick="sortTable(3)">最新建议 <span class="sort-icon"></span></th><th onclick="sortTable(4)">评分 <span class="sort-icon"></span></th><th onclick="sortTable(5)">趋势 <span class="sort-icon"></span></th><th onclick="sortTable(6)">分析时间 <span class="sort-icon"></span></th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
  </div>
  <script>
    function confirmAllAnalysis() {{
        const scheduleTime = "{schedule_time or ''}";
        let msg = "确定要开始对所有基金进行全量分析吗？\\n\\n这可能需要 30-40 分钟。";
        if (scheduleTime) {{
            msg = "【定时任务提示】\\n系统已配置在每日 " + scheduleTime + " 自动执行全量分析。\\n\\n您确定现在要手动执行一次吗？";
        }}
        if (confirm(msg)) {{
            window.location.href = '/analysis/all';
        }}
    }}
    function filterFunds() {{ const input = document.getElementById('fund_search'); const filter = input.value.toUpperCase(); const table = document.getElementById('fund_table'); const tr = table.getElementsByTagName('tr'); for (let i = 1; i < tr.length; i++) {{ const code = tr[i].getAttribute('data-code') || ''; const name = tr[i].getAttribute('data-name') || ''; tr[i].style.display = (code.toUpperCase().indexOf(filter) > -1 || name.toUpperCase().indexOf(filter) > -1) ? "" : "none"; }} }}
    function sortTable(n) {{ const table = document.getElementById("fund_table"); let dir = "asc", switching = true, switchcount = 0; const headers = table.getElementsByTagName("th"); for (let i = 0; i < headers.length; i++) headers[i].classList.remove("sort-asc", "sort-desc"); while (switching) {{ switching = false; const rows = table.rows; for (let i = 1; i < (rows.length - 1); i++) {{ let shouldSwitch = false; let x = rows[i].getElementsByTagName("TD")[n].textContent; let y = rows[i+1].getElementsByTagName("TD")[n].textContent; if (n === 4) {{ x = parseFloat(x) || 0; y = parseFloat(y) || 0; }} if (dir == "asc" ? x > y : x < y) {{ shouldSwitch = true; break; }} }} if (shouldSwitch) {{ rows[i].parentNode.insertBefore(rows[i + 1], rows[i]); switching = true; switchcount++; }} else if (switchcount == 0 && dir == "asc") {{ dir = "desc"; switching = true; }} }} headers[n].classList.add(dir == "asc" ? "sort-asc" : "sort-desc"); }}
  </script>
"""
    return render_base("基金概览 | WebUI", content, active_nav="overview").encode("utf-8")


def render_fund_detail_page(
    code: str,
    name: str,
    fund_info: Dict[str, Any],
    performance: Dict[str, str],
    holdings: List[Dict[str, str]],
    realtime_valuation: Dict[str, str],
    latest_analysis: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    渲染基金详情页面
    """
    info_html = "".join([f'<div class="task-detail-row"><span class="label">{k}</span><span>{v}</span></div>' 
                        for k, v in fund_info.items() if k not in ['基金代码', '基金名称', '基金简称']])
    
    # 实时估值卡片
    val_val = realtime_valuation.get("value", "-")
    val_style = "color: #ef4444;" if '+' in val_val else ("color: #10b981;" if '-' in val_val else "")
    valuation_html = f"""
    <div style="background: #fff; border: 1px solid var(--border); padding: 1.25rem; border-radius: 1rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-size: 0.85rem; color: var(--text-light); margin-bottom: 0.25rem;">实时估算收益率</div>
            <div style="font-size: 1.8rem; font-weight: 800; {val_style}">{val_val}</div>
        </div>
        <div style="text-align: right;">
            <div class="badge badge-info" style="margin-bottom: 0.4rem;">{realtime_valuation.get('source', '-')}</div>
            <div style="font-size: 0.75rem; color: var(--text-light);">更新时间: {realtime_valuation.get('time', '-')}</div>
        </div>
    </div>
    """

    # 持仓明细 HTML
    holding_rows = "".join([f'<tr><td>{h["name"]}</td><td><code class="code-badge">{h["code"]}</code></td><td style="text-align: right; font-weight: 600;">{h["ratio"]}</td></tr>' for h in holdings])
    holdings_html = f"""
    <div style="background: #fff; border: 1px solid var(--border); padding: 1.5rem; border-radius: 1rem; margin-bottom: 1.5rem;">
        <h3 style="margin-top: 0; font-size: 1.1rem; margin-bottom: 1rem;">📦 前十大重仓持仓</h3>
        <table class="mini-table">
            <thead><tr><th>资产名称</th><th>代码</th><th style="text-align: right;">持仓比例</th></tr></thead>
            <tbody>{holding_rows or '<tr><td colspan="3" style="text-align: center;">暂无持仓数据</td></tr>'}</tbody>
        </table>
        <p class="text-muted" style="margin-top: 0.75rem; font-size: 0.7rem;">注：持仓数据来源于基金季度报告，具有一定的滞后性。</p>
    </div>
    """

    # 阶段收益率 HTML
    perf_items = []
    periods = ['近一周', '近一月', '近三月', '近六月', '近一年', '近三年', '近五年', '成立来']
    for p in periods:
        val = performance.get(p, '-')
        style = "color: #ef4444;" if '+' in val else ("color: #10b981;" if '-' in val else "")
        perf_items.append(f'<div class="perf-item"><div class="perf-label">{p}</div><div class="perf-value" style="{style}">{val}</div></div>')
    
    analysis_html = ""
    if not latest_analysis:
        analysis_html = '<div class="task-hint">该基金暂无成功分析记录</div>'
    else:
        advice, score, created_at = latest_analysis.get('operation_advice', '-'), latest_analysis.get('sentiment_score', '-'), latest_analysis.get('created_at', '')
        if created_at:
            try: created_at = datetime.fromisoformat(created_at).strftime('%Y-%m-%d %H:%M')
            except: pass
        advice_class = "badge-info"
        if '买' in advice or '加仓' in advice: advice_class = "badge-success"
        elif '卖' in advice or '减仓' in advice: advice_class = "badge-error"
        elif '持有' in advice: advice_class = "badge-warning"
        summary = latest_analysis.get('analysis_summary', '')
        highlights = {'买入': '#dcfce7;#166534', '加仓': '#dcfce7;#166534', '卖出': '#fee2e2;#991b1b', '减仓': '#fee2e2;#991b1b', '风险': '#fef3c7;#92400e', '利好': '#dbeafe;#1e40af'}
        summary_html = html.escape(summary)
        for kw, style in highlights.items():
            bg, fg = style.split(';')
            summary_html = summary_html.replace(kw, f'<span style="background:{bg};color:{fg};font-weight:bold;padding:0 2px;border-radius:2px;">{kw}</span>')
        
        dashboard_html = render_dashboard_html(latest_analysis.get('raw_result', '{}'))
        analysis_html = f"""
        <div class="task-card completed" style="margin-bottom: 0.5rem; cursor: default;"><div class="task-status">✓</div><div class="task-main"><div class="task-title"><span class="name">最新分析研判报告</span></div><div class="task-meta"><span>⏱ {created_at}</span><span>{latest_analysis.get('trend_prediction', '-')}</span></div></div><div class="task-result"><span class="badge {advice_class}">{advice}</span><span class="task-score">{score}分</span></div></div>
        <div style="background: white; border: 1px solid var(--border); border-top: none; padding: 1.5rem; border-radius: 0 0 0.75rem 0.75rem;"><div class="summary-text">分析总结：</div><div style="margin-top: 0.5rem; line-height: 1.8;">{summary_html}</div>{dashboard_html}</div>
        """

    content = f"""
  <div class="container" style="max-width: 1000px;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem;"><div><h2 style="margin-bottom: 0.5rem;">{name}</h2><code class="code-badge" style="font-size: 1rem;">{code}</code></div><a href="/history?code={code}" class="btn btn-outline">查看全部历史记录 →</a></div>
    <div style="display: grid; grid-template-columns: 320px 1fr; gap: 2rem;"><div style="display: flex; flex-direction: column; gap: 1.5rem;"><div style="background: #f8fafc; padding: 1.5rem; border-radius: 1rem; border: 1px solid var(--border);"><h3 style="margin-top: 0; font-size: 1.1rem; margin-bottom: 1rem;">📋 基金档案</h3><div style="font-size: 0.85rem;">{info_html or '<div class="task-hint">暂无数据</div>'}</div></div><div style="background: #f8fafc; padding: 1.5rem; border-radius: 1rem; border: 1px solid var(--border);"><h3 style="margin-top: 0; font-size: 1.1rem; margin-bottom: 1rem;">📈 阶段收益</h3><div class="perf-grid">{"".join(perf_items)}</div></div></div><div>{valuation_html}{holdings_html}{analysis_html}</div></div>
    <div class="footer"><a href="/" style="color: var(--primary); text-decoration: none;">← 返回基金概览</a></div>
  </div>
"""
    return render_base(f"{name} 详情 | WebUI", content, active_nav="overview").encode("utf-8")


def render_history_page(
    history_records: List[Dict[str, Any]],
    total_count: int = 0,
    current_page: int = 1,
    limit: int = 20,
    filter_code: Optional[str] = None,
    filter_success: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> bytes:
    """
    渲染历史记录页面
    """
    if not history_records:
        history_html = '<div class="task-hint">暂无符合条件的分析记录</div>'
    else:
        rows = []
        for rec in history_records:
            is_success = rec.get('success', True)
            advice, score, created_at = rec.get('operation_advice', '-'), rec.get('sentiment_score', '-'), rec.get('created_at', '')
            if created_at:
                try: created_at = datetime.fromisoformat(created_at).strftime('%Y-%m-%d %H:%M')
                except: pass
            status_icon, status_class = ("✓", "completed") if is_success else ("✗", "failed")
            advice_class = "badge-info"
            if not is_success: advice_class, advice = "badge-error", "分析失败"
            elif '买' in advice or '加仓' in advice: advice_class = "badge-success"
            elif '卖' in advice or '减仓' in advice: advice_class = "badge-error"
            elif '持有' in advice: advice_class = "badge-warning"
            summary = rec.get('analysis_summary', '')
            highlights = {'买入': '#dcfce7;#166534', '加仓': '#dcfce7;#166534', '卖出': '#fee2e2;#991b1b', '减仓': '#fee2e2;#991b1b', '风险': '#fef3c7;#92400e', '利好': '#dbeafe;#1e40af'}
            summary_html = html.escape(summary)
            for kw, style in highlights.items():
                bg, fg = style.split(';')
                summary_html = summary_html.replace(kw, f'<span style="background:{bg};color:{fg};font-weight:bold;padding:0 2px;border-radius:2px;">{kw}</span>')
            dashboard_html = render_dashboard_html(rec.get('raw_result', '{}')) if is_success else f"<div class='highlight-box' style='background:#fee2e2;color:#991b1b;padding:0.75rem;border-radius:0.5rem;margin-top:0.5rem;'><strong>错误详情：</strong> {html.escape(summary)}</div>"
            rows.append(f'<div class="task-card {status_class}" style="margin-bottom: 0.5rem; cursor: pointer;" onclick="toggleHistoryDetail(\'{rec["id"]}\')"><div class="task-status">{status_icon}</div><div class="task-main"><div class="task-title"><span class="code">{rec.get("code", "-")}</span><span class="name">{rec.get("name", "-")}</span></div><div class="task-meta"><span>⏱ {created_at}</span><span>{rec.get("trend_prediction", "-")}</span></div></div><div class="task-result"><span class="badge {advice_class}">{advice}</span><span class="task-score">{score if is_success else "-"}分</span></div></div><div class="task-detail" id="hist_detail_{rec["id"]}" style="margin-bottom: 1rem; background: white; border: 1px solid var(--border); border-top: none; display: none; padding: 1rem; border-radius: 0 0 0.75rem 0.75rem;">{dashboard_html}</div>')
        history_html = "".join(rows)

    total_pages = (total_count + limit - 1) // limit
    pagination_html = ""
    if total_pages > 1:
        btns = []
        success_param = f"&success={str(filter_success).lower()}" if filter_success is not None else ""
        for p in range(max(1, current_page - 2), min(total_pages, current_page + 2) + 1):
            active = " active" if p == current_page else ""
            btns.append(f'<a href="/history?page={p}&code={filter_code or ""}{success_param}&sort_by={sort_by}&sort_order={sort_order}" class="page-btn{active}">{p}</a>')
        pagination_html = f'<div class="pagination">{"".join(btns)}</div>'

    success_val = ""
    if filter_success is True: success_val = "true"
    elif filter_success is False: success_val = "false"

    content = f"""
  <div class="container" style="max-width: 900px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;"><h2>📜 分析历史记录</h2><a href="/history" style="font-size: 0.8rem; color: var(--primary);">清除筛选</a></div>
    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 200px;"><label style="font-size: 0.75rem; color: var(--text-light);">按基金代码筛选</label><form action="/history" method="get" style="display: flex; gap: 0.5rem;"><input type="text" name="code" value="{filter_code or ''}" placeholder="输入代码..." class="search-box" style="margin-bottom: 0;"><input type="hidden" name="success" value="{success_val}"><button type="submit" class="btn btn-outline" style="padding: 0 1rem; height: 38px;">筛选</button></form></div>
        <div><label style="font-size: 0.75rem; color: var(--text-light);">分析状态</label><select onchange="location.href='/history?code={filter_code or ''}&sort_by={sort_by}&success='+this.value" class="report-select" style="height: 38px; min-width: 120px;"><option value="" { 'selected' if filter_success is None else '' }>全部</option><option value="true" { 'selected' if filter_success is True else '' }>成功</option><option value="false" { 'selected' if filter_success is False else '' }>失败</option></select></div>
        <div><label style="font-size: 0.75rem; color: var(--text-light);">排序方式</label><select onchange="location.href='/history?code={filter_code or ''}&success={success_val}&sort_by='+this.value" class="report-select" style="height: 38px; min-width: 120px;"><option value="created_at" { 'selected' if sort_by == 'created_at' else '' }>按时间</option><option value="sentiment_score" { 'selected' if sort_by == 'sentiment_score' else '' }>按评分</option><option value="code" { 'selected' if sort_by == 'code' else '' }>按代码</option></select></div>
    </div>
    <div class="task-list" style="max-height: none;">{history_html}</div>
    {pagination_html}
  </div>
  <script>function toggleHistoryDetail(id) {{ const d = document.getElementById('hist_detail_' + id); if (d) d.style.display = d.style.display === 'block' ? 'none' : 'block'; }}</script>
"""
    return render_base("分析历史 | WebUI", content, active_nav="history").encode("utf-8")


def render_market_review_list_page(
    history_records: List[Dict[str, Any]],
    total_count: int = 0,
    current_page: int = 1,
    limit: int = 10
) -> bytes:
    """
    渲染综合分析列表页面
    """
    rows = []
    for rec in history_records:
        created_at = rec.get('created_at', '')
        if created_at:
            try: created_at = datetime.fromisoformat(created_at).strftime('%Y-%m-%d %H:%M')
            except: pass
        summary = rec.get('analysis_summary', '')
        preview = summary[:150] + "..." if len(summary) > 150 else summary
        rows.append(f'<div class="task-card completed" style="margin-bottom: 1rem; cursor: pointer;" onclick="location.href=\'/market_review/detail?id={rec["id"]}\'"><div class="task-status">🎯</div><div class="task-main"><div class="task-title">持仓综合研判报告</div><div class="task-meta"><span>⏱ {created_at}</span></div><div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-light); line-height: 1.5;">{html.escape(preview)}</div></div><div style="flex-shrink: 0; color: var(--primary); font-size: 1.2rem;">→</div></div>')
    
    total_pages = (total_count + limit - 1) // limit
    pagination_html = ""
    if total_pages > 1:
        btns = "".join([f'<a href="/market_review?page={p}" class="page-btn{" active" if p == current_page else ""}">{p}</a>' for p in range(1, total_pages + 1)])
        pagination_html = f'<div class="pagination">{btns}</div>'

    content = f"""
  <div class="container" style="max-width: 900px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <h2>🎯 综合分析历史</h2>
        <button type="button" class="btn btn-success" onclick="confirmMarketReview()">🚀 开始新研判</button>
    </div>
    <div class="task-list">{"".join(rows) or '<div class="task-hint">暂无综合分析记录</div>'}</div>
    {pagination_html}
  </div>
  <script>
    function confirmMarketReview() {{
        if (confirm("确定要对当前持仓进行综合研判吗？\\n\\n建议在所有基金的单体分析完成后执行。")) {{
            window.location.href = '/market_review/run';
        }}
    }}
  </script>
"""
    return render_base("综合分析 | WebUI", content, active_nav="market").encode("utf-8")


def render_market_review_detail_page(
    record: Dict[str, Any]
) -> bytes:
    """
    渲染综合分析详情页面
    """
    created_at = record.get('created_at', '')
    if created_at:
        try: created_at = datetime.fromisoformat(created_at).strftime('%Y-%m-%d %H:%M:%S')
        except: pass
    report = record.get('analysis_summary', '')
    formatted_report = report.replace('\n', '<br>').replace('### ', '<h4>').replace('## ', '<h3>').replace('# ', '<h2>').replace('**', '<strong>')
    content = f'<div class="container" style="max-width: 900px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;"><h2>🎯 综合研判详情</h2><a href="/market_review" class="btn btn-outline">← 返回列表</a></div><div style="margin-bottom: 1rem; text-align: right; color: var(--text-light); font-size: 0.85rem;">生成时间: {created_at}</div><div class="task-detail show" style="background: white; border: 1px solid var(--border); padding: 2rem; line-height: 1.8; border-radius: 1rem;">{formatted_report}</div></div>'
    return render_base("综合分析详情 | WebUI", content, active_nav="market").encode("utf-8")


def render_config_page(
    stock_list: str,
    env_filename: str,
    message: Optional[str] = None
) -> bytes:
    """
    渲染配置页面
    """
    from src.config import get_config
    config = get_config()
    mask = lambda s: s[:4] + "*" * (len(s) - 8) + s[-4:] if s and len(s) > 10 else (s or "")
    gemini_key, email_pass = mask(config.gemini_api_key), mask(config.email_password)
    
    content = f"""
  <div class="container">
    <h2>⚙️ 系统配置管理</h2><p class="subtitle">管理基金列表、定时任务及 AI 核心密钥</p>
    <form method="post" action="/update">
      <div class="report-section" style="margin-top: 0; border-top: none; padding-top: 0;"><div class="report-section-title">📋 基金持仓配置</div><div class="form-group"><label for="stock_list">我的场外基金列表</label><textarea id="stock_list" name="stock_list" rows="5" placeholder="输入 6 位基金代码，逗号分隔">{html.escape(stock_list)}</textarea></div></div>
      <div class="report-section"><div class="report-section-title">⏰ 自动化与通知</div><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;"><div class="form-group"><label for="schedule_time">定时触发时间</label><input type="text" id="schedule_time" name="schedule_time" value="{config.schedule_time}" placeholder="HH:MM (留空则禁用自动触发)"></div><div class="form-group"><label for="email_sender">发件人邮箱</label><input type="text" id="email_sender" name="email_sender" value="{config.email_sender or ''}" placeholder="example@qq.com"></div></div><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;"><div class="form-group"><label for="email_password">邮箱授权码</label><input type="password" id="email_password" name="email_password" value="{email_pass}" placeholder="SMTP 授权码"></div><div class="form-group"><label for="email_receivers">收件人列表</label><input type="text" id="email_receivers" name="email_receivers" value="{','.join(config.email_receivers)}" placeholder="多个邮箱用逗号分隔"></div></div></div>
      <div class="report-section"><div class="report-section-title">🔑 AI 核心密钥</div><div class="form-group"><label for="gemini_key">Gemini API Key</label><input type="password" id="gemini_key" name="gemini_key" value="{gemini_key}" placeholder="AI 分析核心密钥"></div></div>
      <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border);"><button type="submit" class="btn btn-success" style="width: 100%; height: 3.5rem; font-size: 1.1rem;">💾 保存并应用所有配置</button></div>
    </form>
    <div class="footer"><p>当前环境文件: <code>{html.escape(env_filename)}</code></p></div>
  </div>
  {render_toast(message) if message else ""}
"""
    return render_base("配置管理 | WebUI", content, active_nav="config").encode("utf-8")


def render_system_status_page(
    tasks: List[Dict[str, Any]],
    health_data: Dict[str, Any]
) -> bytes:
    """
    渲染系统状态页面 (合并任务列表和健康检查)
    """
    task_rows = []
    for task in tasks:
        status, code = task.get('status', 'pending'), task.get('code', '-')
        result = task.get('result', {})
        name, start_time = result.get('name', code), task.get('start_time', '')
        if start_time:
            try: start_time = datetime.fromisoformat(start_time).strftime('%H:%M:%S')
            except: pass
        status_icon = '<span class="spinner"></span>' if status == "running" else ("✅" if status == "completed" else "❌")
        task_rows.append(f'<div class="task-card {status}" style="margin-bottom: 0.5rem;"><div class="task-status">{status_icon}</div><div class="task-main"><div class="task-title"><span class="code">{code}</span><span class="name">{name}</span></div><div class="task-meta"><span>⏱ {start_time}</span><span>状态: {status}</span></div></div></div>')
    
    content = f"""
  <div class="container" style="max-width: 900px;">
    <h2>🖥️ 系统运行状态</h2>
    <p class="subtitle">监控 Web 服务健康度及活跃分析任务</p>
    
    <div class="report-section" style="margin-top: 0; border-top: none; padding-top: 0;">
        <div class="report-section-title">💓 服务健康</div>
        <div class="task-card completed" style="margin-bottom: 1rem; cursor: default;">
            <div class="task-status">✓</div>
            <div class="task-main">
                <div class="task-title">Web 核心服务</div>
                <div class="task-meta">状态: {health_data.get('status', 'unknown')} | 时间: {health_data.get('timestamp', '-')}</div>
            </div>
        </div>
    </div>

    <div class="report-section">
        <div class="report-section-title">⏳ 活跃分析任务 (最近 50 条)</div>
        <div class="task-list">{"".join(task_rows) or '<div class="task-hint">当前无活跃任务</div>'}</div>
    </div>
    
    <div class="footer"><p>任务状态每 3 秒自动更新（需在首页查看）</p></div>
  </div>
"""
    return render_base("系统状态 | WebUI", content, active_nav="status").encode("utf-8")


def render_error_page(
    status_code: int,
    message: str,
    details: Optional[str] = None
) -> bytes:
    """
    渲染错误页面
    """
    details_html = f"<p class='text-muted'>{html.escape(details)}</p>" if details else ""
    content = f'<div class="container" style="text-align: center;"><h2>😵 {status_code}</h2><p>{html.escape(message)}</p>{details_html}<a href="/" class="btn btn-outline" style="margin-top: 1rem;">← 返回首页</a></div>'
    return render_base(f"错误 {status_code}", content).encode("utf-8")


def render_toast(message: str, toast_type: str = "success") -> str:
    """
    渲染 Toast 通知
    """
    icon = "✅" if toast_type == "success" else "❌"
    return f'<div id="toast" class="toast show"><span class="icon">{icon}</span> {html.escape(message)}</div><script>setTimeout(() => {{ document.getElementById("toast").classList.remove("show"); }}, 5000);</script>'
