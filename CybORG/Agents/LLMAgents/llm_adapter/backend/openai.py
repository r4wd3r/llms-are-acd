from openai import OpenAI
from typing import List, Dict
from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend
import weave

from CybORG.Agents.LLMAgents.llm_adapter.utils.logger import Logger
class OpenAIBackend(ModelBackend):
    """OpenAI model backend."""

    def __init__(self, hyperparams: dict, api_key: str):
        self.openai_client = OpenAI(api_key=api_key) 
        self.model_name = hyperparams["model_name"].lower()
        self.temperature = hyperparams["generate"]["temperature"]
        self.max_tokens = hyperparams["generate"]["max_new_tokens"]

    @weave.op
    def generate(self, messages: List[Dict[str, str]]) -> str:
        formatted_prompt = self._format_messages_history(messages)
        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": formatted_prompt}], 
            max_tokens=self.max_tokens,
            temperature=self.temperature
        ).choices[0].message.content
        # TODO: Keep track of token usage
        return self._format_response(response)
    
    
class NewOpenAIBackend(ModelBackend):
    """OpenAI model backend for new models"""

    def __init__(self, hyperparams: dict, api_key: str):
        self.openai_client = OpenAI(api_key=api_key) 
        self.model_name = hyperparams["model_name"].lower()
        self.temperature = hyperparams["generate"]["temperature"]
        self.max_tokens = hyperparams["generate"]["max_new_tokens"]

    @weave.op
    def generate(self, messages: List[Dict[str, str]]) -> str:
        formatted_prompt = self._format_messages_history(messages)
        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": formatted_prompt}]
        ).choices[0].message.content
        Logger.info(f"Generated response: {response}")
        # TODO: Keep track of token usage
        return self._format_response(response)