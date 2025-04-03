from abc import ABC, abstractmethod
from typing import List, Dict

class ModelBackend(ABC):

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]]) -> str:
        """Generates a response based on the provided messages.

        Args:
            messages (List[Dict[str, str]]): A list of messages.

        Returns:
            str: The generated response.
        """
        pass
    
    def _format_messages_history(self, messages) -> str:
        """Format the conversation history for the LLM."""
        formatted = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                formatted += f"<|system|>{content}"
            elif role == "user":
                formatted += f"<|user|>{content}"
            elif role == "assistant":
                formatted += f"<|assistant|>{content}"
        return formatted + "<|assistant|>"
    
    def _format_response(self, response) -> str:
        """Format the response from the LLM."""
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()
            if "<|user|>" in response:
                response = response.split("<|user|>")[0].strip()
        return response