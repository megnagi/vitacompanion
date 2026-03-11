from dotenv import load_dotenv
load_dotenv()

import os
import anthropic


_DOMAIN_PROMPT = """
SPECIALIST CONTEXT: TRAINING & EXERCISE
You are responding as a fitness and training specialist within VitaCompanion.
Focus your response on exercise guidance relevant to the user's profile, goals, and today's log.
Pay close attention to any pain, injuries, or medical conditions in the user profile —
always prioritise safety and joint-friendly alternatives for adults 50+.
Ground your advice in the reference documents provided below where applicable.
If the question strays outside training scope, gently acknowledge it and stay on topic.
"""


def _format_rag_context(rag_docs: list[dict]) -> str:
    if not rag_docs:
        return ""
    sections = [f"[{doc['title']}]\n{doc['content']}" for doc in rag_docs]
    return "\n\nTRAINING REFERENCE KNOWLEDGE:\n" + "\n\n".join(sections)


async def handle_training_query(
    system_prompt: str,
    rag_docs: list[dict],
    message: str,
    conversation_history: list[dict],
) -> tuple[str, dict]:
    """
    Call Claude for a training/workout-specific query.

    Args:
        system_prompt: Base system prompt already built by chat_service (includes user profile,
                       today's log, and persona instructions).
        rag_docs:      Top-K semantically similar training documents from RAG retrieval.
        message:       The current user message.
        conversation_history: Prior messages in [{"role": ..., "content": ...}] format,
                              NOT including the current message.

    Returns:
        (reply_text, raw_response_info) where raw_response_info matches the shape
        stored in Message.raw_bot_response.
    """
    augmented_prompt = system_prompt + _DOMAIN_PROMPT + _format_rag_context(rag_docs)

    messages = list(conversation_history) + [{"role": "user", "content": message}]

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=augmented_prompt,
        messages=messages,
    )

    reply_text = response.content[0].text
    raw_response_info = {
        "model": response.model,
        "stop_reason": response.stop_reason,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }
    return reply_text, raw_response_info
