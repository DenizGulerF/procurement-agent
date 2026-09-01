"""
LLM Agent service — simple tool-calling loop using OpenAI.
"""

import json

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import TOOL_DEFINITIONS, execute_tool


def run_agent(db: Session, user_id: int, message: str) -> dict:
    """
    Run the agent for a single user request.

    Returns:
        {
            "response": str,
            "tool_calls": [str, ...]  # list of tool names called
        }
    """
    # Support both OpenAI cloud and any OpenAI-compatible local server (llama.cpp, Ollama, LM Studio…)
    client_kwargs = {
        "api_key": settings.OPENAI_API_KEY or "local",
    }
    if settings.LLM_BASE_URL:
        client_kwargs["base_url"] = settings.LLM_BASE_URL

    client = OpenAI(**client_kwargs)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"[Acting user_id: {user_id}]\n\n{message}"},
    ]

    tool_calls_made: list[str] = []
    max_iterations = 10  # prevent infinite loops

    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        choice = response.choices[0]

        # Append the assistant message (may contain tool_calls)
        messages.append(choice.message)

        if choice.finish_reason == "tool_calls":
            # Execute each requested tool
            for tc in choice.message.tool_calls:
                tool_name = tc.function.name
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                tool_calls_made.append(tool_name)

                result = execute_tool(
                    tool_name=tool_name,
                    arguments=arguments,
                    db=db,
                    acting_user_id=user_id,
                )

                # Feed tool result back to the LLM
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )

        else:
            # finish_reason == "stop" — we have the final answer
            final_text = choice.message.content or ""
            return {"response": final_text, "tool_calls": tool_calls_made}

    # Fallback if max iterations hit
    return {
        "response": "The agent reached the maximum number of steps without a final answer.",
        "tool_calls": tool_calls_made,
    }
