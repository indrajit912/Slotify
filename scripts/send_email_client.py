"""
Hermes API Email Client
----------------------
This script provides a reusable Python function to send emails via the Hermes API `/api/v1/send-email` endpoint.

Author: Indrajit Ghosh
Created On: Sep 23, 2025

Purpose:
- Integrate email sending into any Python project using Hermes as a backend service.
- Supports all Hermes email features: personal API keys, EmailBots, HTML/text bodies, CC/BCC, attachments, etc.
- Example usage included for quick testing and integration.

Usage:
- Import `send_email_via_hermes` in your project, or run this script directly for a demo.
"""
import base64
import os
import requests
from typing import List, Optional, Dict, Any

def send_email_via_hermes(
    api_url: str,
    api_key: str,
    to: List[str],
    subject: Optional[str] = None,
    email_plain_text: Optional[str] = None,
    email_html_text: Optional[str] = None,
    from_name: Optional[str] = None,
    bot_id: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Send an email using the Hermes API /api/v1/send-email endpoint.

    Args:
        api_url: Base URL of the Hermes API (e.g., 'https://hermesbot.pythonanywhere.com/api/v1/send-email')
        api_key: Your personal API key (Bearer token)
        to: List of recipient email addresses
        subject: Email subject (optional)
        email_plain_text: Plain text body (optional)
        email_html_text: HTML body (optional)
        from_name: Sender name (optional)
        bot_id: EmailBot ID to use (optional)
        cc: List of CC email addresses (optional)
        bcc: List of BCC email addresses (optional)
        attachments: List of file paths (optional)
        timeout: Request timeout in seconds

    Returns:
        Response JSON from Hermes API
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "to": to,
    }
    if subject is not None:
        payload["subject"] = subject
    if email_plain_text is not None:
        payload["email_plain_text"] = email_plain_text
    if email_html_text is not None:
        payload["email_html_text"] = email_html_text
    if from_name:
        payload["from_name"] = from_name
    if bot_id:
        payload["bot_id"] = bot_id
    if cc:
        payload["cc"] = cc
    if bcc:
        payload["bcc"] = bcc
    if attachments:
        attachment_objs = []
        for path in attachments:
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            attachment_objs.append({
                "filename": os.path.basename(path),
                "content": encoded
            })
        payload["attachments"] = attachment_objs

    response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    # Example usage:
    HOST = "http://localhost:8080"

    result = send_email_via_hermes(
        api_url=f"{HOST}/api/v1/send-email",
        api_key="YOUR_API_KEY",
        to=["recipient@example.com"],
        subject="Hello from Hermes",
        email_html_text="""
            <html>
              <body>
                <h2 style='color: #007bff;'>Welcome to Hermes!</h2>
                <p>This is a <b>test email</b> sent using the Hermes API.</p>
                <ul>
                  <li>Fast</li>
                  <li>Secure</li>
                  <li>Easy to use</li>
                </ul>
                <p style='font-size: 0.9em; color: #888;'>Sent via <i>Hermes API</i></p>
              </body>
            </html>
        """,
        from_name="Your App",
    )
    
    print(result)