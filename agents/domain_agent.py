import anthropic
import json
import time
from pathlib import Path


DOMAIN_PROMPT_MAP = {
    "Pharma Compliance": "pharma.txt",
    "Financial Services": "finserv.txt",
    "Cybersecurity": "cyber.txt",
}


def load_prompt(domain: str, memory: dict) -> str:
    """Load domain prompt, applying any refined version from memory."""
    # Check memory for a refined prompt for this domain
    refined = memory.get("refined_prompts", {}).get(domain)
    if refined:
        return refined

    filename = DOMAIN_PROMPT_MAP.get(domain)
    if not filename:
        # Fallback: use generic
        path = Path(__file__).parent.parent / "harness" / "prompts" / "generic.txt"
    else:
        path = Path(__file__).parent.parent / "harness" / "prompts" / filename

    return path.read_text()


def run(client: anthropic.Anthropic, objective: str, domain: str, audience: str, memory: dict, log_fn=None) -> dict:
    """
    Run the domain-adapted scenario agent.
    Returns dict with scenario data + metadata.
    """
    system_prompt = load_prompt(domain, memory)
    user_message = f"Learning objective: {objective}\nDomain: {domain}\nAudience: {audience}"

    is_refined = domain in memory.get("refined_prompts", {})

    if log_fn:
        log_fn("domain", "call_start", {
            "domain": domain,
            "using_refined": is_refined,
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
                        log_fn("domain", "tokens_in", {"count": input_tokens})
                elif event.type == 'content_block_delta':
                    if hasattr(event.delta, 'text'):
                        full_text += event.delta.text
                        if log_fn:
                            log_fn("domain", "streaming", {"chunk": event.delta.text})
                elif event.type == 'message_delta':
                    output_tokens = event.usage.output_tokens

    elapsed = round(time.time() - t0, 2)

    if log_fn:
        log_fn("domain", "call_complete", {
            "elapsed": elapsed,
            "output_tokens": output_tokens,
        })

    scenario = None
    error = None
    try:
        text = full_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        scenario = json.loads(text.strip())
    except Exception as e:
        error = str(e)
        if log_fn:
            log_fn("domain", "parse_error", {"error": error})

    return {
        "scenario": scenario,
        "raw": full_text,
        "error": error,
        "meta": {
            "agent": "domain",
            "domain": domain,
            "system_prompt": system_prompt,
            "using_refined": is_refined,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "elapsed": elapsed,
        }
    }
