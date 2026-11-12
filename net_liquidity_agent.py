#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
Project: Bitcoin Net Liquidity & Supply Shock Agent
Philosophy: Hardware Democratization (Institutional Intelligence on Old Hardware)
Target Hardware: Intel Core i7-4770 / 8GB RAM / Zero GPU / Under 25MB RAM / Fanless
Architecture:
  1. Bootstrapping Instant Dispatch (Instant intelligence within 3 seconds of boot)
  2. Scheduled Daily 09:00 AM Intelligence Briefing
  3. 15-Minute Intraday Watchdog (Real-time alert on dormant dump / vault squeeze / mempool spike)
License: MIT License
===============================================================================
"""

import sys
import os

# Auto-configure Windows CMD console to UTF-8
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")

import json
import sqlite3
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional, Any

# =====================================================================
# 0. Global Configuration (Sanitized for GitHub - Environment Driven)
# =====================================================================
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID_HERE")
DB_PATH: str = os.getenv("DB_PATH", "liquidity_metrics.db")

# --- Intraday Watchdog Anomaly Thresholds ---
WATCHDOG_INTERVAL_MINUTES: int = 15       # Inspection interval in minutes
ALERT_AWAKENING_THRESHOLD: float = 1200.0  # Dormant supply dump alert threshold (BTC)
ALERT_ABSORPTION_THRESHOLD: float = 2500.0 # Cold vault absorption squeeze threshold (BTC)
ALERT_MEMPOOL_TX_THRESHOLD: int = 120000  # Mempool queue congestion alert threshold (txs)
ALERT_COOLDOWN_MINUTES: int = 90          # Cooldown to prevent spamming notifications


# =====================================================================
# 1. Memory-Constrained Entity Models (__slots__ eliminates __dict__ bloat)
# =====================================================================
class PriceBucket:
    __slots__ = ('price', 'supply')
    def __init__(self, price: float, supply: float) -> None:
        self.price = price
        self.supply = supply


class SupplyBalanceReport:
    __slots__ = (
        'date_str', 'btc_price', 'lth_total', 'sth_total', 'all_total',
        'lth_ratio', 'lth_delta_1d', 'lth_delta_7d', 'awakening_vol',
        'absorption_vol', 'net_supply_shift', 'sentiment_status',
        'sentiment_desc', 'top_awakened_bins', 'top_locked_bins',
        'mempool_tx_count', 'mempool_vsize_mb'
    )
    def __init__(
        self, date_str: str, btc_price: float, lth_total: float, sth_total: float,
        all_total: float, lth_ratio: float, lth_delta_1d: float, lth_delta_7d: float,
        awakening_vol: float, absorption_vol: float, net_supply_shift: float,
        sentiment_status: str, sentiment_desc: str,
        top_awakened_bins: List[Tuple[float, float]],
        top_locked_bins: List[Tuple[float, float]],
        mempool_tx_count: int, mempool_vsize_mb: float
    ) -> None:
        self.date_str = date_str
        self.btc_price = btc_price
        self.lth_total = lth_total
        self.sth_total = sth_total
        self.all_total = all_total
        self.lth_ratio = lth_ratio
        self.lth_delta_1d = lth_delta_1d
        self.lth_delta_7d = lth_delta_7d
        self.awakening_vol = awakening_vol
        self.absorption_vol = absorption_vol
        self.net_supply_shift = net_supply_shift
        self.sentiment_status = sentiment_status
        self.sentiment_desc = sentiment_desc
        self.top_awakened_bins = top_awakened_bins
        self.top_locked_bins = top_locked_bins
        self.mempool_tx_count = mempool_tx_count
        self.mempool_vsize_mb = mempool_vsize_mb


# =====================================================================
# 2. SQLite Native Persistence Layer (WAL High-Performance Mode)
# =====================================================================
class LiquidityStorage:
    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lth_snapshots (
                    date_str TEXT NOT NULL,
                    price_bin REAL NOT NULL,
                    supply REAL NOT NULL,
                    PRIMARY KEY (date_str, price_bin)
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_liquidity_summary (
                    date_str TEXT PRIMARY KEY,
                    btc_price REAL,
                    lth_total REAL,
                    sth_total REAL,
                    net_shift REAL,
                    awakening_vol REAL,
                    absorption_vol REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def save_lth_buckets(self, date_str: str, buckets: List[PriceBucket]) -> None:
        if not buckets:
            return
        records = [(date_str, b.price, b.supply) for b in buckets]
        with self._get_connection() as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO lth_snapshots (date_str, price_bin, supply)
                VALUES (?, ?, ?);
            """, records)
            conn.commit()

    def load_lth_snapshot(self, date_str: str) -> Dict[float, float]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT price_bin, supply FROM lth_snapshots WHERE date_str = ?;", (date_str,))
            return {r[0]: r[1] for r in cur.fetchall()}

    def save_daily_summary(self, rep: SupplyBalanceReport) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO daily_liquidity_summary 
                (date_str, btc_price, lth_total, sth_total, net_shift, awakening_vol, absorption_vol)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (rep.date_str, rep.btc_price, rep.lth_total, rep.sth_total, 
                  rep.net_supply_shift, rep.awakening_vol, rep.absorption_vol))
            conn.commit()

    def get_past_lth_total(self, days_ago: int, ref_date: datetime) -> Optional[float]:
        target_date = (ref_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT lth_total FROM daily_liquidity_summary WHERE date_str = ?;", (target_date,))
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute("SELECT SUM(supply) FROM lth_snapshots WHERE date_str = ?;", (target_date,))
            row_sum = cur.fetchone()
            return row_sum[0] if (row_sum and row_sum[0] is not None) else None


# =====================================================================
# 3. Streamlined Asynchronous Data Fetcher
# =====================================================================
class BitviewLiquidityFetcher:
    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }

    async def fetch_lth_urpd(self, date_str: Optional[str] = None) -> List[PriceBucket]:
        import aiohttp
        endpoint = (
            f"https://bitview.space/api/urpd/lth/{date_str}?agg=lin500&weight=none"
            if date_str
            else "https://bitview.space/api/urpd/lth?agg=lin500&weight=none"
        )
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
            try:
                async with session.get(endpoint) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json(content_type=None)
                    return self._parse_bitview_json(data, default_step=500.0)
            except Exception as e:
                sys.stderr.write(f"[-] LTH fetch failed ({endpoint}): {e}\n")
                return []

    async def fetch_all_urpd_sum(self, date_str: Optional[str] = None) -> float:
        import aiohttp
        endpoint = (
            f"https://bitview.space/api/urpd/all/{date_str}?agg=lin500&weight=none"
            if date_str
            else "https://bitview.space/api/urpd/all?agg=lin500&weight=none"
        )
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
            try:
                async with session.get(endpoint) as resp:
                    if resp.status != 200:
                        return 19_800_000.0
                    data = await resp.json(content_type=None)
                    buckets = self._parse_bitview_json(data, default_step=500.0)
                    return sum(b.supply for b in buckets) if buckets else 19_800_000.0
            except Exception:
                return 19_800_000.0

    async def fetch_mempool_and_price(self) -> Tuple[float, int, float]:
        import aiohttp
        price = 0.0
        tx_count = 0
        vsize_mb = 0.0
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
            try:
                async with session.get("https://bitview.space/api/mempool/price") as resp:
                    if resp.status == 200:
                        p_data = await resp.json(content_type=None)
                        if isinstance(p_data, dict):
                            price = float(p_data.get("price", p_data.get("USD", 0.0)))
                        elif isinstance(p_data, (int, float)):
                            price = float(p_data)
            except Exception:
                price = 0.0

            try:
                async with session.get("https://bitview.space/api/mempool") as resp:
                    if resp.status == 200:
                        m_data = await resp.json(content_type=None)
                        tx_count = int(m_data.get("count", 0))
                        vsize = float(m_data.get("vsize", 0.0))
                        vsize_mb = round(vsize / (1024 * 1024), 2)
            except Exception:
                pass

        return price, tx_count, vsize_mb

    def _parse_bitview_json(self, raw_data: Any, default_step: float = 500.0) -> List[PriceBucket]:
        if not raw_data:
            return []

        def _extract(node: Any) -> Optional[List[PriceBucket]]:
            if not node:
                return None

            if isinstance(node, dict):
                if "columns" in node and "data" in node and isinstance(node["data"], list):
                    cols = [str(c).lower() for c in node["columns"]]
                    p_idx = next((cols.index(k) for k in ("price", "price_floor", "prices", "bin", "bins") if k in cols), -1)
                    s_idx = next((cols.index(k) for k in ("supply", "supplies", "volume", "amount") if k in cols), -1)
                    if p_idx != -1 and s_idx != -1:
                        res = []
                        for row in node["data"]:
                            if isinstance(row, (list, tuple)) and len(row) > max(p_idx, s_idx):
                                try:
                                    res.append(PriceBucket(float(row[p_idx]), float(row[s_idx])))
                                except (ValueError, TypeError):
                                    continue
                        if res:
                            return res

                p_key = next((k for k in ("price", "price_floor", "prices", "bin", "bins", "p") if k in node and isinstance(node[k], list)), None)
                s_key = next((k for k in ("supply", "supplies", "volume", "volumes", "v", "amount") if k in node and isinstance(node[k], list)), None)
                if p_key and s_key:
                    prices = node[p_key]
                    supplies = node[s_key]
                    res = []
                    for p, s in zip(prices, supplies):
                        if p is not None and s is not None:
                            try:
                                res.append(PriceBucket(float(p), float(s)))
                            except (ValueError, TypeError):
                                continue
                    if res:
                        return res

                if s_key and not p_key:
                    supplies = node[s_key]
                    res = []
                    for idx, s in enumerate(supplies):
                        if s is not None:
                            try:
                                res.append(PriceBucket(float(idx * default_step), float(s)))
                            except (ValueError, TypeError):
                                continue
                    if res:
                        return res

                is_kv = True
                kv_res = []
                for k, v in node.items():
                    if isinstance(v, (dict, list)):
                        is_kv = False
                        break
                    try:
                        kv_res.append(PriceBucket(float(k), float(v)))
                    except (ValueError, TypeError):
                        is_kv = False
                        break
                if is_kv and kv_res:
                    return kv_res

                for sub_key in ("buckets", "data", "urpd", "result", "distribution", "items"):
                    if sub_key in node and isinstance(node[sub_key], (dict, list)):
                        sub_res = _extract(node[sub_key])
                        if sub_res:
                            return sub_res

            elif isinstance(node, list):
                if not node:
                    return None
                first = node[0]
                if isinstance(first, dict):
                    res = []
                    for r in node:
                        p = next((r[k] for k in ("price", "price_floor", "bin", "prices", "p") if k in r), None)
                        s = next((r[k] for k in ("supply", "supplies", "volume", "v", "amount") if k in r), None)
                        if p is not None and s is not None:
                            try:
                                res.append(PriceBucket(float(p), float(s)))
                            except (ValueError, TypeError):
                                continue
                    if res:
                        return res
                elif isinstance(first, (list, tuple)) and len(first) >= 2:
                    res = []
                    for r in node:
                        try:
                            res.append(PriceBucket(float(r[0]), float(r[1])))
                        except (ValueError, TypeError):
                            continue
                    if res:
                        return res
                elif isinstance(first, (int, float)):
                    res = []
                    for idx, s in enumerate(node):
                        try:
                            res.append(PriceBucket(float(idx * default_step), float(s)))
                        except (ValueError, TypeError):
                            continue
                    if res:
                        return res

            return None

        parsed = _extract(raw_data)
        return parsed if parsed else []


