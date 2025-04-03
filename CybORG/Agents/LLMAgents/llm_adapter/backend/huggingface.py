import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict
from CybORG.Agents.LLMAgents.llm_adapter.backend.model_backend import ModelBackend

import weave


DEVICE = "cuda" if torch.cuda.is_available() else "cpu" # Optimization for GPU

class HuggingFaceBackend(ModelBackend):
    """Hugging Face model backend."""

    def __init__(self, hyperparams: dict, token: str):
        self.hyperparams = hyperparams
        self.token = token
        self.model = AutoModelForCausalLM.from_pretrained(
            self.hyperparams["model_name"],
            load_in_8bit=self.hyperparams["load_in_8bit"],
            token=self.token,
        ).to(DEVICE)
        self.tokenizer = AutoTokenizer.from_pretrained(self.hyperparams["model_name"])

    @weave.op
    def generate(self, messages: List[Dict[str, str]]) -> str:
        formatted_prompt = self._format_messages_history(messages)
        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.hyperparams["generate"]["max_length"],
        ).to(DEVICE)
        
        with torch.no_grad():
            generate_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.hyperparams["generate"]["max_new_tokens"],
                do_sample=self.hyperparams["generate"]["do_sample"],
                top_p=self.hyperparams["generate"]["top_p"],
                temperature=self.hyperparams["generate"]["temperature"],
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
    
        response = self.tokenizer.batch_decode(generate_ids, skip_special_tokens=True)[0]
        return self._format_response(response)