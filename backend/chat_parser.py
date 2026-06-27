import re
import unicodedata
from datetime import datetime
from typing import List, Dict, Any, Optional

# Regular expression to match Android export:
# e.g., "12/06/2025, 10:32 - Naseen: Message" or "12/06/2025, 10:32 am - Naseen: Message"
# Captures Date, Time, Name, and Message.
android_pattern = re.compile(
    r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[aApP][mM])?)\s*-\s*([^:]+):\s*(.*)$'
)

# Regular expression to match iPhone export:
# e.g., "[12/06/2025, 10:32:00] Naseen: Message" or "[12/6/25, 10:32:00 AM] Naseen: Message"
iphone_pattern = re.compile(
    r'^\[?(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[aApP][mM])?)\]?\s*([^:]+):\s*(.*)$'
)

android_system_pattern = re.compile(
    r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[aApP][mM])?)\s*-\s*(.*)$'
)

iphone_system_pattern = re.compile(
    r'^\[?(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[aApP][mM])?)\]?\s*(.*)$'
)

def is_emoji_only(text: str) -> bool:
    """
    Checks if a string is composed entirely of emojis, symbols, punctuation, or whitespace.
    Returns True if no alphanumeric letter/number exists in the string.
    """
    text = text.strip()
    if not text:
        return True
    
    for char in text:
        cat = unicodedata.category(char)
        # L = Letter, N = Number
        if cat.startswith('L') or cat.startswith('N'):
            return False
    return True

def parse_timestamp(date_str: str, time_str: str) -> str:
    """
    Parses a date and time string from WhatsApp exports and returns an ISO 8601 string.
    """
    # Clean spacing
    date_str = date_str.strip()
    time_str = time_str.strip()
    
    # Parse Date (supports DD/MM/YYYY or DD/MM/YY)
    date_parts = date_str.split('/')
    if len(date_parts) == 3:
        try:
            day = int(date_parts[0])
            month = int(date_parts[1])
            year = int(date_parts[2])
            if year < 100:
                year += 2000
        except ValueError:
            return datetime.utcnow().isoformat()
    else:
        return datetime.utcnow().isoformat()
        
    # Parse Time (supports HH:MM, HH:MM:SS, AM/PM)
    time_str_lower = time_str.lower()
    is_pm = 'pm' in time_str_lower
    is_am = 'am' in time_str_lower
    
    time_clean = time_str_lower.replace('am', '').replace('pm', '').strip()
    time_parts = time_clean.split(':')
    
    hour = 0
    minute = 0
    second = 0
    
    try:
        if len(time_parts) >= 2:
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            if len(time_parts) == 3:
                second = int(time_parts[2])
                
        if is_pm and hour < 12:
            hour += 12
        elif is_am and hour == 12:
            hour = 0
            
        dt = datetime(year, month, day, hour, minute, second)
        return dt.isoformat()
    except Exception:
        # Return manually formatted string in case of edge values
        return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"

def calculate_quality_score(message: str) -> int:
    """
    Calculates quality score from 0 to 10 based on:
    - Length (1 pt per 5 words, max 4)
    - Task Keywords (+3 pts)
    - Spam Penalty (-3 pts for purely low-value messages)
    
    Uses word-boundary regex to avoid false positives
    (e.g. "measure" should NOT trigger the "sure" spam penalty).
    Penalty only applies if the message is short AND matches spam words.
    """
    import re
    msg_lower = message.lower()
    words = msg_lower.split()
    word_count = len(words)

    # Length score
    length_score = min(4, word_count // 5)

    # Task keywords check — plain substring is fine here (directional phrases)
    task_keywords = [
        "done", "finished", "pushed", "completed", "submitted",
        "will do", "i'll", "i will", "here is", "here's", "sent",
        "updated", "fixed", "resolved", "deployed", "uploaded",
        "attached", "added", "working on", "just did", "just sent",
    ]
    has_keyword = any(kw in msg_lower for kw in task_keywords)
    keyword_bonus = 3 if has_keyword else 0

    # Spam check — use \b word boundaries to avoid false positives
    spam_words = [
        r"\bok\b", r"\bk\b", r"\bsure\b", r"\blol\b", r"\bhaha\b",
        r"\bthanks\b", r"\bthx\b", r"\bnoted\b", r"\bnp\b",
        r"\bcool\b", r"\bhmm\b", r"\byep\b", r"\byup\b",
        r"\bokay\b", r"\balright\b", r"\bya\b", r"\byah\b",
    ]
    has_spam = any(re.search(pattern, msg_lower) for pattern in spam_words)
    # Only penalize if the message is short (≤ 5 words) — a long message
    # containing "thanks" likely has real content too.
    spam_penalty = -3 if (has_spam and word_count <= 5) else 0

    score = length_score + keyword_bonus + spam_penalty
    return max(0, min(10, score))

def should_filter_message(name: str, message: str) -> bool:
    """
    Applies message filtration rules:
    - Media placeholders
    - Deleted message notifications
    - Emoji/symbol only messages
    """
    msg_clean = message.strip()
    msg_lower = msg_clean.lower()
        
    # 1. Media placeholders
    media_indicators = [
        "<media omitted>",
        "<sticker omitted>",
        "image omitted",
        "video omitted",
        "sticker omitted",
        "audio omitted",
        "document omitted",
        "gif omitted"
    ]
    if any(ind in msg_lower for ind in media_indicators):
        return True
        
    # 2. Deleted messages
    if "this message was deleted" in msg_lower or "you deleted this message" in msg_lower:
        return True
        
    # 3. Emoji-only messages
    if is_emoji_only(msg_clean):
        return True
        
    return False

def parse_whatsapp_chat(chat_text: str) -> List[Dict[str, Any]]:
    """
    Parses a raw WhatsApp chat string line-by-line, handling multi-line messages,
    applying filters, and scoring each message.
    """
    lines = chat_text.splitlines()
    parsed_messages = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Try Android regex match
        match = android_pattern.match(line)
        if not match:
            # Try iPhone regex match
            match = iphone_pattern.match(line)
            
        if match:
            date_str, time_str, name, msg = match.groups()
            
            # Check if this matched line is a system action or should be filtered
            if should_filter_message(name, msg):
                continue
                
            timestamp = parse_timestamp(date_str, time_str)
            quality_score = calculate_quality_score(msg)
            
            parsed_messages.append({
                "name": name.strip(),
                "timestamp": timestamp,
                "message": msg.strip(),
                "quality_score": quality_score
            })
        else:
            # Check if this is a system message (has date/time but no colon)
            sys_match = android_system_pattern.match(line) or iphone_system_pattern.match(line)
            if sys_match:
                continue
                
            # If no match, check if this is a continuation of the previous message
            if parsed_messages:
                last_msg = parsed_messages[-1]
                # Append line to previous message
                updated_text = last_msg["message"] + "\n" + line
                
                last_msg["message"] = updated_text
                last_msg["quality_score"] = calculate_quality_score(updated_text)
                    
    return parsed_messages
