"""
email_tool.py
=============
Tool 4 of 4: Mock Email Sender Tool (Day 4 - Session 2)

Design Best Practices Implemented:
1. Clear Naming: 'send_email' is unambiguous and standard.
2. Model-Facing Description:
   - Explains that this tool sends an email message to a specified recipient.
   - States mandatory fields (to_email, subject, body) and optional CC recipients.
3. Strict Typed Argument Validation:
   - Validates email format using regex (must contain '@' and a valid domain).
   - Validates subject and body content lengths.
4. Error as Observation:
   - Formatted error messages guide the model to fix bad email addresses or missing subjects.
5. Auditability:
   - Generates unique tracking Message IDs and logs all dispatches to 'sent_emails.jsonl'.
"""

import re
import datetime
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

AUDIT_LOG_FILE = Path(__file__).parent / "sent_emails.jsonl"

_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)


def send_email(
    to_email: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Sends an email message to an employee, client, or team member via the corporate mail gateway.

    Args:
        to_email: The primary recipient's valid email address (e.g. 'sarah.connor@enterprise.io').
        subject: The subject line of the email (must not be empty).
        body: The full plain-text or markdown content of the email message.
        cc: Optional list of additional email addresses to carbon copy.
    """
    # 1. Recipient Email Validation
    if not isinstance(to_email, str) or not _EMAIL_REGEX.match(to_email.strip()):
        return {
            "status": "error",
            "error_type": "InvalidEmailAddress",
            "message": (
                f"The recipient address '{to_email}' is invalid. "
                "Please provide a properly formatted email address, e.g. 'user@example.com'."
            ),
        }

    # 2. CC Email Validation
    clean_cc: List[str] = []
    if cc:
        if isinstance(cc, str):
            cc_list = [c.strip() for c in cc.split(",") if c.strip()]
        elif isinstance(cc, list):
            cc_list = [str(c).strip() for c in cc]
        else:
            cc_list = []

        for c_addr in cc_list:
            if not _EMAIL_REGEX.match(c_addr):
                return {
                    "status": "error",
                    "error_type": "InvalidCCAddress",
                    "message": f"Carbon copy address '{c_addr}' has an invalid email format.",
                }
            clean_cc.append(c_addr)

    # 3. Subject & Body Validation
    if not isinstance(subject, str) or len(subject.strip()) < 3:
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "The email subject must be a descriptive string with at least 3 characters.",
        }

    if not isinstance(body, str) or len(body.strip()) < 5:
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "The email body cannot be empty. Please include the message body.",
        }

    # 4. Mock SMTP Dispatch & Receipt Generation
    message_id = f"MSG-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    audit_entry = {
        "message_id": message_id,
        "timestamp": timestamp,
        "to_email": to_email.strip(),
        "cc": clean_cc,
        "subject": subject.strip(),
        "body_preview": body.strip()[:100] + ("..." if len(body.strip()) > 100 else ""),
        "full_body": body.strip(),
        "delivery_status": "DELIVERED_TO_MOCK_GATEWAY",
    }

    # Append to local audit log
    try:
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_entry) + "\n")
    except Exception as e:
        # Non-fatal audit log failure
        pass

    return {
        "status": "success",
        "message_id": message_id,
        "recipient": to_email.strip(),
        "cc": clean_cc,
        "subject": subject.strip(),
        "timestamp": timestamp,
        "delivery_confirmation": f"Email successfully queued and delivered to {to_email.strip()}.",
    }


def get_sent_emails() -> List[Dict[str, Any]]:
    """Retrieves all sent emails from the local audit log."""
    if not AUDIT_LOG_FILE.exists():
        return []
    records = []
    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))
    return records


if __name__ == "__main__":
    print("=== Testing send_email Tool ===")
    
    # 1. Valid Email Dispatch
    res_valid = send_email(
        to_email="sarah.connor@enterprise.io",
        subject="Q3 Architecture Review Summary",
        body="Hi Sarah,\n\nHere is the summary of the Q3 architecture review. All milestones are on track.\n\nRegards,\nAI Operations",
        cc=["marcus.vance@enterprise.io"],
    )
    print("Valid Send:", res_valid["status"], f"(Message ID: {res_valid.get('message_id')})")

    # 2. Invalid Email Format (Error Observation)
    res_err = send_email(to_email="sarah_connor_no_at_sign", subject="Hello", body="Test message")
    print("Invalid Email (Observation):", res_err["error_type"], "-", res_err["message"])

    # 3. Read audit log
    history = get_sent_emails()
    print(f"Total Sent Emails in Audit Log: {len(history)}")
