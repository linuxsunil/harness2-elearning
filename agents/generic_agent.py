import anthropic
import json
import time
from pathlib import Path


def load_prompt():
    path = Path(__file__).parent.parent / "harness" / "prompts" / "generic.txt"
    return path.read_text()


def run(client: anthropic.Anthropic, objective: str, domain: str, audience: str, log_fn=None) -> dict:
    """
    Run the generic (un-harnessed) scenario agent.
    Returns dict with scenario data + metadata.
    """
    system_prompt = load_prompt()
    user_message = f"Learning objective: {objective}\nDomain: {domain}\nAudience: {audience}"

    if log_fn:
        log_fn("generic", "call_start", {
            "system_prompt_preview": system_prompt[:120] + "...",
            "system_prompt_chars": len(system_prompt),
        })

    t0 = time.time()
    full_text = ""
    input_tokens = 0
    output_tokens = 0

    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    ) as stream:
        for event in stream:
            if hasattr(event, 'type'):
                if event.type == 'message_start':
                    input_tokens = event.message.usage.input_tokens
                    if log_fn:
                        log_fn("generic", "tokens_in", {"count": input_tokens})
                elif event.type == 'content_block_delta':
                    if hasattr(event.delta, 'text'):
                        full_text += event.delta.text
                        if log_fn:
                            log_fn("generic", "streaming", {"chunk": event.delta.text})
                elif event.type == 'message_delta':
                    output_tokens = event.usage.output_tokens

    elapsed = round(time.time() - t0, 2)

    if log_fn:
        log_fn("generic", "call_complete", {
            "elapsed": elapsed,
            "output_tokens": output_tokens,
            "total_chars": len(full_text)
        })

    # Parse JSON
    scenario = None
    error = None
    try:
        # Strip markdown code fences if present
        text = full_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        scenario = json.loads(text.strip())
    except Exception as e:
        error = str(e)
        if log_fn:
            log_fn("generic", "parse_error", {"error": error, "raw": full_text[:300]})

    return {
        "scenario": scenario,
        "raw": full_text,
        "error": error,
        "meta": {
            "agent": "generic",
            "system_prompt": system_prompt,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "elapsed": elapsed,
        }
    }
