# ⚖️ Bitcoin Net Liquidity & Supply Shock Agent

> **Institutional-grade Bitcoin on-chain volume & liquidity intelligence, democratized for everyday hardware.**  
> *Zero GPU. Zero Bloat. Under 25MB RAM. Runs silently on a 10-year-old Intel Core i7-4770, a Raspberry Pi, or a $3/month VPS.*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](#prerequisites)
[![Architecture: Zero-GPU](https://img.shields.io/badge/Architecture-Zero--GPU-orange.svg)](#hardware-democratization-manifesto)

---

## 📖 The Core Philosophy: "Volume & Liquidity Don't Lie"

Candlestick charts (K-lines) can be easily painted, manipulated, and faked by exchange market makers through wash trading and spoofing. Lagging technical indicators (EMA, SMA, RSI) are mathematically delayed derivatives of past price points.

**On-chain supply and UTXO transitions cannot be forged.**

This Agent constructs a continuous **On-Chain Net Liquidity Balance Sheet**, tracking two immutable physical forces on the Bitcoin blockchain:
1. **The Absorption Stream (Inflow to Cold Vaults)**: Measures floating coins being systematically bought and locked into Long-Term Holder (LTH, >155 days) cold storage.
2. **The Awakening Stream (Dormant Coin Spending)**: Monitors ancient, dormant supply (>1-5 years) waking up and moving toward exchanges.
3. **The Net Supply Shift ($\Delta \text{Net}$)**:
   $$\text{Net Supply Balance} = \text{Cold Vault Absorption} - \text{Dormant Supply Awakening}$$

When this net balance skews heavily positive, a **Supply Squeeze** is statistically imminent regardless of short-term chart noise.

---

## 🏛️ Hardware Democratization Manifesto

Most modern institutional trading bots require heavy multi-gigabyte pandas/torch dependencies, continuous cloud bills, and expensive data subscriptions ($800+/month from commercial analytics vendors).

This project proves that **institutional-grade intelligence can be democratized**:
* **Pure Native Standard Library + `aiohttp`**: Zero heavy analytics dependencies.
* **Minimal Footprint**: Operates under **25MB of RAM** and **0% CPU** during background standby.
* **Zero Fan Noise**: Designed to run quietly on decommissioned office hardware (e.g., Haswell i7-4770 without chassis fans).

---

## ⚡ Tri-Modal Execution Architecture

1. **Bootstrapping Instant Dispatch**:
   * Dispatches an instant intelligence report within 3 seconds of launching the script (perfect for users who turn off their workstations at night).
2. **Scheduled 09:00 AM Daily Briefing**:
   * Stays in an ultra-low-power asynchronous standby and pushes a morning briefing every day at 09:00 AM local time.
3. **15-Minute Intraday Watchdog Sentinel**:
   * Silently wakes up for 0.3 seconds every 15 minutes to probe the live mempool and UTXO age buckets.
   * **Instant Emergency Interruption**: If a sudden ancient dormant supply dump (e.g., >1,200 BTC) or a mempool congestion tsunami occurs, it breaks standby immediately and fires an emergency alert to Telegram (with a 90-minute anti-spam cooldown).

---

## 🚀 Quick Start

### 1. Prerequisites
* Python 3.9 or higher
* `aiohttp` library

```bash
pip install aiohttp
```

### 2. Configuration
Set your Telegram Bot Token and Chat ID as environment variables, or edit the placeholders directly in `net_liquidity_agent.py`:

```bash
# Linux / macOS
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

# Windows (Command Prompt)
set TELEGRAM_BOT_TOKEN=your_bot_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here
```

*(Alternatively, open `net_liquidity_agent.py` and replace `YOUR_TELEGRAM_BOT_TOKEN_HERE` and `YOUR_TELEGRAM_CHAT_ID_HERE` with your credentials).*

### 3. Run the Agent

**On Windows:**
Double-click `start_agent.bat` or run:
```cmd
python net_liquidity_agent.py
```

**On Linux / VPS / Raspberry Pi:**
```bash
python3 net_liquidity_agent.py
```

---

## 📱 Telegram Report Previews

### Regular Daily / Boot Briefing
```text
⚖️ [BTC ON-CHAIN TRUE LIQUIDITY & SUPPLY BALANCE]
📌 Trigger: 🟢 [Agent Boot / Instant Ready Report]
🗓 Cycle: 2026-11-12 (UTC) | Price: $73,700
━━━━━━━━━━━━━━━━━━━━━━

🎯 1. Supply Shock Status:
🟡 [NEUTRAL INVENTORY CHURN / CONSOLIDATION]
Equilibrium state (Net shift: +320.26 BTC). Neither aggressive panic distribution nor institutional hoarding.

🌊 2. Strong-Hand Vault Absorption (Illiquidity):
• LTH Total Vaulted Supply: 16,273,197.1 BTC (80.9% of Network)
• 24h Cold Vault Inflow: +790.2 BTC
• Key Accumulation Anchors:
  • $65,000 bin: locked +605.8 BTC
  • $65,500 bin: locked +184.4 BTC

🩸 3. Ancient Supply Release (Dormant Awakening):
• 24h Dormant Coins Spent: -470.0 BTC
• Primary Awakening Price Bins:
  • $58,000 bin: awakened -159.1 BTC
  • $66,500 bin: awakened -125.6 BTC

⚡ 4. Net Balance Dynamics (True Net Shift):
• Daily Net Supply Shift: +320.3 BTC
• 7-Day Cumulative LTH Shift: +105.3 BTC
• Speculative Floating Supply (STH): 3,837,572.8 BTC

⏳ 5. Real-Time Mempool Queue:
• Unconfirmed Tx Count: 57,084 txs | Congestion Size: 29.33 MB
━━━━━━━━━━━━━━━━━━━━━━
🤖 Generated by Net Liquidity Agent (Hardware Democratization Project)
```

### Intraday Emergency Watchdog Alert
```text
⚖️ [BTC ON-CHAIN TRUE LIQUIDITY & SUPPLY BALANCE]
📌 Trigger: 🚨 [Intraday Watchdog Anomaly Alert]
🗓 Cycle: 2026-11-12 (UTC) | Price: $72,400
━━━━━━━━━━━━━━━━━━━━━━
⚠️ [WATCHDOG ANOMALY TRIGGER]:
🚨 Massive ancient dormant supply dump detected! Intraday outflow reached -1,850.4 BTC (exceeded 1,200 threshold)!
━━━━━━━━━━━━━━━━━━━━━━

🎯 1. Supply Shock Status:
🔴 [DORMANT SUPPLY SOFTENING / SUPPLY RELEASE]
Moderate outflow from older wallets. Trapped high-tier coins moving to exchanges. Absorption needed.
...
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```