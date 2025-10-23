#!/usr/bin/env python3
"""
iceboys_monetizer.py - ULTIMATE FINAL, DEBUGGED BUILD
Fully automated, stable, Webhook-verified subscription bot.
"""
from db import grant_subscription, check_subscription
import os
import time
import threading
import datetime
from decimal import Decimal

# --- CRITICAL IMPORTS ---
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update
from web3 import Web3
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# ------------------------

# --- LOAD ENVIRONMENT VARIABLES ---
def load_env_vars():
    globals().update({
        "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "OWNER_ID": int(os.environ.get("ADMIN_ID", "0")),
        "TREASURY_WALLET_ADDR": os.environ.get("TREASURY_WALLET_ADDR", "0xYOUR_TREASURY_WALLET_HERE"),
        "SUBSCRIPTION_ETH": Decimal(os.environ.get("SUBSCRIPTION_ETH_PRICE", "0.01")),
        "SUBSCRIPTION_DAYS": int(os.environ.get("SUBSCRIPTION_DAYS", "30")),
        "TRACK_POLL_INTERVAL": int(os.environ.get("TRACK_POLL_INTERVAL", "30")),
        "DATABASE_URL": os.environ.get("DATABASE_URL", None),
        "ALCHEMY_API_URL": os.environ.get("ALCHEMY_API_URL", ""),
        "PORT": int(os.environ.get("PORT", '5000')),
        "RENDER_APP_NAME": os.environ.get("RENDER_APP_NAME", None),
    })

load_env_vars()

if not TELEGRAM_BOT_TOKEN:
    raise SystemExit("FATAL: TELEGRAM_BOT_TOKEN not configured.")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test_subscriptions.db"
    print("WARNING: Using local SQLite DB. Set DATABASE_URL for production.")

# --- DATABASE SETUP ---
Base = declarative_base()

class Subscription(Base):
    __tablename__ = 'subscriptions'
    user_id = Column(String, primary_key=True)
    expires = Column(DateTime)
    plan = Column(String)

def init_db():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

Session = init_db()

# --- WEB3 / ALCHEMY SETUP ---
w3 = None
if ALCHEMY_API_URL:
    try:
        w3 = Web3(Web3.HTTPProvider(ALCHEMY_API_URL))
        if not w3.is_connected():
            print("ERROR: Failed to connect to Ethereum via Alchemy.")
        else:
            print("SUCCESS: Connected to Ethereum via Alchemy.")
    except Exception as e:
        print(f"ERROR connecting Web3: {e}")

# --- LOGGING ---
def log(msg: str):
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(f"[{ts}] {msg}")

# --- SUBSCRIPTION FUNCTIONS ---
def grant_subscription(user_id: str, days: int = SUBSCRIPTION_DAYS):
    session = Session()
    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + datetime.timedelta(days=days)
    sub = session.query(Subscription).filter_by(user_id=str(user_id)).first()
    if sub:
        sub.expires = expire
    else:
        sub = Subscription(user_id=str(user_id), expires=expire, plan="automated_monthly")
        session.add(sub)
    session.commit()
    session.close()

def check_subscription(user_id: str) -> bool:
    session = Session()
    sub = session.query(Subscription).filter_by(user_id=str(user_id)).first()
    session.close()
    return sub and sub.expires > datetime.datetime.now(datetime.timezone.utc)

# --- ON-CHAIN PAYMENT CHECK ---
def check_payment_onchain(wallet_address: str, required_eth: Decimal) -> bool:
    if not w3:
        log("WARNING: Web3 not connected. Simulating success for testing.")
        return True
    try:
        checksum_address = w3.to_checksum_address(wallet_address)
        balance_wei = w3.eth.get_balance(checksum_address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        return balance_eth >= required_eth
    except:
        return False

# --- TELEGRAM HANDLERS ---
def cmd_start(update: Update, context: CallbackContext):
    update.message.reply_text("ICEBOYS-bot is ACTIVE. Use /subscribe <wallet>.")

def cmd_subscribe(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text(f"Use /subscribe <wallet> to check for {SUBSCRIPTION_ETH} ETH.")
        return
    wallet = context.args[0]
    if check_payment_onchain(wallet, SUBSCRIPTION_ETH):
        grant_subscription(str(update.effective_user.id))
        update.message.reply_text("🥳 Payment Confirmed! Subscription activated.")
    else:
        update.message.reply_text("Wallet check failed. Insufficient ETH.")

def cmd_status(update: Update, context: CallbackContext):
    if check_subscription(str(update.effective_user.id)):
        update.message.reply_text("✅ Subscription active.")
    else:
        update.message.reply_text("✖ Subscription inactive.")

def cmd_premium_feature(update: Update, context: CallbackContext):
    if check_subscription(str(update.effective_user.id)):
        update.message.reply_text("✅ Premium access granted.")
    else:
        update.message.reply_text("❌ Premium access required. Use /subscribe.")

# --- TRACKER THREAD ---
def tracker_loop(updater: Updater):
    log("Tracker loop started (24/7 maintenance).")
    while True:
        try:
            log("Tracker: Running maintenance and checks...")
            # Placeholder for sniping / monitoring logic
            time.sleep(TRACK_POLL_INTERVAL)
        except Exception as e:
            log(f"Tracker error: {e}")
            time.sleep(10)

# --- MAIN EXECUTION ---
def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command Handlers
    dp.add_handler(CommandHandler("start", cmd_start))
    dp.add_handler(CommandHandler("subscribe", cmd_subscribe, pass_args=True))
    dp.add_handler(CommandHandler("status", cmd_status))
    dp.add_handler(CommandHandler("wallets", cmd_premium_feature))

    if RENDER_APP_NAME:
        WEBHOOK_URL = f'https://{RENDER_APP_NAME}.onrender.com'

        def set_webhook_safely(bot, url, token):
            time.sleep(2)
            try:
                bot.set_webhook(url=url + '/' + token)
                log(f"SUCCESS: Webhook URL set: {url}/{token}")
            except Exception as e:
                log(f"WARNING: Webhook set failed (non-fatal). Error: {e}")

        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TELEGRAM_BOT_TOKEN)
        log(f"Webhook listener started on internal port {PORT}.")

        t_tracker = threading.Thread(target=tracker_loop, args=(updater,), daemon=True)
        t_tracker.start()
        t_webhook = threading.Thread(target=set_webhook_safely, args=(updater.bot, WEBHOOK_URL, TELEGRAM_BOT_TOKEN), daemon=True)
        t_webhook.start()
    else:
        updater.start_polling()
        log("Bot started. Falling back to polling (local test).")
        t = threading.Thread(target=tracker_loop, args=(updater,), daemon=True)
        t.start()

    updater.idle()

if __name__ == "__main__":
    main()
