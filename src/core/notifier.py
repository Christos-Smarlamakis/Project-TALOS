# -*- coding: utf-8 -*-
"""
Module: notifier.py (v1.0)
Project: TALOS v5.10.0
Description:
    Multi-channel notification system for the TALOS daemon. Sends alerts
    via Telegram (Bot API), Discord (Webhooks), and Email (SMTP). All
    connection exceptions are caught so failures never crash the calling
    code. Configuration is read from environment variables (dotenv).

    Channels:
    - Telegram: Uses Bot API (sendMessage). Requires TELEGRAM_BOT_TOKEN and
      TELEGRAM_CHAT_ID in .env.
    - Discord: Uses Webhook URL. Messages are truncated to 2000 characters
      (Discord limit) with a "[TRUNCATED]" marker.
    - Email: Uses SMTP (smtplib). Requires SMTP_SERVER, SMTP_PORT,
      SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM, SMTP_TO in .env.

    Key design decisions:
    - All methods are fire-and-forget — they catch exceptions internally
      and print warnings. The caller never needs try/except around them.
    - Discord truncation uses character count, not byte count, because
      Discord counts UTF-8 characters, not bytes.
    - Email uses STARTTLS for compatibility with most providers (Gmail, etc.).
"""
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# ── Load environment variables at module level ─────────────────────────────
# This way all instances share the same configuration.
load_dotenv()


class TalosNotifier:
    """
    Multi-channel notification sender for the TALOS autonomous daemon.

    Supports Telegram (instant alerts), Discord (community/team alerts),
    and Email (weekly digest reports). All methods silently handle errors
    so the daemon never crashes due to a notification failure.

    Attributes:
        telegram_token (str or None): Bot token from @BotFather.
        telegram_chat_id (str or None): Target chat or channel ID.
        discord_webhook (str or None): Discord webhook URL.
        smtp_config (dict): SMTP server configuration.
    """

    def __init__(self):
        """
        Initialise the notifier by reading all keys from environment.

        Reads from the .env file (loaded at module level). Keys that
        are missing are set to None — the corresponding send method
        will silently skip.
        """
        # ── Telegram configuration ────────────────────────────────────────
        # Create a bot with @BotFather on Telegram to get the token.
        # The chat_id can be your personal ID or a channel ID.
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        # ── Discord configuration ─────────────────────────────────────────
        # Create a webhook in your Discord server settings.
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

        # ── Email (SMTP) configuration ────────────────────────────────────
        # For Gmail: smtp.gmail.com, port 587, use an App Password.
        self.smtp_config = {
            "server": os.getenv("SMTP_SERVER"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD"),
            "from_addr": os.getenv("SMTP_FROM"),
            "to_addr": os.getenv("SMTP_TO"),
        }

    # ══════════════════════════════════════════════════════════════════════════
    # TELEGRAM
    # ══════════════════════════════════════════════════════════════════════════

    def telegram_send(self, message: str):
        """
        Send a message via Telegram Bot API.

        This is the fastest notification channel — ideal for instant
        alerts when the DRL agent discovers a high-scoring paper.

        Args:
            message (str): The text to send (max 4096 chars for Telegram).
        """
        # ── Guard: skip if not configured ────────────────────────────────
        if not self.telegram_token or not self.telegram_chat_id:
            return

        # ── Build the API URL ────────────────────────────────────────────
        url = (
            f"https://api.telegram.org/bot{self.telegram_token}"
            f"/sendMessage"
        )

        # ── Truncate message if needed ───────────────────────────────────
        # Telegram limit is 4096 characters. We add a truncation marker.
        if len(message) > 4000:
            message = message[:4000] + "\n\n[TRUNCATED — message too long for Telegram]"

        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML",  # Allows bold, italic, links
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            # 200 = success, anything else = log the error but don't raise
            if response.status_code != 200:
                print(f"  ⚠️  Telegram send failed: {response.status_code} — {response.text[:200]}")
        except requests.RequestException as e:
            # Network down, timeout, DNS failure — log and continue
            print(f"  ⚠️  Telegram connection error: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # DISCORD
    # ══════════════════════════════════════════════════════════════════════════

    def discord_send(self, message: str):
        """
        Send a message via Discord Webhook.

        Discord has a strict 2000-character limit per message. Messages
        longer than this are truncated with a "[TRUNCATED]" marker.

        Args:
            message (str): The text to send.
        """
        # ── Guard: skip if not configured ────────────────────────────────
        if not self.discord_webhook:
            return

        # ── Truncate to Discord's 2000-character limit ────────────────────
        if len(message) > 1950:
            message = message[:1950] + "\n\n[TRUNCATED — message exceeds Discord 2000 char limit]"

        payload = {"content": message}

        try:
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            if response.status_code not in (200, 204):
                # Discord returns 204 for success, 200 also works
                print(f"  ⚠️  Discord send failed: {response.status_code} — {response.text[:200]}")
        except requests.RequestException as e:
            print(f"  ⚠️  Discord connection error: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # EMAIL (SMTP)
    # ══════════════════════════════════════════════════════════════════════════

    def email_send(self, subject: str, body: str):
        """
        Send an email via SMTP.

        Used for the weekly digest report (every Friday at 17:00). Uses
        STARTTLS for secure connection, compatible with Gmail, Outlook,
        and most corporate SMTP servers.

        Args:
            subject (str): Email subject line.
            body (str): Email body (plain text or HTML).
        """
        # ── Guard: skip if not configured ────────────────────────────────
        cfg = self.smtp_config
        if not all([cfg["server"], cfg["username"], cfg["password"],
                    cfg["from_addr"], cfg["to_addr"]]):
            return

        # ── Build the email message ──────────────────────────────────────
        msg = MIMEMultipart()
        msg["From"] = cfg["from_addr"]
        msg["To"] = cfg["to_addr"]
        msg["Subject"] = subject
        # Attach the body as HTML (rich formatting) with a plain-text fallback
        msg.attach(MIMEText(body, "html", "utf-8"))

        try:
            # ── Connect to the SMTP server ───────────────────────────────
            server = smtplib.SMTP(cfg["server"], cfg["port"], timeout=30)
            server.ehlo()  # Identify ourselves to the server
            server.starttls()  # Upgrade to encrypted connection
            server.ehlo()  # Re-identify over TLS
            server.login(cfg["username"], cfg["password"])
            server.sendmail(cfg["from_addr"], cfg["to_addr"], msg.as_string())
            server.quit()
            print(f"  📧 Email sent successfully to {cfg['to_addr']}")
        except smtplib.SMTPException as e:
            print(f"  ⚠️  Email send failed (SMTP): {e}")
        except (OSError, ConnectionError) as e:
            print(f"  ⚠️  Email connection error: {e}")