# =====================================================================
# 4. Quantitative Balance Sheet Computation Engine
# =====================================================================
class LiquidityShockEngine:
    @staticmethod
    def evaluate(
        date_str: str,
        btc_price: float,
        snap_prev: Dict[float, float],
        snap_curr: Dict[float, float],
        all_supply_total: float,
        lth_7d_total: Optional[float],
        mempool_tx: int,
        mempool_vsize: float
    ) -> SupplyBalanceReport:
        all_bins = sorted(set(snap_prev.keys()).union(set(snap_curr.keys())))
        
        lth_curr_total = sum(snap_curr.values())
        lth_prev_total = sum(snap_prev.values())
        sth_curr_total = max(0.0, all_supply_total - lth_curr_total)
        lth_ratio = (lth_curr_total / all_supply_total * 100) if all_supply_total > 0 else 0.0

        lth_delta_1d = lth_curr_total - lth_prev_total
        lth_delta_7d = (lth_curr_total - lth_7d_total) if (lth_7d_total and lth_7d_total > 0) else lth_delta_1d

        awakened_list: List[Tuple[float, float]] = []
        locked_list: List[Tuple[float, float]] = []

        for p in all_bins:
            v_prev = snap_prev.get(p, 0.0)
            v_curr = snap_curr.get(p, 0.0)
            diff = v_curr - v_prev
            if diff < -10.0:
                awakened_list.append((p, abs(diff)))
            elif diff > 10.0:
                locked_list.append((p, diff))

        awakening_vol = sum(vol for _, vol in awakened_list)
        absorption_vol = sum(vol for _, vol in locked_list)
        net_supply_shift = absorption_vol - awakening_vol

        awakened_list.sort(key=lambda x: x[1], reverse=True)
        locked_list.sort(key=lambda x: x[1], reverse=True)

        if net_supply_shift >= 3000.0:
            status = "🟢 [EXTREME SUPPLY SHOCK / SQUEEZE LOADING]"
            desc = (
                f"Net strong-hand absorption of +{net_supply_shift:,.2f} BTC in 24h! "
                "Ancient supply remains diamond-handed while circulating coins are aggressively locked into cold vaults. "
                "Severe liquidity squeeze imminent."
            )
        elif net_supply_shift >= 500.0:
            status = "🟢 [HEALTHY STRONG-HAND LOCKUP / SUPPLY TIGHTENING]"
            desc = (
                f"Net positive absorption (+{net_supply_shift:,.2f} BTC). "
                "Long-Term Holders are steadily absorbing floating supply at key structural support levels."
            )
        elif net_supply_shift <= -3000.0:
            status = "🔴 [MAJOR DORMANT SUPPLY AWAKENING / DUMP ALERT]"
            desc = (
                f"Significant ancient supply movement detected (-{abs(net_supply_shift):,.2f} BTC)! "
                "Long-Term Holders are actively waking up and liquidating older UTXOs. Exercise caution against cascading sell-offs."
            )
        elif net_supply_shift <= -500.0:
            status = "🔴 [DORMANT SUPPLY SOFTENING / SUPPLY RELEASE]"
            desc = (
                f"Moderate outflow from older wallets (-{abs(net_supply_shift):,.2f} BTC). "
                "Earlier profit-takers or trapped high-tier coins are moving to exchanges. Absorption needed."
            )
        else:
            status = "🟡 [NEUTRAL INVENTORY CHURN / CONSOLIDATION]"
            desc = (
                f"Equilibrium state (Net shift: {net_supply_shift:+,.2f} BTC). "
                "Neither aggressive panic distribution nor institutional hoarding. Range-bound price discovery."
            )

        return SupplyBalanceReport(
            date_str=date_str,
            btc_price=btc_price,
            lth_total=lth_curr_total,
            sth_total=sth_curr_total,
            all_total=all_supply_total,
            lth_ratio=lth_ratio,
            lth_delta_1d=lth_delta_1d,
            lth_delta_7d=lth_delta_7d,
            awakening_vol=awakening_vol,
            absorption_vol=absorption_vol,
            net_supply_shift=net_supply_shift,
            sentiment_status=status,
            sentiment_desc=desc,
            top_awakened_bins=awakened_list[:3],
            top_locked_bins=locked_list[:3],
            mempool_tx_count=mempool_tx,
            mempool_vsize_mb=mempool_vsize
        )


