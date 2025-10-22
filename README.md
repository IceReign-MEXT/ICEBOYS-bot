# 🔥 ICEBOYS-bot: Automated Crypto Sniping and Wallet Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Deployed](https://img.shields.io/badge/Status-LIVE-brightgreen.svg)]()
[![Built with Python](https://img.shields.io/badge/Built%20with-Python-blue.svg)](https://www.python.org/)

## 🚀 The ICEBOYS Advantage

The **ICEBOYS-bot** provides a critical advantage in the fast-paced DeFi and token market. Built as a stable, 24/7 Telegram service, it monitors blockchain activity to deliver **premium, real-time wallet alerts and market intelligence** directly to subscribers.

**Goal:** Turn slow public data into rapid, actionable alpha for traders.

## 🌟 Key Features

*   **⚡️ Automated Webhook Deployment:** Stable, 24/7 uptime using Render Webhooks and Docker.
*   **💳 Instant Subscription Verification:** Uses **Alchemy** and **Web3** to instantly check a subscriber's wallet balance (e.g., 0.01 ETH) for immediate premium access.
*   **💾 PostgreSQL Persistence:** Uses Render's managed PostgreSQL database for reliable, high-availability storage of subscription and tracking data.
*   **🔒 Secure & Scalable:** Built on a production-ready Docker image with a minimal footprint.

## 💰 Monetization

The bot operates on a **Premium Access Model** powered by instant, on-chain verification:

1.  **User Access:** A user sends `/subscribe <wallet_address>`.
2.  **Instant Check:** The bot uses the Alchemy API to verify the wallet holds the required ETH balance.
3.  **Automatic Activation:** Subscription is activated instantly and stored in the PostgreSQL database.

## 🛠 Setup & Deployment (Production)

### Prerequisites

*   A GitHub Account
*   A Render Account (for hosting and PostgreSQL)
*   A Telegram Bot Token
*   An Alchemy API Key

### Deployment Steps (via Docker)

The service is configured to deploy directly to a Web Service on Render using the included `Dockerfile`.

1.  **Clone the Repository:**
    ```bash
    git clone [YOUR REPO URL HERE]
    ```
2.  **Set Environment Variables:** Configure all secrets in the **Render Dashboard's Environment Variables** section (DO NOT commit to GitHub).
    *   `TELEGRAM_BOT_TOKEN`, `ADMIN_ID`, `DATABASE_URL`, `ALCHEMY_API_URL`, `RENDER_APP_NAME`, etc.
3.  **Deploy:** Connect Render to the repository and initiate the Docker build.

## ⚙️ Core Stack

| Component | Purpose |
| :--- | :--- |
| **Backend** | Python 3.12, python-telegram-bot |
| **Database** | PostgreSQL (via Render DB) |
| **Blockchain** | Web3.py, Alchemy API |
| **Deployment** | Docker, Render (Webhooks) |

## ✅ Commands

*   `/start` - Welcome and command list.
*   `/subscribe <wallet>` - Instant premium access check.
*   `/status` - Check subscription expiry.
*   `/wallets`, `/viewtx` - **Premium Features (Sniping/Alerts)**

---
*Created by IceReign-MEXT*
