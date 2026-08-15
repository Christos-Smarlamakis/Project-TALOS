# -*- coding: utf-8 -*-
"""
Module: notifier.py (v1.0)
Project: TALOS v5.10.5
Description:
    Multi-channel notification system for the TALOS daemon. Sends alerts
    via Telegram (Bot API), Discord (Webhooks), and Email (SMTP). All
    connection exceptions are caught so failures never crash the calling
    code. Configuration is read from environment variables (dotenv).

    Channels:
    - Telegram: Uses Bot API (sendMessage). Requires TELEGRAM_BOT_TOKEN and
      TELEGRAM_CHAT_ID in .env.
    - Discord: Uses Webhook URL. Notifications are delivered as rich embeds
      (title, fields, footer) instead of plain text with HTML tags.
    - Email: Uses SMTP (smtplib). Requires SMTP_SERVER, SMTP_PORT,
      SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM, SMTP_TO in .env.

    Key design decisions:
    - All methods are fire-and-forget — they catch exceptions internally
      and print warnings. The caller never needs try/except around them.
    - Discord notifications use the "embeds" payload array (rich formatting)
      so raw HTML tags are never sent to the "content" field.
    - Email uses STARTTLS for compatibility with most providers (Gmail, etc.).
"""
import os
import smtplib
import html
from datetime import datetime
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from config.settings import TALOS_VERSION

# ── Load environment variables at module level ─────────────────────────────
# This way all instances share the same configuration.
load_dotenv()


def _paper_value(paper, key, default="N/A"):
    """
    Return a paper field as a string, falling back when missing or empty.

    Shared by every notification channel so all payloads render the same
    discovery metadata consistently.

    Args:
        paper (dict): Paper metadata dict (standardized ingestion format).
        key (str): Field key to read (e.g., "title", "authors_str", "doi").
        default (str): Fallback value when the field is missing or empty.

    Returns:
        str: The field value or the default.
    """
    if not isinstance(paper, dict):
        return default
    value = paper.get(key)
    if value is None or value == "":
        return default
    return str(value)


