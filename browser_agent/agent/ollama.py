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
- navigate: Go to a URL - {{"type": "navigate", "url": "https://example.com", "thinking": "why"}}
- click: Click an element - {{"type": "click", "selector": "button:nth-of-type(1)", "thinking": "why"}}
- type: Type text into input - {{"type": "type", "selector": "#search", "text": "query", "thinking": "why"}}
- wait: Wait briefly - {{"type": "wait", "seconds": 2, "thinking": "why"}}
- scroll: Scroll down page - {{"type": "scroll", "thinking": "why"}}
- complete: Task is done - {{"type": "complete", "result": "description of what was accomplished", "thinking": "why"}}
- needs_attention: Need human help - {{"type": "needs_attention", "reason": "what you need", "thinking": "why"}}

RULES:
1. Return ONLY valid JSON for one action
2. Use exact selectors from Interactive Elements list
3. For text input, use the selector from the input elements
4. Include "thinking" to explain your reasoning
5. If the task asks you to NAVIGATE to a site and you're already there, use "complete"
6. If the task asks you to READ/EXTRACT info and you can see it, use "complete" with the info
7. If you encounter login, captcha, or MFA, use "needs_attention"
8. If stuck or repeating the same action, use "needs_attention"
9. NEVER repeat the same navigation - if you navigated once, look at the result

Return the next action as JSON:"""

        try:
            response = await self.generate(prompt)
            # Extract JSON from response (Ollama might add extra text)
            action_data = self._extract_json(response)

            if not action_data:
                return Action.error("Failed to parse action from AI response")

            # Validate and create Action
            return Action(**action_data)

        except Exception as e:
            return Action.error(f"AI decision error: {str(e)}")

    def _summarize_interactive_elements(self, elements: list[dict]) -> str:
        """Create a concise summary of interactive elements."""
        if not elements:
            return "  (none found)"

        lines = []
        for i, elem in enumerate(elements[:20], 1):  # Limit to 20 elements
            elem_type = elem.get("type", "unknown")
            if elem_type == "button":
                text = elem.get("text", "")[:50]
                selector = elem.get("selector", "")
                lines.append(f"  {i}. Button: '{text}' [{selector}]")
            elif elem_type == "link":
                text = elem.get("text", "")[:50]
                href = elem.get("href", "")
                lines.append(f"  {i}. Link: '{text}' -> {href}")
            elif elem_type == "input":
                input_type = elem.get("inputType", "text")
                placeholder = elem.get("placeholder", "")
                selector = elem.get("selector", "")
                lines.append(f"  {i}. Input ({input_type}): placeholder='{placeholder}' [{selector}]")

        return "\n".join(lines) if lines else "  (no interactive elements)"

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON object from text response."""
        # Try to find JSON in the response
        text = text.strip()

        # Look for JSON object patterns
        start = text.find("{")
        end = text.rfind("}") + 1

        if start >= 0 and end > start:
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
