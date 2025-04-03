from typing import Dict, List
from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend
from CybORG.Agents.LLMAgents.llm_adapter.utils.logger import Logger
from openai import OpenAI
import weave


class DeepSeekBackend(ModelBackend):
    """DeepSeek model backend."""

    def __init__(self, hyperparams: dict, api_key: str):
        self.headers={
            "HTTP-Referer": "https://github.com/cage-paper/cage-4",
            "X-Title": "CAGE Project"
        }
        
        self.openai_client = OpenAI(base_url="https://openrouter.ai/api/v1", 
                                    api_key=api_key)
        self.model_name = hyperparams.get("model_name", "").lower()
        self.temperature = hyperparams["generate"]["temperature"]
        self.max_tokens = hyperparams["generate"]["max_new_tokens"]

    @weave.op
    def generate(self, messages: List[Dict[str, str]]) -> str:
        formatted_prompt = self._format_messages_history(messages)
        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": formatted_prompt}], 
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            extra_headers=self.headers,
            extra_body={}
        ).choices[0].message.content
        Logger.info(f"Generated response: {response}")
        return self._format_response(response)