class TalosNotifier:
    """
    Multi-channel notification sender for the TALOS autonomous daemon.

    Supports Telegram (instant alerts), Discord (community/team alerts),
    and Email (daily digest reports). All methods silently handle errors
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

    def telegram_send(self, paper: dict, score: float, action_taken=None):
        """
        Send an HTML-formatted paper alert via Telegram Bot API.

        The payload carries the full discovery metadata (title, authors,
        DOI, URL, source, score, and DRL action) with bold field headers,
        zero emojis, and the dynamic project version in the footer.

        Args:
            paper (dict): Paper metadata (title, authors_str, doi, url or
                doi_url, source). Missing fields render as "N/A".
            score (float): Overall evaluation score (0.0 - 10.0).
            action_taken (optional): DRL action index that found the paper.
        """
        # -- Guard: skip if not configured --
        if not self.telegram_token or not self.telegram_chat_id:
            return

        # -- Build the HTML message with escaped user content --
        title = html.escape(_paper_value(paper, "title", "Unknown Title")[:500])
        authors = html.escape(_paper_value(paper, "authors_str")[:1024])
        doi = html.escape(_paper_value(paper, "doi"))
        paper_url = html.escape(
            _paper_value(paper, "url", "") or _paper_value(paper, "doi_url", "") or "N/A")
        source = html.escape(_paper_value(paper, "source"))

        lines = [
            "<b>TALOS Discovery Alert</b>\n",
            "<b>Title:</b> " + title,
            "<b>Authors:</b> " + authors,
            "<b>DOI:</b> " + doi,
            "<b>URL:</b> " + paper_url,
            "<b>Source:</b> " + source,
            "<b>Score:</b> " + f"{score:.1f}/10",
        ]
        if action_taken is not None:
            lines.append("<b>DRL Action:</b> " + str(action_taken))
        lines.append("\n<i>- TALOS Autonomous Research Service v" + TALOS_VERSION + "</i>")

        message = "\n".join(lines)

        # -- Truncate to Telegram's 4096-character limit --
        if len(message) > 4000:
            message = message[:4000] + "\n\n[TRUNCATED - message too long for Telegram]"

        api_url = (
            f"https://api.telegram.org/bot{self.telegram_token}"
            f"/sendMessage"
        )

        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(api_url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"Telegram send failed: {response.status_code} - {response.text[:200]}")
        except requests.RequestException as e:
            print(f"Telegram connection error: {e}")


    # ══════════════════════════════════════════════════════════════════════════
    # DISCORD
    # ══════════════════════════════════════════════════════════════════════════

    def discord_send(self, paper: dict, score: float, action_taken=None):
        """
        Send a rich Discord embed for a discovered paper via Webhook.

        Instead of posting plain text with raw HTML tags to the "content"
        field, this method builds Discord's structured "embeds" array so
        the notification renders with proper formatting (title, fields,
        footer, and a colour-coded side bar).

        Args:
            paper (dict): Paper metadata (title, authors_str, doi, url or
                doi_url, source). Missing fields render as "N/A".
            score (float): Overall evaluation score (0.0 - 10.0).
            action_taken (optional): DRL action index that discovered the
                paper. Included as a "DRL Action" field when provided.
        """
        # -- Guard: skip if not configured --
        if not self.discord_webhook:
            return

        # -- Build the embed from paper metadata (missing keys degrade) --
        title = _paper_value(paper, "title", "Unknown Title")[:256]
        url = (paper.get("url") or paper.get("doi_url") or "") if isinstance(paper, dict) else ""
        color = 13938487 if score >= 7.0 else 26367

        fields = [
            {"name": "Authors", "value": _paper_value(paper, "authors_str")[:1024], "inline": False},
            {"name": "Score", "value": f"{score}/10", "inline": True},
            {"name": "Source", "value": _paper_value(paper, "source"), "inline": True},
            {"name": "DOI", "value": _paper_value(paper, "doi"), "inline": True},
        ]

        # -- Include the DRL action that found the paper (when available) --
        if action_taken is not None:
            fields.append({"name": "DRL Action", "value": str(action_taken), "inline": True})

        embed = {
            "title": title,
            "url": url,
            "color": color,
            "fields": fields,
            "footer": {"text": f"Project TALOS v{TALOS_VERSION} | SYNAPSE Event Bus"},
        }

        payload = {"embeds": [embed]}

        try:
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            if response.status_code not in (200, 204):
                # Discord returns 204 for success, 200 also works
                print(f"Discord send failed: {response.status_code} - {response.text[:200]}")
        except requests.RequestException as e:
            print(f"Discord connection error: {e}")


    # ══════════════════════════════════════════════════════════════════════════
    # EMAIL (SMTP)
    # ══════════════════════════════════════════════════════════════════════════

    def email_send(self, subject: str, body: str):
        """
        Send an email via SMTP.

        Used for the daily digest report (every day at 17:00). Uses
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
            print(f"Email sent successfully to {cfg['to_addr']}")
        except smtplib.SMTPException as e:
            print(f"Email send failed (SMTP): {e}")
        except (OSError, ConnectionError) as e:
            print(f"Email connection error: {e}")

    def email_paper_alert(self, paper: dict, score: float, action_taken=None):
        """
        Send a professional HTML email alert for a discovered paper.

        Builds an academic, emoji-free HTML table carrying the full
        discovery metadata and the dynamic project version, then delegates
        delivery to email_send (SMTP). Silently skips when SMTP is not
        configured.

        Args:
            paper (dict): Paper metadata (title, authors_str, doi, url or
                doi_url, source). Missing fields render as "N/A".
            score (float): Overall evaluation score (0.0 - 10.0).
            action_taken (optional): DRL action index that found the paper.
        """
        cfg = self.smtp_config
        if not all([cfg["server"], cfg["username"], cfg["password"],
                    cfg["from_addr"], cfg["to_addr"]]):
            return

        subject_title = _paper_value(paper, "title", "Unknown Title")
        title = html.escape(subject_title)
        authors = html.escape(_paper_value(paper, "authors_str"))
        doi = html.escape(_paper_value(paper, "doi"))
        paper_url = html.escape(
            _paper_value(paper, "url", "") or _paper_value(paper, "doi_url", "") or "N/A")
        source = html.escape(_paper_value(paper, "source"))

        rows = [
            ("Title", title),
            ("Authors", authors),
            ("DOI", doi),
            ("URL", paper_url),
            ("Source", source),
            ("Score", f"{score:.1f}/10"),
        ]
        if action_taken is not None:
            rows.append(("DRL Action", str(action_taken)))

        table = "".join(
            f'<tr><td style="padding:6px;color:#555"><b>{label}</b></td>'
            f'<td style="padding:6px">{value}</td></tr>'
            for label, value in rows
        )

        body = (
            "<!DOCTYPE html>"
            '<html><body style="font-family:Arial,sans-serif;color:#222;line-height:1.6">'
            "<h2>TALOS Discovery Alert</h2>"
            '<table style="border-collapse:collapse;width:100%">' + table + "</table>"
            "<hr>"
            '<p style="color:#888;font-size:0.85em">'
            "This is an automated message from the TALOS Autonomous Daemon v" + TALOS_VERSION + "."
            "</p></body></html>"
        )

        subject = "TALOS Discovery Alert - " + subject_title[:80]
        self.email_send(subject, body)

    def email_daily_digest(self, papers: list):
        """
        Send the daily digest email with the day's elite papers.

        Builds a clean, emoji-free HTML table listing each paper's title,
        source, score, and DOI/URL, with the dynamic project version in
        the footer. Silently skips when SMTP is not configured.

        Args:
            papers (list): List of paper dicts (title, source, overall_score,
                doi, url) for papers added/updated in the last 24 hours.
        """
        cfg = self.smtp_config
        if not all([cfg["server"], cfg["username"], cfg["password"],
                    cfg["from_addr"], cfg["to_addr"]]):
            return

        now = datetime.now()
        rows = ""
        if papers:
            for paper in papers:
                title = html.escape(str(paper.get("title") or "Unknown Title"))
                source = html.escape(str(paper.get("source") or "N/A"))
                score = paper.get("overall_score") or paper.get("score") or 0.0
                doi = html.escape(str(paper.get("doi") or ""))
                url = html.escape(str(paper.get("url") or ""))
                link = doi or url or "N/A"
                rows += (
                    f'<tr><td style="padding:6px">{title}</td>'
                    f'<td style="padding:6px">{source}</td>'
                    f'<td style="padding:6px">{score}</td>'
                    f'<td style="padding:6px">{link}</td></tr>'
                )
        else:
            rows = (
                '<tr><td colspan="4" style="padding:6px;color:#888">'
                "No elite papers in the last 24 hours.</td></tr>"
            )

        body = (
            "<!DOCTYPE html>"
            '<html><body style="font-family:Arial,sans-serif;color:#222;line-height:1.6">'
            "<h2>TALOS Daily Digest</h2>"
            f"<p><strong>Date:</strong> {now.strftime('%Y-%m-%d')}</p>"
            "<hr>"
            "<h3>Elite Papers (score >= 7.0) - last 24 hours</h3>"
            '<table border="1" cellpadding="6" style="border-collapse:collapse;width:100%">'
            "<tr><th>Title</th><th>Source</th><th>Score</th><th>DOI/URL</th></tr>"
            + rows +
            "</table>"
            "<hr>"
            '<p style="color:#888;font-size:0.85em">'
            "This is an automated message from the TALOS Autonomous Daemon v" + TALOS_VERSION + "."
            "</p></body></html>"
        )

        subject = f"TALOS Daily Digest - {now.strftime('%Y-%m-%d')}"
        self.email_send(subject, body)

