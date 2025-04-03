import os
from CybORG.Agents.LLMAgents.llm_adapter.backend.deepseek import DeepSeekBackend
from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend
from CybORG.Agents.LLMAgents.llm_adapter.backend.openai import OpenAIBackend
from CybORG.Agents.LLMAgents.llm_adapter.backend.openai import NewOpenAIBackend
from CybORG.Agents.LLMAgents.llm_adapter.backend.huggingface import HuggingFaceBackend
from CybORG.Agents.LLMAgents.llm_adapter.backend.dummy import DummyBackend


HF_TOKEN = os.environ.get("HF_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

class BackendFactory:
    """Factory class for creating model backend instances."""

    @staticmethod
    def create_backend(backend_name: str, hyperparams: dict) -> ModelBackend:
        if backend_name == "openai":
            return OpenAIBackend(hyperparams=hyperparams, api_key=OPENAI_API_KEY)
        elif backend_name == "huggingface":
            return HuggingFaceBackend(hyperparams=hyperparams, token=HF_TOKEN)
        elif backend_name == "new-openai":
            return NewOpenAIBackend(hyperparams=hyperparams, api_key=OPENAI_API_KEY)
        elif backend_name == "deepseek":
            if not OPENROUTER_API_KEY:
                    raise ValueError("OPENROUTER_API_KEY environment variable is required for DeepSeek models")
            return DeepSeekBackend(hyperparams=hyperparams, api_key=OPENROUTER_API_KEY)
        elif backend_name == "dummy":
            return DummyBackend()
        else:
            raise ValueError(f"Invalid backend: {backend_name}")

class ModelManager:
    """Model manager class.
    
    This class is responsible for managing the model backend instances, sending messages to the model backend,
    handling the responses, and storing the model configurations.
    """
    def __init__(self, hyperparams: dict):
        self.hyperparams = hyperparams
        self.backend_name = hyperparams["backend"].lower()
        self.model_backend = BackendFactory.create_backend(self.backend_name, hyperparams)
    
    def generate_response(self, message: str) -> str:
        """Generates a response using the model backend."""
        return self.model_backend.generate(message)