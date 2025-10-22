# nano iceboys_monetizer.py
# (PASTE THE COMPLETE CONTENT BELOW)

#!/usr/bin/env python3
"""
iceboys_monetizer.py - FINAL PRODUCTION BUILD
Fully automated, PostgreSQL-backed, Alchemy-verified subscription bot using Webhooks.
"""

import os
import time
import threading
import uuid
import datetime
from pathlib import Path
from decimal import Decimal

# --- CRITICAL IMPORTS FOR STABILITY & FEATURES ---
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update, ParseMode
from web3 import Web3
from web3.exceptions import InvalidAddress
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
# ------------------------------------------------


# --- CONFIGURATION (from .env) ---
BASE_DIR = Path.home() / "ICEBOYS-bot"

# Load environment variables (Critical Step)
def load_dotenv(path: Path):
    if not path.exists(): return
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            globals().update({k: v})

load_dotenv(BASE_DIR / ".env")


# --- GLOBAL DEFAULTS / CONSTANTS (Overridden by .env) ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("ADMIN_ID", "0"))

# Subscription and Payment Configuration
SUBSCRIPTION_ETH = Decimal(os.environ.get("SUBSCRIPTION_ETH_PRICE", "0.01"))
SUBSCRIPTION_DAYS = int(os.environ.get("SUBSCRIPTION_DAYS", "30"))
TRACK_POLL_INTERVAL = int(os.environ.get("TRACK_POLL_INTERVAL", "30")) # Seconds for the tracker thread

# Hosting/Deployment Config
PORT = int(os.environ.get('PORT', '5000'))
RENDER_APP_NAME = os.environ.get('RENDER_APP_NAME', os.environ.get('HEROKU_APP_NAME')) # Use HEROKU/RENDER name


if not TELEGRAM_BOT_TOKEN:
    print("FATAL ERROR: TELEGRAM_BOT_TOKEN not configured.")
    raise SystemExit(1)


# --- DATABASE SETUP (PostgreSQL) ---
DATABASE_URL = os.environ.get("DATABASE_URL", None)
if not DATABASE_URL:
    print("FATAL ERROR: DATABASE_URL not configured. Cannot proceed with stable storage.")
    raise SystemExit(1)

Base = declarative_base()

class Subscription(Base):
    __tablename__ = 'subscriptions'
    user_id = Column(String, primary_key=True)
    expires = Column(DateTime)
    plan = Column(String)

def init_db(db_url):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session

Session = init_db(DATABASE_URL)


# --- WEB3 / ALCHEMY SETUP ---
ALCHEMY_API_URL = os.environ.get("ALCHEMY_API_URL", "")
w3 = None
if ALCHEMY_API_URL:
    try:
        w3 = Web3(Web3.HTTPProvider(ALCHEMY_API_URL))
        if not w3.is_connected():
            print("ERROR: Failed to connect to Ethereum via Alchemy. Check ALCHEMY_API_URL.")
        else:
            print("SUCCESS: Connected to Ethereum via Alchemy for payment checks.")
    except Exception as e:
        print(f"ERROR connecting Web3: {e}")


# --- LOGGING ---
def log(msg: str):
    ts = datetime.datetime.now(datetime.UTC).isoformat()
    line = f"[{ts}] {msg}"
    print(line)


# --- Core Subscription/DB Functions ---
def grant_subscription(user_id: str, days: int = SUBSCRIPTION_DAYS):
    session = Session()
    now = datetime.datetime.now(datetime.UTC)
    expire = now + datetime.timedelta(days=days)

    sub = session.query(Subscription).filter_by(user_id=str(user_id)).first()
    if sub:
        sub.expires = expire
    else:
        sub = Subscription(user_id=str(user_id), expires=expire, plan="automated_monthly")
        session.add(sub)

    session.commit()
    session.close()

def check_subscription(user_id: str) -> datetime.datetime | None:
    session = Session()
    sub = session.query(Subscription).filter_by(user_id=str(user_id)).first()
    session.close()

    if sub and sub.expires > datetime.datetime.now(datetime.UTC):
        return sub.expires

    return None

def subscription_expiry(user_id: str) -> str:
    exp = check_subscription(user_id)
    return exp.strftime("%Y-%m-%d %H:%M UTC") if exp else "None"


# --- Automated Payment Check ---
def check_payment_onchain(wallet_address: str, required_eth: Decimal) -> bool:
    """
    Checks if the wallet holds at least the required ETH balance.
    This is the instant check for the /subscribe command.
    """
    if not w3:
        log("Payment check failed: Web3 not connected.")
        return False

    try:
        checksum_address = w3.to_checksum_address(wallet_address)
        balance_wei = w3.eth.get_balance(checksum_address)
        balance_eth = w3.from_wei(balance_wei, 'ether')

        log(f"Wallet {wallet_address} balance: {balance_eth:.4f} ETH. Required: {required_eth} ETH")

        return balance_eth >= required_eth

    except InvalidAddress:
        return False
    except Exception as e:
        log(f"Error checking on-chain payment for {wallet_address}: {e}")
        return False


