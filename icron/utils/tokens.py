"""Token counting utilities for conversation trimming."""


def count_tokens(text: str) -> int:
    """
    Estimate token count for text.
    
    Uses a simple heuristic of ~4 characters per token, which is
    reasonably accurate for English text and good enough for
    conversation trimming purposes.
    
    Args:
        text: The text to count tokens for.
    
    Returns:
        Estimated token count.
    """
    if not text:
        return 0
    return len(text) // 4 + 1


def count_message_tokens(message: dict) -> int:
    """
    Count tokens in a message dict.
    
    Args:
        message: A message dict with 'role' and 'content' keys.
    
    Returns:
        Estimated token count including role overhead.
    """
    content = message.get("content", "")
    
    # Handle list content (images + text)
    if isinstance(content, list):
        text_content = ""
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_content += item.get("text", "")
        content = text_content
    
    # Add ~4 tokens for role/formatting overhead
    return count_tokens(str(content)) + 4
