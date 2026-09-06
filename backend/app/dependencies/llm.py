from typing import Annotated

from fastapi import Depends
from functools import lru_cache
from openai import OpenAI

from app.services.chat.llm_service import LLMService
from app.core.config import settings

@lru_cache
def get_llm_service():
    """
    Creates the shared LLM service using Openrouter
    """

    client = OpenAI(api_key=settings.OPENROUTER_API_KEY,base_url=settings.OPENROUTER_BASE_URL)

    return LLMService(client=client,model="openai/gpt-4o-mini")

    
    
LLMServiceDEP = Annotated[
    LLMService,
    Depends(get_llm_service)
]