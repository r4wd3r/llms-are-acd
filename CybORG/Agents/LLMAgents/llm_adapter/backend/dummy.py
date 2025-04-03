from openai import OpenAI
from typing import List, Dict
from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend
import weave

class DummyBackend(ModelBackend):
    """Dummy model backend for testing."""

    def generate(self, messages: List[Dict[str, str]]) -> str:
        response = "Dummy response."
        return self._format_response(response)