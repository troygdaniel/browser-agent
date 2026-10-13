"""Action definitions for browser automation."""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel


class ActionType(str, Enum):
    """Types of actions the agent can take."""

    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    SCROLL = "scroll"
    COMPLETE = "complete"
    NEEDS_ATTENTION = "needs_attention"
    ERROR = "error"


class Action(BaseModel):
    """Represents an action to be executed."""

    type: ActionType
    selector: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None
    seconds: Optional[float] = None
    result: Optional[str] = None
    reason: Optional[str] = None
    thinking: Optional[str] = None  # Agent's reasoning

    @classmethod
    def navigate(cls, url: str, thinking: str = "") -> "Action":
        return cls(type=ActionType.NAVIGATE, url=url, thinking=thinking)

    @classmethod
    def click(cls, selector: str, thinking: str = "") -> "Action":
        return cls(type=ActionType.CLICK, selector=selector, thinking=thinking)

    @classmethod
    def type_text(cls, selector: str, text: str, thinking: str = "") -> "Action":
        return cls(type=ActionType.TYPE, selector=selector, text=text, thinking=thinking)

    @classmethod
    def wait(cls, seconds: float = 1.0, thinking: str = "") -> "Action":
        return cls(type=ActionType.WAIT, seconds=seconds, thinking=thinking)

    @classmethod
    def scroll(cls, thinking: str = "") -> "Action":
        return cls(type=ActionType.SCROLL, thinking=thinking)

    @classmethod
    def complete(cls, result: str, thinking: str = "") -> "Action":
        return cls(type=ActionType.COMPLETE, result=result, thinking=thinking)

    @classmethod
    def needs_attention(cls, reason: str, thinking: str = "") -> "Action":
        return cls(type=ActionType.NEEDS_ATTENTION, reason=reason, thinking=thinking)

    @classmethod
    def error(cls, reason: str) -> "Action":
        return cls(type=ActionType.ERROR, reason=reason)
