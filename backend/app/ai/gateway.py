import os
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type, TypeVar
from pydantic import BaseModel
from groq import Groq

T = TypeVar("T", bound=BaseModel)

class AIProvider(ABC):
    @abstractmethod
    def generate_chat(self, messages: List[Dict[str, str]]) -> str:
        pass

    @abstractmethod
    def generate_structured(self, messages: List[Dict[str, str]], response_model: Type[T]) -> T:
        pass

class GroqProvider(AIProvider):
    def __init__(self, model_name: str = "openai/gpt-oss-120b"):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model_name = model_name

    def generate_chat(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model_name
        )
        return response.choices[0].message.content

    def generate_structured(self, messages: List[Dict[str, str]], response_model: Type[T]) -> T:
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model_name,
            response_format={"type": "json_object"},
            max_tokens=2000
        )
        raw_content = response.choices[0].message.content
        data = json.loads(raw_content)
        return response_model(**data)

# Singleton instance for the application
# If we ever switch to OpenAI, we just swap this instance
ai_gateway: AIProvider = GroqProvider()
