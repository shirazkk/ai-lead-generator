import logging
import asyncio
import json
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from config import settings

logger = logging.getLogger(__name__)

# --- Base Interface ---
class BaseLLMProvider(ABC):
    @abstractmethod
    async def analyze_lead(self, business_data: Dict[str, Any], prompt: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a business lead."""
        pass

    @abstractmethod
    async def generate_outreach(self, lead_data: Dict[str, Any], analysis: Dict[str, Any], tone: Optional[str] = "friendly", prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate personalized outreach email."""
        pass

    async def _generate_with_retry(
        self,
        operation_name: str,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """Shared retry logic for LLM calls."""
        for attempt in range(max_retries):
            try:
                logger.info(f"{operation_name}: Attempt {attempt + 1}/{max_retries}")
                return await self._execute_generation(**kwargs)
            except Exception as e:
                logger.warning(f"{operation_name}: Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise Exception(f"{operation_name} failed after {max_retries} attempts: {e}")
        raise Exception("Unreachable")

    @abstractmethod
    async def _execute_generation(self, **kwargs) -> Dict[str, Any]:
        """Actual provider-specific generation call."""
        pass

# --- Gemini Implementation ---
class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model_name = settings.gemini_model
        logger.info(f"Initialized GeminiProvider with model {self.model_name}")

    async def analyze_lead(self, business_data: Dict[str, Any], prompt: Optional[str] = None) -> Dict[str, Any]:
        schema = {
            "type": "object",
            "properties": {
                "opportunity_score": {"type": "integer"},
                "identified_problem": {"type": "string"},
                "website_benefits": {"type": "string"},
                "estimated_value": {"type": "string"}
            },
            "required": ["opportunity_score", "identified_problem", "website_benefits", "estimated_value"]
        }
        if not prompt: prompt = f"Analyze business: {business_data.get('name', 'Unknown')}"
        return await self._generate_with_retry(
            operation_name="analyze_lead",
            prompt=prompt,
            generation_config=GenerationConfig(response_mime_type="application/json", response_schema=schema)
        )

    async def generate_outreach(self, lead_data: Dict[str, Any], analysis: Dict[str, Any], tone: Optional[str] = "friendly", prompt: Optional[str] = None) -> Dict[str, Any]:
        schema = {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["subject", "message"]
        }
        if not prompt: prompt = f"Generate outreach for {lead_data.get('name', 'Unknown')}"
        return await self._generate_with_retry(
            operation_name="generate_outreach",
            prompt=prompt,
            generation_config=GenerationConfig(response_mime_type="application/json", response_schema=schema)
        )

    async def _execute_generation(self, **kwargs) -> Dict[str, Any]:
        prompt = kwargs["prompt"]
        config = kwargs["generation_config"]
        model = genai.GenerativeModel(self.model_name, generation_config=config)
        response = await asyncio.to_thread(model.generate_content, prompt)
        return json.loads(response.text)

# --- OpenRouter Implementation ---
class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = settings.openrouter_model
        logger.info(f"Initialized OpenRouterProvider with model {self.model}")

    async def analyze_lead(self, business_data: Dict[str, Any], prompt: Optional[str] = None) -> Dict[str, Any]:
        if not prompt: prompt = f"Analyze business: {business_data.get('name', 'Unknown')}"
        return await self._generate_with_retry(operation_name="analyze_lead", prompt=prompt)

    async def generate_outreach(self, lead_data: Dict[str, Any], analysis: Dict[str, Any], tone: Optional[str] = "friendly", prompt: Optional[str] = None) -> Dict[str, Any]:
        if not prompt: prompt = f"Generate outreach for {lead_data.get('name', 'Unknown')}"
        return await self._generate_with_retry(operation_name="generate_outreach", prompt=prompt)

    async def _execute_generation(self, **kwargs) -> Dict[str, Any]:
        prompt = kwargs["prompt"]
        headers = {"Authorization": f"Bearer {self.api_key}", "HTTP-Referer": "https://localhost", "X-Title": "AI Lead Generator"}
        data = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return json.loads(response.json()["choices"][0]["message"]["content"])

# --- Orchestrator ---
class LLMService:
    def __init__(self, api_key: str):
        # OpenRouter as primary, Gemini as failover
        self.providers = {
            "primary": OpenRouterProvider(api_key=settings.openrouter_api_key) if settings.openrouter_api_key else None,
            "failover": GeminiProvider(api_key=api_key)
        }
        # Start with primary if available, else failover
        self.active_provider_key = "primary" if self.providers["primary"] else "failover"
        logger.info(f"Initialized LLMService. Active provider: {self.active_provider_key}")

    async def _execute(self, method_name: str, *args, **kwargs) -> Dict[str, Any]:
        # Try active provider
        try:
            return await getattr(self.providers[self.active_provider_key], method_name)(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Active provider {self.active_provider_key} failed: {e}")
            
            # Switch to the other provider
            new_key = "failover" if self.active_provider_key == "primary" else "primary"
            if not self.providers.get(new_key):
                raise Exception(f"Provider {self.active_provider_key} failed, and no alternative provider is configured.")
            
            self.active_provider_key = new_key
            logger.info(f"Switching to provider: {self.active_provider_key}")
            
            # Try the new active provider
            return await getattr(self.providers[self.active_provider_key], method_name)(*args, **kwargs)

    async def analyze_lead(self, business_data: Dict[str, Any], prompt: Optional[str] = None) -> Dict[str, Any]:
        return await self._execute("analyze_lead", business_data, prompt)

    async def generate_outreach(self, lead_data: Dict[str, Any], analysis: Dict[str, Any], tone: Optional[str] = "friendly", prompt: Optional[str] = None) -> Dict[str, Any]:
        return await self._execute("generate_outreach", lead_data, analysis, tone, prompt)
