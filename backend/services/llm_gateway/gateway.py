# backend/services/llm_gateway/gateway.py
"""
LLM Gateway - Phase 0 minimal
Supports OpenAI and SiliconFlow.
"""
import httpx
from typing import List, Dict, Optional, Any
from config import settings


class LLMGateway:
    """LLM Gateway - Phase 0 minimal; supports OpenAI and SiliconFlow."""

    def __init__(self):
        self.providers = {
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "api_key": settings.openai_api_key,
                "headers": {
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
            },
            "siliconflow": {
                "base_url": settings.siliconflow_base_url,
                "api_key": getattr(settings, "siliconflow_api_key", ""),
                "headers": {
                    "Authorization": f"Bearer {getattr(settings, 'siliconflow_api_key', '')}",
                    "Content-Type": "application/json",
                },
            },
            "moonshot": {
                "base_url": settings.moonshot_base_url,
                "api_key": getattr(settings, "moonshot_api_key", ""),
                "headers": {
                    "Authorization": f"Bearer {getattr(settings, 'moonshot_api_key', '')}",
                    "Content-Type": "application/json",
                },
            },
            "qwen": {
                "base_url": settings.qwen_base_url,
                "api_key": getattr(settings, "qwen_api_key", ""),
                "headers": {
                    "Authorization": f"Bearer {getattr(settings, 'qwen_api_key', '')}",
                    "Content-Type": "application/json",
                },
            },
        }

    async def chat_completion(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        response_format: Optional[Dict[str, str]] = None,
        json_schema: Optional[Dict] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Unified LLM chat completion."""
        if provider is None:
            provider = settings.llm_provider

        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")

        provider_config = self.providers[provider]
        if not provider_config["api_key"]:
            raise ValueError(f"{provider} API key is not configured")

        if not messages:
            raise ValueError("messages must not be empty")

        if model is None:
            model = settings.llm_model

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if response_format:
            payload["response_format"] = response_format

        if json_schema and provider == "siliconflow":
            payload["response_format"] = {
                "type": "json_object",
                "schema": json_schema,
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{provider_config['base_url']}/chat/completions",
                headers=provider_config["headers"],
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

        return {
            "content": result["choices"][0]["message"]["content"],
            "model": result.get("model", model),
            "usage": result.get("usage", {}),
            "provider": provider,
        }

    async def vision_completion(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        images: Optional[List[str]] = None,
        prompt: Optional[str] = None,
        response_format: Optional[Dict[str, str]] = None,
        json_schema: Optional[Dict] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """Unified vision completion for image inputs."""
        if provider is None:
            provider = settings.llm_provider

        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")

        provider_config = self.providers[provider]
        if not provider_config["api_key"]:
            raise ValueError(f"{provider} API key is not configured")

        if not images:
            raise ValueError("images must not be empty")

        if model is None:
            model = settings.llm_model

        content = []
        for image in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": image},
            })

        if prompt:
            content.append({"type": "text", "text": prompt})

        messages = [{"role": "user", "content": content}]

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{provider_config['base_url']}/chat/completions",
                headers=provider_config["headers"],
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

        return {
            "content": result["choices"][0]["message"]["content"],
            "model": result.get("model", model),
            "usage": result.get("usage", {}),
            "provider": provider,
        }