# =====================================================================
# 5. Telegram Tactical Notification Dispatcher
# =====================================================================
class TelegramReporter:
    @classmethod
    async def push_balance_sheet(cls, rep: SupplyBalanceReport, trigger_mode: str = "boot", alert_reason: str = "") -> bool:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or "YOUR_TELEGRAM" in TELEGRAM_BOT_TOKEN:
            print("[!] Telegram credentials not configured or using placeholders. Skipping dispatch.")
            return False

        if trigger_mode == "boot":
            header_title = "🟢 [Agent Boot / Instant Ready Report]"
        elif trigger_mode == "daily":
            header_title = "🌅 [Daily 09:00 AM Intelligence Briefing]"
        else:
            header_title = "🚨 [Intraday Watchdog Anomaly Alert]"

        price_line = f"${rep.btc_price:,.0f}" if rep.btc_price > 0 else "Fetching..."

        awakened_txt = ""
        if rep.top_awakened_bins:
            for p, v in rep.top_awakened_bins:
                awakened_txt += f"  • <code>${p:,.0f}</code> bin: awakened <b>-{v:,.1f} BTC</b>\n"
        else:
            awakened_txt = "  • No significant dormant spending detected\n"

        locked_txt = ""
        if rep.top_locked_bins:
            for p, v in rep.top_locked_bins:
                locked_txt += f"  • <code>${p:,.0f}</code> bin: locked <b>+{v:,.1f} BTC</b>\n"
        else:
            locked_txt = "  • No concentrated absorption node\n"

        alert_banner = ""
        if alert_reason:
            alert_banner = (
                f"⚠️ <b>[WATCHDOG ANOMALY TRIGGER]:</b>\n"
                f"<b>{alert_reason}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
            )

        msg = (
            f"⚖️ <b>[BTC ON-CHAIN TRUE LIQUIDITY & SUPPLY BALANCE]</b>\n"
            f"📌 <b>Trigger:</b> <code>{header_title}</code>\n"
            f"🗓 <b>Cycle:</b> <code>{rep.date_str} (UTC)</code> | Price: <b>{price_line}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{alert_banner}"
            f"🎯 <b>1. Supply Shock Status:</b>\n"
            f"<b>{rep.sentiment_status}</b>\n"
            f"<i>{rep.sentiment_desc}</i>\n\n"
            f"🌊 <b>2. Strong-Hand Vault Absorption (Illiquidity):</b>\n"
            f"• LTH Total Vaulted Supply: <code>{rep.lth_total:,.1f} BTC</code> (<b>{rep.lth_ratio:.1f}%</b> of Network)\n"
            f"• 24h Cold Vault Inflow: <code>+{rep.absorption_vol:,.1f} BTC</code>\n"
            f"• Key Accumulation Anchors:\n{locked_txt}\n"
            f"🩸 <b>3. Ancient Supply Release (Dormant Awakening):</b>\n"
            f"• 24h Dormant Coins Spent: <code>-{rep.awakening_vol:,.1f} BTC</code>\n"
            f"• Primary Awakening Price Bins:\n{awakened_txt}\n"
            f"⚡ <b>4. Net Balance Dynamics (True Net Shift):</b>\n"
            f"• Daily Net Supply Shift: <code>{rep.net_supply_shift:+,.1f} BTC</code>\n"
            f"• 7-Day Cumulative LTH Shift: <code>{rep.lth_delta_7d:+,.1f} BTC</code>\n"
            f"• Speculative Floating Supply (STH): <code>{rep.sth_total:,.1f} BTC</code>\n\n"
            f"⏳ <b>5. Real-Time Mempool Queue:</b>\n"
            f"• Unconfirmed Tx Count: <code>{rep.mempool_tx_count:,} txs</code> | Congestion Size: <code>{rep.mempool_vsize_mb} MB</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>🤖 Generated by Net Liquidity Agent (Hardware Democratization Project)</i>"
        )

        import aiohttp
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=15) as resp:
                    if resp.status == 200:
                        print(f"[+] Telegram [{header_title}] dispatched successfully!")
                        return True
                    else:
                        print(f"[-] Telegram dispatch failed [HTTP {resp.status}]")
                        return False
        except Exception as e:
            print(f"[-] Telegram network error: {e}")
            return False


