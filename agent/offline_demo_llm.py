"""TEST-ONLY scripted LLM for checking LangChain tool orchestration offline.

NOT an artificial intelligence model. It never chooses a tool intelligently;
each test case explicitly supplies its desired tool and argument.
"""
from __future__ import annotations
from typing import Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ScriptedOfflineChatModel(BaseChatModel):
    planned_tool: str
    planned_args: dict[str, str]

    @property
    def _llm_type(self) -> str:
        return "scripted-offline-test-only"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        # Only supports the predetermined action below; not a real tool router.
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        recent_tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        if recent_tool_messages:
            observation = str(recent_tool_messages[-1].content)
            message = AIMessage(content="OFFLINE DEMO ONLY — predetermined tool result: " + observation)
        else:
            message = AIMessage(
                content="",
                tool_calls=[{
                    "name": self.planned_tool,
                    "args": self.planned_args,
                    "id": "offline_test_call_001",
                    "type": "tool_call",
                }],
            )
        return ChatResult(generations=[ChatGeneration(message=message)])


class MockTavilySearch:
    """Produces *fictional* result data, never evidence for a factual answer."""
    def invoke(self, inputs: dict) -> dict:
        return {"results": [{
            "title": "DEMO ONLY — test source",
            "url": "https://example.org/offline-demo-only",
            "content": "Synthetic search snippet used only to check tool plumbing.",
        }]}
