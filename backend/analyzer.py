import os
import json
from typing import List, Dict, Any
from groq import Groq

def get_groq_client() -> Groq:
    """
    Retrieves a Groq API client or raises ValueError if GROQ_API_KEY is not set.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set. Please configure the .env file in the backend folder.")
    return Groq(api_key=api_key)

def count_words(parsed_chat: List[Dict[str, Any]]) -> int:
    """
    Calculates total word count of parsed messages.
    """
    return sum(len(msg["message"].split()) for msg in parsed_chat)

def chunk_parsed_chat(parsed_chat: List[Dict[str, Any]], limit: int = 2500) -> List[List[Dict[str, Any]]]:
    """
    Slices parsed chat list into sequential chunks where each chunk is under the word limit.
    """
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
    """
    Converts list of parsed messages to a readable text dump for Groq.
    """
    lines = []
    for msg in messages:
        lines.append(f"[{msg['timestamp']}] {msg['name']}: {msg['message']}")
    return "\n".join(lines)

def summarize_chunk(client: Groq, previous_summary: str, chunk_text: str) -> str:
    """
    Prompts Groq to summarize older message chunks sequentially to retain project progress context.
    """
    system_prompt = "You are an assistant tracking team contributions in a WhatsApp chat. Write a concise summary."
    user_prompt = (
        f"Previous accumulated summary:\n{previous_summary or 'None'}\n\n"
        f"Here is a new chunk of chat data:\n{chunk_text}\n\n"
        "Update the running summary of individual contributions, roles, tasks mentioned, completed milestones, and general team behavior. Keep the output under 400 words."
    )
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing chunk: {e}")
        return previous_summary  # Return fallback

def parse_groq_json(response_text: str) -> Dict[str, Any]:
    """
    Strips markdown formatting from Groq response text and parses it into JSON.
    """
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    return json.loads(cleaned)

def run_contribution_analysis(client: Groq, chat_text: str) -> Dict[str, Any]:
    """
    Call 1 - Contribution Analysis: Requests structured JSON format from Groq.
    Retries once on error.
    """
    system_prompt = (
        "You are an expert team dynamics analyst. Analyze the following "
        "WhatsApp group chat and return ONLY a valid JSON object. "
        "No explanation, no markdown, just raw JSON."
    )
    
    user_prompt = (
        "Analyze this group chat and return contribution data in this exact format:\n"
        "{\n"
        "  \"members\": [\n"
        "    {\n"
        "      \"name\": string,\n"
        "      \"scores\": {\n"
        "        \"message_frequency\": number (0-10),\n"
        "        \"initiative\": number (0-10),\n"
        "        \"task_ownership\": number (0-10),\n"
        "        \"follow_through\": number (0-10),\n"
        "        \"responsiveness\": number (0-10)\n"
        "      },\n"
        "      \"overall_score\": number (0-10),\n"
        "      \"summary\": string (2 lines max),\n"
        "      \"promises\": [list of 'I will do X' statements],\n"
        "      \"deliveries\": [list of 'done/pushed/finished X' statements],\n"
        "      \"promise_delivery_ratio\": number (0-1),\n"
        "      \"avg_response_time_hours\": number,\n"
        "      \"peak_activity_hours\": [list of hours 0-23],\n"
        "      \"top_words\": [list of top 10 words excluding stopwords]\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"Chat data:\n{chat_text}"
    )
    
    attempts = 2
    last_error = None
    for attempt in range(attempts):
        try:
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            return parse_groq_json(response_text)
        except Exception as e:
            last_error = e
            print(f"Groq analysis JSON call failed (attempt {attempt + 1}/{attempts}): {e}")
            
    raise ValueError(f"Failed to generate valid contribution analysis JSON after {attempts} attempts. Last error: {last_error}")

def run_narrative_report(client: Groq, chat_text: str, analysis_json: Dict[str, Any]) -> str:
    """
    Call 2 - Narrative Report: Requests a 3-paragraph faculty-style evaluation of the project team.
    """
    system_prompt = "You are an expert team dynamics analyst and academic evaluator."
    user_prompt = (
        "Write a 3 paragraph faculty evaluation report for this group project team "
        "based on the chat analysis. Be specific, evidence-based, and professional. "
        "Mention specific members by name with examples from the chat.\n\n"
        f"Quantitative Analysis JSON:\n{json.dumps(analysis_json, indent=2)}\n\n"
        f"Chat data:\n{chat_text}"
    )
    
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.5
    )
    return completion.choices[0].message.content.strip()

def analyze_chat(parsed_chat: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Splits the parsed chat JSON into chunks if word count exceeds 3000,
    calls Groq API to analyze contributions and build the report.
    """
    client = get_groq_client()
    word_count = count_words(parsed_chat)
    
    if word_count <= 3000:
        chat_text = format_chat_messages(parsed_chat)
    else:
        # Chat exceeds limit; chunk it!
        chunks = chunk_parsed_chat(parsed_chat, limit=2500)
        running_summary = ""
        
        # Summarize all older chunks
        for i in range(len(chunks) - 1):
            chunk_txt = format_chat_messages(chunks[i])
            running_summary = summarize_chunk(client, running_summary, chunk_txt)
            
        # For the final chunk, bundle it with the running summary of prior chunks
        recent_txt = format_chat_messages(chunks[-1])
        chat_text = (
            f"SUMMARY OF PRIOR CONTEXT (OLDER CHUNKS):\n{running_summary}\n\n"
            f"RECENT MESSAGES CHUNK:\n{recent_txt}"
        )
        
    # Make Call 1 (Contribution Analysis JSON)
    analysis_json = run_contribution_analysis(client, chat_text)
    
    # Make Call 2 (Narrative Report)
    report_text = run_narrative_report(client, chat_text, analysis_json)
    
    return {
        "analysis": analysis_json,
        "report": report_text
    }
