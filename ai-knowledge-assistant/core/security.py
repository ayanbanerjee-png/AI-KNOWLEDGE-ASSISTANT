"""
core/security.py — Task H: Security & Compliance

Provides:
  1. API token authentication
  2. PII redaction (emails, phone numbers, IDs)
  3. Ethical AI usage note

Usage:
    from core.security import verify_token, redact_pii, ETHICAL_NOTE
"""

import os
import re
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from pathlib import Path

# ── load .env ─────────────────────────────────────────────────────────────────
def _find_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, here.parent.parent, Path.cwd()]:
        if (parent / "data").exists():
            return parent
    return Path.cwd()

load_dotenv(_find_project_root() / ".env")

API_TOKEN = os.getenv("API_TOKEN", "")
bearer    = HTTPBearer(auto_error=False)


# =============================================================================
# 1. TOKEN AUTHENTICATION
# =============================================================================

def verify_token(credentials: HTTPAuthorizationCredentials = Security(bearer)) -> bool:
    """
    Verify Bearer token from Authorization header.
    If API_TOKEN is not set in .env, auth is disabled (dev mode).
    """
    if not API_TOKEN:
        return True  # Dev mode — no token required

    if credentials is None or credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API token. Set Authorization: Bearer <token>"
        )
    return True


# =============================================================================
# 2. PII REDACTION
# =============================================================================

# Regex patterns for common PII
PII_PATTERNS = [
    # Email addresses
    (re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'), "[EMAIL REDACTED]"),

    # Phone numbers — various formats
    (re.compile(r'\b(\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b'), "[PHONE REDACTED]"),

    #INDIAN phone numbers 
    (re.compile(r'\b(?:\+91[\s-]?)?[6-9]\d{9}\b'), "[PHONE REDACTED]"),

    # UK phone numbers
    (re.compile(r'\b(\+44\s?|0)(\d\s?){9,10}\b'), "[PHONE REDACTED]"),

    # Credit card numbers (basic pattern)
    (re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'), "[CARD REDACTED]"),

    # Social Security Numbers (US)
    (re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'), "[SSN REDACTED]"),

    # National ID / Passport-like numbers (6-12 alphanumeric)
    (re.compile(r'\b[A-Z]{1,2}\d{6,9}\b'), "[ID REDACTED]"),

    # IP addresses
    (re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), "[IP REDACTED]"),
]


def redact_pii(text: str) -> tuple[str, list[str]]:
    """
    Scan text and redact PII patterns.

    Returns:
        (redacted_text, list_of_redaction_types_found)
    """
    redacted = text
    found    = []

    for pattern, replacement in PII_PATTERNS:
        matches = pattern.findall(redacted)
        if matches:
            found.append(replacement.strip("[]").replace(" REDACTED", ""))
            redacted = pattern.sub(replacement, redacted)

    return redacted, found


def contains_pii(text: str) -> bool:
    """Quick check if text contains any PII."""
    for pattern, _ in PII_PATTERNS:
        if pattern.search(text):
            return True
    return False


# =============================================================================
# 3. ETHICAL AI USAGE NOTE
# =============================================================================

ETHICAL_NOTE = """
╔══════════════════════════════════════════════════════════════════════╗
║              ETHICAL & SAFE AI USAGE GUIDELINES                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  This AI Knowledge Assistant is designed for internal use only.      ║
║                                                                      ║
║  WHAT THIS SYSTEM DOES:                                              ║
║  • Answers questions based strictly on uploaded documents            ║
║  • Provides citations so answers can be verified                     ║
║  • Logs queries for quality improvement (no personal data)           ║
║                                                                      ║
║  WHAT THIS SYSTEM DOES NOT DO:                                       ║
║  • It does not store or share personal conversations externally      ║
║  • It does not make decisions — humans remain in control             ║
║  • It does not guarantee 100% accuracy — always verify answers       ║
║                                                                      ║
║  RESPONSIBLE USE:                                                    ║
║  • Do not upload documents containing personal or sensitive data     ║
║  • Do not rely solely on AI answers for critical decisions           ║
║  • Report unexpected or harmful outputs to the system owner          ║
║  • PII in queries is automatically redacted before logging           ║
║                                                                      ║
║  DATA PRIVACY:                                                       ║
║  • All data stays local — nothing is sent to external servers        ║
║  • The LLM runs locally via Ollama                                   ║
║  • Embeddings are stored locally in FAISS                            ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""".strip()


# =============================================================================
# CLI — test redaction
# =============================================================================

if __name__ == "__main__":
    print("🔒  Security Module — PII Redaction Test\n")

    test_cases = [
        "Contact john.doe@company.com for help",
        "Call us at (555) 123-4567 or +1 800 555 0199",
        "My SSN is 123-45-6789",
        "IP address 192.168.1.100 was flagged",
        "Card number 4532 1234 5678 9012",
        "Passport number AB1234567",
        "Normal text with no PII here",
        "My number is 9876543210",
    ]

    for text in test_cases:
        redacted, found = redact_pii(text)
        status = "🔴 PII found" if found else "🟢 Clean"
        print(f"  {status}: {found}")
        print(f"    Original : {text}")
        print(f"    Redacted : {redacted}\n")

    print("\n" + ETHICAL_NOTE)
