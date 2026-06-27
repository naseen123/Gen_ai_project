import os
import json
from typing import List, Dict, Any
from groq import Groq

TASK_KEYWORDS = [
    "i'll", "i will", "done", "finished", "pushed",
    "completed", "here", "check", "will do", "assigned",
    "deadline", "submit", "upload", "send", "share",
    "today", "tonight", "tomorrow", "by", "task",
    "presentation", "report", "code", "push", "finish",
    "meeting", "update", "progress", "working", "started","completed"
]

def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")
    return Groq(api_key=api_key)

def count_words(parsed_chat: List[Dict[str, Any]]) -> int:
    return sum(len(msg["message"].split()) for msg in parsed_chat)

def is_task_message(msg: Dict[str, Any]) -> bool:
    text = msg['message'].lower()
    return any(kw in text for kw in TASK_KEYWORDS)

def chunk_parsed_chat(parsed_chat: List[Dict[str, Any]], limit: int = 1000) -> List[List[Dict[str, Any]]]:
    chunks = []
    current_chunk = []
    current_word_count = 0
    for msg in parsed_chat:
        words_in_msg = len(msg["message"].split())
        if current_word_count + words_in_msg > limit and current_chunk:
            chunks.append(current_chunk)
            current_chunk = [msg]
            current_word_count = words_in_msg
        else:
            current_chunk.append(msg)
            current_word_count += words_in_msg
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def format_chat_messages(messages: List[Dict[str, Any]]) -> str:
    lines = []
    for msg in messages:
        # Truncate long messages
        words = msg['message'].split()
        truncated = ' '.join(words[:50])
        if len(words) > 50:
            truncated += '...'
        lines.append(f"{msg['name']}: {truncated}")
    return "\n".join(lines)

def summarize_chunk(client: Groq, previous_summary: str, chunk_text: str) -> str:
    system_prompt = "You are an assistant tracking team contributions in a WhatsApp chat. Write a concise summary."
    user_prompt = (
        f"Previous accumulated summary:\n{previous_summary or 'None'}\n\n"
        f"Here is a new chunk of chat data:\n{chunk_text}\n\n"
        "Update the running summary of individual contributions, roles, tasks mentioned, "
        "completed milestones, and general team behavior. Keep the output under 400 words."
    )
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=400
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing chunk: {e}")
        return previous_summary

def parse_groq_json(response_text: str) -> Dict[str, Any]:
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    return json.loads(cleaned)

def run_contribution_analysis(client: Groq, chat_text: str, num_members: int) -> Dict[str, Any]:
    system_prompt = "Analyze this WhatsApp group chat. Return ONLY valid JSON, no markdown."
    user_prompt = (
        f'Analyze chat. Return JSON for all {num_members} members (use 0s if no data):\n'
        '{"members":[{"name":str,"scores":{"message_frequency":0-10,"initiative":0-10,'
        '"task_ownership":0-10,"follow_through":0-10,"responsiveness":0-10},'
        '"overall_score":0-10,"summary":str,"promises":[str],"deliveries":[str],'
        '"promise_delivery_ratio":0-1,"top_words":[str]}]}\n\n'
        f"Chat:\n{chat_text}"
    )
    attempts = 2
    last_error = None
    for attempt in range(attempts):
        try:
            approx_tokens = len(user_prompt) // 4
            print(f"run_contribution_analysis: approx tokens = {approx_tokens}")
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            return parse_groq_json(response_text)
        except Exception as e:
            last_error = e
            print(f"Groq analysis JSON call failed (attempt {attempt + 1}/{attempts}): {e}")
    raise ValueError(f"Failed after {attempts} attempts. Last error: {last_error}")

def run_narrative_report(client: Groq, analysis_json: Dict[str, Any]) -> str:
    system_prompt = "You are an expert team dynamics analyst and academic evaluator."
    # Only send analysis JSON to narrative report — not the full chat text
    user_prompt = (
        "Write a 3 paragraph faculty evaluation report for this group project team "
        "based on the analysis below. Be specific, evidence-based, and professional. "
        "Mention specific members by name.\n\n"
        f"Analysis:\n{json.dumps(analysis_json, indent=2)}"
    )
    approx_tokens = len(user_prompt) // 4
    print(f"run_narrative_report: approx tokens = {approx_tokens}")
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="llama-3.1-8b-instant",
        temperature=0.5,
        max_tokens=800
    )
    return completion.choices[0].message.content.strip()

def analyze_chat(parsed_chat: List[Dict[str, Any]]) -> Dict[str, Any]:
    client = get_groq_client()

    unique_members = sorted(list(set(msg.get('name', 'Unknown') for msg in parsed_chat)))
    member_list_str = "ALL MEMBERS IN CHAT: " + ", ".join(unique_members) + "\n\n"

    # Step 1 — Filter to task-relevant messages
    task_messages = [m for m in parsed_chat if is_task_message(m)]

    # Step 2 — If filter too aggressive, fall back to full chat
    if len(task_messages) < 20:
        print(f"Task filter too aggressive ({len(task_messages)} messages), using full chat.")
        task_messages = parsed_chat

    print(f"Total messages: {len(parsed_chat)} | Task-relevant: {len(task_messages)}")

    # Step 3 — Sample from filtered messages
    MAX_MESSAGES = 30

    if len(task_messages) <= MAX_MESSAGES:
        sampled = task_messages
    else:
        early = task_messages[:5]
        recent = task_messages[-25:]
        sampled = early + recent

    total = len(parsed_chat)
    filtered = len(task_messages)
    shown = len(sampled)

    print(f"Sending {shown} messages to Groq (filtered from {filtered}, total {total})")

    chat_text = (
        member_list_str +
        f"[{shown} task-relevant messages from {total} total]\n\n"
        + format_chat_messages(sampled)
    )

    # Step 4 — Contribution Analysis
    analysis_json = run_contribution_analysis(client, chat_text, len(unique_members))

    # Step 5 — Narrative Report (only sends analysis JSON, not full chat)
    report_text = run_narrative_report(client, analysis_json)

    return {
        "analysis": analysis_json,
        "report": report_text
    }