# =====================================================================
# 6. One-Shot Inspection Task Core
# =====================================================================
async def execute_inspection(trigger_mode: str = "boot", alert_reason: str = "") -> Optional[SupplyBalanceReport]:
    storage = LiquidityStorage(DB_PATH)
    fetcher = BitviewLiquidityFetcher()

    now_utc = datetime.now(timezone.utc)
    t_curr_str = now_utc.strftime("%Y-%m-%d")
    t_prev_str = (now_utc - timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. Load or fetch T-1
    snap_prev = storage.load_lth_snapshot(t_prev_str)
    if not snap_prev:
        buckets_prev = await fetcher.fetch_lth_urpd(t_prev_str)
        if buckets_prev:
            storage.save_lth_buckets(t_prev_str, buckets_prev)
            snap_prev = {b.price: b.supply for b in buckets_prev}

    # 2. Load or fetch T
    buckets_curr = await fetcher.fetch_lth_urpd(None)
    if not buckets_curr:
        buckets_curr = await fetcher.fetch_lth_urpd(t_curr_str)

    eval_date_str = t_curr_str
    if not buckets_curr:
        t_prev_2_str = (now_utc - timedelta(days=2)).strftime("%Y-%m-%d")
        buckets_prev2 = await fetcher.fetch_lth_urpd(t_prev_2_str)
        if buckets_prev2:
            storage.save_lth_buckets(t_prev_2_str, buckets_prev2)
            snap_prev = {b.price: b.supply for b in buckets_prev2}
        snap_curr = snap_prev
        eval_date_str = t_prev_str
    else:
        storage.save_lth_buckets(t_curr_str, buckets_curr)
        snap_curr = {b.price: b.supply for b in buckets_curr}

    if not snap_prev:
        snap_prev = snap_curr

    # 3. Supplemental metrics
    all_supply_total = await fetcher.fetch_all_urpd_sum(eval_date_str)
    btc_price, mp_tx, mp_vsize = await fetcher.fetch_mempool_and_price()
    lth_7d_total = storage.get_past_lth_total(7, now_utc)

    # 4. Engine evaluation
    report = LiquidityShockEngine.evaluate(
        date_str=eval_date_str,
        btc_price=btc_price,
        snap_prev=snap_prev,
        snap_curr=snap_curr,
        all_supply_total=all_supply_total,
        lth_7d_total=lth_7d_total,
        mempool_tx=mp_tx,
        mempool_vsize=mp_vsize
    )

    storage.save_daily_summary(report)

    # 5. Terminal CLI Dashboard
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Settlement: Price ${report.btc_price:,.0f} | Net: {report.net_supply_shift:+,.1f} BTC | Dormant Outflow: -{report.awakening_vol:,.1f} BTC | Mempool: {report.mempool_tx_count:,} txs")

    # 6. Telegram Dispatch
    await TelegramReporter.push_balance_sheet(report, trigger_mode=trigger_mode, alert_reason=alert_reason)
    return report


# =====================================================================
# 7. Intraday Watchdog Probe Engine
# =====================================================================
async def run_watchdog_probe(last_alert_time: Optional[datetime]) -> Tuple[Optional[datetime], bool]:
    """Lightweight 15-minute probe, fires emergency alert if anomalies exceed thresholds"""
    now = datetime.now()
    fetcher = BitviewLiquidityFetcher()
    storage = LiquidityStorage(DB_PATH)

    now_utc = datetime.now(timezone.utc)
    t_prev_str = (now_utc - timedelta(days=1)).strftime("%Y-%m-%d")

    snap_prev = storage.load_lth_snapshot(t_prev_str)
    if not snap_prev:
        return last_alert_time, False

    buckets_curr = await fetcher.fetch_lth_urpd(None)
    btc_price, mp_tx, mp_vsize = await fetcher.fetch_mempool_and_price()

    if not buckets_curr:
        return last_alert_time, False

    snap_curr = {b.price: b.supply for b in buckets_curr}

    awakening = sum(abs(snap_curr[p] - snap_prev[p]) for p in snap_curr if p in snap_prev and (snap_curr[p] - snap_prev[p]) < -10.0)
    absorption = sum((snap_curr[p] - snap_prev[p]) for p in snap_curr if p in snap_prev and (snap_curr[p] - snap_prev[p]) > 10.0)
    net_shift = absorption - awakening

    trigger_reason = ""
    if awakening >= ALERT_AWAKENING_THRESHOLD:
        trigger_reason = f"🚨 Massive ancient dormant supply dump detected! Intraday outflow reached -{awakening:,.1f} BTC (exceeded {ALERT_AWAKENING_THRESHOLD:,.0f} threshold)!"
    elif absorption >= ALERT_ABSORPTION_THRESHOLD:
        trigger_reason = f"🟢 Strong-hand vault squeeze detected! Intraday cold vault lockup reached +{absorption:,.1f} BTC (exceeded {ALERT_ABSORPTION_THRESHOLD:,.0f} threshold)!"
    elif mp_tx >= ALERT_MEMPOOL_TX_THRESHOLD:
        trigger_reason = f"⏳ Mempool congestion spike detected! Unconfirmed queue surged to {mp_tx:,} txs (exceeded {ALERT_MEMPOOL_TX_THRESHOLD:,} threshold)!"

    if trigger_reason:
        in_cooldown = False
        if last_alert_time:
            time_diff = (now - last_alert_time).total_seconds() / 60.0
            if time_diff < ALERT_COOLDOWN_MINUTES:
                in_cooldown = True

        if not in_cooldown:
            print(f"\n[🚨 Watchdog Anomaly Triggered] {trigger_reason}")
            await execute_inspection(trigger_mode="watchdog", alert_reason=trigger_reason)
            return now, True
        else:
            print(f"[*] Anomaly detected but currently in cooldown ({time_diff:.1f}/{ALERT_COOLDOWN_MINUTES} mins), standing guard...")

    else:
        print(f"[🛡️ Watchdog {now.strftime('%H:%M')}] Equilibrium normal (Net: {net_shift:+,.1f} BTC, Dormant: -{awakening:,.1f} BTC, Mempool: {mp_tx:,} txs) | Standing guard...")

    return last_alert_time, False


# =====================================================================
# 8. Tri-Modal Execution Lifecycle Scheduler
# =====================================================================
async def main_scheduler():
    print("=" * 72)
    print("🚀 BTC Net Liquidity & Supply Shock Agent [Watchdog Enhanced] Initialized")
    print(f"💡 Architecture: Boot Dispatch -> Daily 09:00 AM Briefing -> {WATCHDOG_INTERVAL_MINUTES}-Min Intraday Watchdog")
    print("=" * 72)

    # Trigger 1: Instant boot dispatch
    await execute_inspection(trigger_mode="boot")

    last_watchdog_alert: Optional[datetime] = None
    last_probe_minute: int = -1

    while True:
        now_local = datetime.now()

        # Trigger 2: Scheduled daily 09:00 AM local time briefing
        if now_local.hour == 9 and now_local.minute == 0:
            print(f"\n[⏰] 09:00 AM trigger fired! Executing scheduled daily briefing...")
            await execute_inspection(trigger_mode="daily")
            await asyncio.sleep(70)  # Prevent double trigger in the same minute
            continue

        # Trigger 3: 15-minute intraday watchdog probe
        if now_local.minute % WATCHDOG_INTERVAL_MINUTES == 0 and now_local.minute != last_probe_minute:
            last_probe_minute = now_local.minute
            last_watchdog_alert, _ = await run_watchdog_probe(last_watchdog_alert)

        # Ultra-lightweight asynchronous sleep (0.00% CPU overhead)
        await asyncio.sleep(30)


if __name__ == "__main__":
    try:
        asyncio.run(main_scheduler())
    except (KeyboardInterrupt, SystemExit):
        print("\n[*] Agent gracefully exited.")
        sys.exit(0)