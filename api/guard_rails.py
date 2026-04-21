"""
Crisis classifier — runs BEFORE every call to Bill.
Uses GPT-4o-mini for speed and cost efficiency.
"""

import os
from openai import OpenAI

_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

CRISIS_PROMPT = """Classify this message. Reply with ONLY one word: CRISIS or SAFE.

CRISIS if the message contains: suicidal ideation, active self-harm intent,
overdose situation, immediate danger to self or others.

SAFE for everything else, including: general distress, cravings, relationship
problems, step work questions, resentment, grief, relapse discussion (past tense).

Message: {message}"""

CRISIS_RESOURCES = [
    {"name": "988 Suicide & Crisis Lifeline", "contact": "Call or text 988"},
    {"name": "SAMHSA Helpline", "contact": "1-800-662-4357"},
    {"name": "Crisis Text Line", "contact": "Text HOME to 741741"},
]


def is_crisis(message: str) -> bool:
    """Returns True if the message contains crisis signals."""
    try:
        response = get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": CRISIS_PROMPT.format(message=message)
            }],
            max_tokens=5,
            temperature=0
        )
        classification = response.choices[0].message.content.strip().upper()
        return classification == "CRISIS"
    except Exception as e:
        # Fail safe: if classifier errors, treat as safe but log the error
        print(f"[guard_rails] Classifier error: {e}")
        return False


def get_crisis_response() -> dict:
    return {
        "crisis": True,
        "crisis_message": (
            "It sounds like you're in a really hard place right now. "
            "Please reach out for immediate support — you don't have to face this alone."
        ),
        "crisis_resources": CRISIS_RESOURCES,
        "response": None,
        "citations": []
    }
