"""Ollama client for local AI inference."""

import json
import httpx
from typing import Optional, Dict, Any
from .actions import Action, ActionType


class OllamaClient:
    """Client for communicating with Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "deepseek-coder:6.7b"):
        self.base_url = base_url
        self.model = model
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    async def generate(self, prompt: str) -> str:
        """Generate text completion from Ollama."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Lower temperature for more deterministic actions
                        "top_p": 0.9,
                    },
                },
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

    async def decide_action(
        self, task_description: str, page_state: Dict[str, Any], history: list[str]
    ) -> Action:
        """Decide the next action based on current state."""

        # Build context from page state
        interactive_summary = self._summarize_interactive_elements(page_state.get("interactive_elements", []))

        # Build history context
        history_text = "\n".join(f"  {i+1}. {action}" for i, action in enumerate(history[-5:]))  # Last 5 actions

        prompt = f"""You are a browser automation agent. Your task is to help accomplish the following goal:

TASK: {task_description}

CURRENT PAGE STATE:
URL: {page_state.get('url', 'unknown')}
Title: {page_state.get('title', 'unknown')}

Page Content (first 500 chars):
{page_state.get('text_content', '')[:500]}

Interactive Elements Available:
{interactive_summary}

PREVIOUS ACTIONS:
{history_text if history else '  (none yet)'}

Based on the current page state and your task, decide the SINGLE next action to take.

AVAILABLE ACTIONS:
- navigate: Go to a URL
  Example: {{"type": "navigate", "url": "https://example.com", "thinking": "why"}}

- click: Click an element using its EXACT selector from the list above
  Example: {{"type": "click", "selector": "a:nth-of-type(3)", "thinking": "why"}}
  IMPORTANT: Copy the selector EXACTLY from [brackets] in the Interactive Elements list

- type: Type text into input using its EXACT selector from the list above
  Example: {{"type": "type", "selector": "#search", "text": "your search text here", "thinking": "why"}}
  IMPORTANT: Must include BOTH "selector" (exact from [brackets]) AND "text" (what to type)

- wait: Wait briefly
  Example: {{"type": "wait", "seconds": 2, "thinking": "why"}}

- scroll: Scroll down page
  Example: {{"type": "scroll", "thinking": "why"}}

- complete: Task is done
  Example: {{"type": "complete", "result": "description of what was accomplished", "thinking": "why"}}

- needs_attention: Need human help
  Example: {{"type": "needs_attention", "reason": "what you need", "thinking": "why"}}

CRITICAL RULES:
1. Return EXACTLY ONE action as JSON - no explanations, no multiple actions
2. For click/type actions: COPY the selector EXACTLY from the [brackets] in Interactive Elements
3. DO NOT invent selectors - use ONLY what is provided in the list above
4. DO NOT plan ahead - return ONLY the NEXT SINGLE step
5. If the task asks you to NAVIGATE to a site and you're already there, use "complete"
6. If the task asks you to READ/EXTRACT info and you can see it, use "complete" with the info
7. If you encounter login, captcha, or MFA, use "needs_attention"
8. If no matching element exists in the list, use "needs_attention"
9. NEVER repeat the same action - if it failed once, try something else or ask for help

Return ONLY ONE action as a SINGLE JSON object, nothing else:"""

        try:
            response = await self.generate(prompt)
            # Extract JSON from response (Ollama might add extra text)
            action_data = self._extract_json(response)

            if not action_data:
                # Debug: print what the model actually returned
                print(f"\n[DEBUG] Model response: {response[:500]}")
                return Action.error("Failed to parse action from AI response")

            # Validate and create Action
            return Action(**action_data)

        except Exception as e:
            print(f"\n[DEBUG] Error creating action: {str(e)}")
            print(f"[DEBUG] Action data: {action_data if 'action_data' in locals() else 'None'}")
            return Action.error(f"AI decision error: {str(e)}")

    def _summarize_interactive_elements(self, elements: list[dict]) -> str:
        """Create a concise summary of interactive elements."""
        if not elements:
            return "  (none found)"

        lines = []
        for i, elem in enumerate(elements[:20], 1):  # Limit to 20 elements
            elem_type = elem.get("type", "unknown")
            if elem_type == "button":
                text = elem.get("text", "")[:40]
                selector = elem.get("selector", "")
                lines.append(f"  [{selector}] - Button: '{text}'")
            elif elem_type == "link":
                text = elem.get("text", "")[:40]
                selector = elem.get("selector", "")
                lines.append(f"  [{selector}] - Link: '{text}'")
            elif elem_type == "input":
                input_type = elem.get("inputType", "text")
                placeholder = elem.get("placeholder", "")
                selector = elem.get("selector", "")
                name = elem.get("name", "")
                label = f"placeholder='{placeholder}'" if placeholder else f"name='{name}'" if name else input_type
                lines.append(f"  [{selector}] - Input ({input_type}): {label}")

        return "\n".join(lines) if lines else "  (no interactive elements)"

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract FIRST JSON object from text response."""
        # Try to find JSON in the response
        text = text.strip()

        # Look for FIRST JSON object only
        start = text.find("{")
        if start >= 0:
            # Find the matching closing brace
            brace_count = 0
            end = start
            for i, char in enumerate(text[start:], start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break

            if end > start:
                try:
                    json_str = text[start:end]
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

        # Try parsing the whole response
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    async def check_health(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
