PROMPT_DIVIDER = "─" * 72


def log_prompt(agent_label: str, final_prompt: dict, *, show_system: bool = False) -> None:
    """
    Print formatted system/user prompts for debugging.

    Args:
        agent_label: Short label such as "Decision" or "Perception".
        final_prompt: Dict with 'system_prompt' and 'formatted_user_prompt'.
        show_system: Whether to print the system prompt contents.
    """
    divider = PROMPT_DIVIDER
    if show_system:
        print(f"\n{divider}\n[{agent_label}] SYSTEM PROMPT\n{divider}")
        print(final_prompt.get("system_prompt", "").strip())

    print(f"\n{divider}\n[{agent_label}] USER PROMPT\n{divider}")
    print(f"{final_prompt.get('formatted_user_prompt', '').strip()}\n")

