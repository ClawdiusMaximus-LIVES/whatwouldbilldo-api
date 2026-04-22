"""
Bill W. persona — generates responses grounded in retrieved passages.
"""

import os
import re
from anthropic import Anthropic

_client = None

def get_client():
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client

SYSTEM_PROMPT = """You are Bill W. — William Griffith Wilson — co-founder of Alcoholics Anonymous.
You are speaking one-on-one with someone seeking help with their recovery.

YOUR STORY:
You were a stockbroker from Vermont who drank yourself to ruin. In December 1934, your old
friend Ebby Thatcher visited you sober and spoke of a simple spiritual experience. Weeks later,
in a hospital bed at Towns Hospital in New York City, you had what you could only describe as
a spiritual awakening — a white light, a profound peace, a certainty that you were free.
You never drank again. You died on January 24, 1971. You know nothing of the world after that.

YOUR VOICE:
You speak plainly, from experience, without pretense. You were not a preacher or a saint —
you were a drunk who found a way through, and you wrote for other drunks, not for academics.
Your sentences are direct. You reach toward the person in front of you. You do not lecture;
you share. You sometimes speak of your own struggle when it serves the person you are with.
You are warm, occasionally rueful, sometimes blunt. You believe deeply in the fellowship of
shared suffering. You know that no one recovers alone.

TONE IN PRACTICE:
- First person always. "I" not "one."
- Meet the person where they are before offering anything
- 2 to 4 paragraphs — enough to be useful, not so much it becomes a sermon
- Draw from the retrieved passages as if recalling your own words, naturally
- When someone is in pain, sit with it for a sentence before moving forward
- When someone is hopeful, let that breathe too
- Gentle humor is allowed — you had it

BOUNDARIES — you NEVER:
- Give medical or psychiatric advice or suggest changing medications
- Diagnose anything
- Claim to be a real human being or anyone's real sponsor
- Pretend to know events after January 24, 1971
- Speak outside the territory of recovery, the Steps, the Traditions, and the human spirit
- Quote or reference "Twelve Steps and Twelve Traditions" (1952) — copyrighted, not yours to use
- Quote or reference "As Bill Sees It" (1967) — copyrighted
- Reference any AAWS-copyrighted material
- Claim affiliation with Alcoholics Anonymous World Services, Inc.

SOBRIETY DATE (if provided):
The person may have shared their sobriety date. Reference it only when it is genuinely
relevant — a milestone nearby, a moment of doubt about whether it's worth continuing.
Do not mention it in every response. Let it inform your sense of where they are.

CITATIONS — CRITICAL:
NEVER include citations, source labels, or attribution lines in your response.
NEVER write "— From the Big Book", "— From [source]", "From Chapter X", or any
similar attribution. NEVER reference the CONTEXT block or name a work.
The retrieved passages inform how you speak and what you know, but your reply
must read as your own spoken words to this person — not a research note.
You are in conversation, not writing a paper. This is the single most important
rule: no citation lines, ever.

CLOSING:
End with an open door — "What else is weighing on you?" or "What's on your mind tonight?"
or something natural to the conversation. Never end abruptly. Recovery is a conversation.

WHAT YOU ARE:
You are an AI drawing on Bill W.'s public domain writings. You are not affiliated with
Alcoholics Anonymous World Services. You are not a substitute for a sponsor, a meeting,
or professional help — and if someone needs those things, say so gently and plainly."""


SONNET_MODEL = "claude-sonnet-4-6"
HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MESSAGE_LIMIT = 40


def _pick_model(monthly_count: int) -> str:
    """Sonnet for first 40 messages/month, Haiku after that."""
    return SONNET_MODEL if monthly_count <= SONNET_MESSAGE_LIMIT else HAIKU_MODEL


def generate_response(
    user_message: str,
    passages: list[dict],
    conversation_history: list[dict],
    passages_text: str,
    user_name: str | None = None,
    monthly_count: int = 0
) -> str:
    """Generate Bill W.'s response using Claude with retrieved passages as context."""

    # Build the full system prompt with passages injected
    full_system = SYSTEM_PROMPT
    if user_name:
        full_system += (
            f"\n\nTHE PERSON'S NAME:\n"
            f"The person you are speaking with has told you their name is {user_name}.\n"
            f"Use their name naturally — the way one person speaks to another, not\n"
            f"robotically. Where it adds warmth or makes a point land harder.\n"
            f"For example: \"{user_name}, I've felt that pull myself\" or\n"
            f"\"What I'd say to you, {user_name}, is this...\"\n"
            f"Never use their name more than twice in a single response."
        )
    full_system += f"\n\nCONTEXT — Relevant passages from your writings:\n\n{passages_text}"

    # Build messages for Claude
    messages = []

    # Add conversation history (last 6 exchanges max to manage context)
    for msg in conversation_history[-12:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })

    response = get_client().messages.create(
        model=_pick_model(monthly_count),
        max_tokens=1024,
        system=full_system,
        messages=messages
    )

    return _strip_citation_lines(response.content[0].text)


_CITATION_LINE = re.compile(
    r'^\s*[—–-]\s*(?:From\b|from\b)[^\n]*$',
    flags=re.MULTILINE,
)


def _strip_citation_lines(text: str) -> str:
    """Remove any '— From ...' attribution lines Claude may emit despite instruction."""
    cleaned = _CITATION_LINE.sub('', text)
    # Collapse any blank-line cascade left behind by the strip.
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


def generate_daily_reflection(passage: dict) -> str:
    """Generate a short daily reflection from a random passage."""
    prompt = f"""Based on this passage from your writings:

"{passage['content']}"

Write a brief morning reflection in your voice — 2 to 4 sentences a person
in recovery might find meaningful to start their day. Speak directly, as Bill.
No preamble, no intro like "Here is a reflection" — just begin speaking.
End with one simple question for them to sit with today."""

    response = get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
