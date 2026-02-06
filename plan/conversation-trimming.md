# Conversation Trimming Implementation

## Problem
- Session history grows indefinitely
- Long conversations will hit token limits (128k-200k depending on model)
- No way to control context size sent to LLM

## Solution
Add token-based conversation trimming that preserves recent context while staying within configurable limits.

## Tasks

### 1. Token Counting Utility
- [x] Create `icron/utils/tokens.py` with `count_tokens(text: str) -> int`
- [x] Use simple heuristic: ~4 chars per token (accurate enough for trimming)
- [x] Alternative: use tiktoken if installed, fallback to heuristic

### 2. Update Session.get_history
- [x] Add `max_tokens` parameter to `get_history()`
- [x] Keep counting from newest to oldest messages
- [x] Stop when token budget exceeded
- [x] Always include at least the last message

### 3. Add Config Option
- [x] Add `maxContextTokens` to `ExecConfig` in `config_model.py`
- [x] Default: `100000` (100k tokens, leaves room for system prompt + tools)
- [x] Add to `config.example.json`

### 4. Update AgentLoop
- [x] Pass `max_tokens` from config to `session.get_history()`
- [x] Log when trimming occurs

### 5. Update Web UI
- [x] Add slider/input for "Max Context Tokens" in App.svelte
- [x] Range: 10000 - 200000
- [x] Build UI

### 6. Test & Commit
- [x] Test with long conversation
- [x] Verify trimming works
- [x] Commit and push

## Implementation Details

### Token Counting Strategy
```python
def count_tokens(text: str) -> int:
    """Estimate token count. ~4 chars per token for English."""
    return len(text) // 4 + 1
```

### Session.get_history Changes
```python
def get_history(self, max_messages: int = 50, max_tokens: int | None = None) -> list[dict[str, Any]]:
    """Get message history for LLM context with optional token limit."""
    recent = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
    
    if max_tokens is None:
        return [{"role": m["role"], "content": m["content"]} for m in recent]
    
    # Trim by tokens (newest first)
    result = []
    total_tokens = 0
    for msg in reversed(recent):
        content = msg.get("content", "")
        tokens = count_tokens(str(content))
        if total_tokens + tokens > max_tokens and result:
            break
        result.append({"role": msg["role"], "content": content})
        total_tokens += tokens
    
    return list(reversed(result))  # Restore chronological order
```

## Notes
- Memory tools (permanent storage) are NOT affected
- Only the LLM context window is trimmed
- System prompt and tools still consume tokens separately