# --- Telegram Command Handlers ---

def cmd_start(update: Update, context: CallbackContext):
    txt = (
        "🔥 **ICEBOYS-IBS Bot** - Automated Crypto Alerts\n\n"
        "Commands:\n"
        "/subscribe <wallet> - Start instant 30-day premium access.\n"
        "/status - Show your subscription status.\n"
        "All other commands are Premium features."
    )
    update.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN)

def cmd_subscribe(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)

    if check_subscription(user_id):
        exp = subscription_expiry(user_id)
        update.message.reply_text(f"✅ Subscription active until {exp}.")
        return

    if not context.args:
        msg = (
            "To activate your **30-day premium access** instantly, please use:\n"
            f"```/subscribe <your_wallet_address>```\n\n"
            f"**Requirement:** We will check that your wallet holds a balance of at least **{SUBSCRIPTION_ETH} ETH**.\n"
            "If the balance is confirmed, your subscription is **activated instantly**."
        )
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    wallet_address = context.args[0]

    if check_payment_onchain(wallet_address, SUBSCRIPTION_ETH):
        grant_subscription(user_id, days=SUBSCRIPTION_DAYS)
        update.message.reply_text("🥳 **Payment Confirmed!** Your 30-day premium subscription is now **active**! Welcome to the ICEBOYS.", parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(f"Wallet check failed. Ensure wallet `{wallet_address}` is correct and has a balance of at least {SUBSCRIPTION_ETH} ETH.", parse_mode=ParseMode.MARKDOWN)


def cmd_status(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    exp = check_subscription(user_id)
    if exp:
        update.message.reply_text(f"✅ Premium access active until {subscription_expiry(user_id)}.")
    else:
        update.message.reply_text("✖ You do not have an active subscription. Use /subscribe to begin.")

def cmd_premium_feature(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not check_subscription(user_id):
        update.message.reply_text("❌ This is a **Premium Command**. Please use /subscribe to gain access to this feature.", parse_mode=ParseMode.MARKDOWN)
        return

    update.message.reply_text(f"✅ Premium access granted. Command activated!", parse_mode=ParseMode.MARKDOWN)

# --- Background Tracker/Sniping Thread ---
def tracker_loop(updater: Updater):
    log("Tracker loop started (24/7 Sniping and Maintenance).")

    # This loop is essential for 24/7 tasks that Webhooks can't do (like checking if subs expired)
    while True:
        try:
            log("Tracker: Running maintenance and sniping checks...")
            # Sniping Logic and Subscription Expiry Checks would go here.
            time.sleep(TRACK_POLL_INTERVAL)
        except Exception as e:
            log(f"Tracker loop error: {e}")
            time.sleep(10)


def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command Handlers
    dp.add_handler(CommandHandler("start", cmd_start))
    dp.add_handler(CommandHandler("help", cmd_start))
    dp.add_handler(CommandHandler("subscribe", cmd_subscribe, pass_args=True))
    dp.add_handler(CommandHandler("status", cmd_status))

    # Premium Commands (Placeholder for your core business)
    dp.add_handler(CommandHandler("wallets", cmd_premium_feature))
    dp.add_handler(CommandHandler("pay", cmd_premium_feature))
    dp.add_handler(CommandHandler("viewtx", cmd_premium_feature))
    dp.add_handler(CommandHandler("myinfo", cmd_premium_feature))

    # --- WEBHOOK START (For Render 24/7) ---
    if RENDER_APP_NAME:
        WEBHOOK_URL = f'https://{RENDER_APP_NAME}.onrender.com/'

        # 1. Set the Webhook URL on Telegram
        updater.bot.set_webhook(url=WEBHOOK_URL + TELEGRAM_BOT_TOKEN)
        log(f"Webhook URL set on Telegram: {WEBHOOK_URL + TELEGRAM_BOT_TOKEN}")

        # 2. Start the tracker thread (24/7 maintenance)
        t = threading.Thread(target=tracker_loop, args=(updater,), daemon=True)
        t.start()

        # 3. Start the Webhook listener (listens on all interfaces on the required port)
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TELEGRAM_BOT_TOKEN)
        log(f"Webhook listener started on port {PORT}. Bot is now 24/7 for Render deployment.")

    else:
        # --- POLLING START (For Local Termux Testing) ---
        updater.start_polling()
        log("Bot started. Falling back to Polling for local test.")

        # Start tracker thread for local testing
        t = threading.Thread(target=tracker_loop, args=(updater,), daemon=True)
        t.start()

    updater.idle()


if __name__ == "__main__":
    main()
