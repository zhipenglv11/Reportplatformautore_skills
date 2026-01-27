"""
Qwen-VL Client for Vision-Language Tasks
通义千问多模态客户端
"""

import base64
import logging
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from dashscope import MultiModalConversation
    import dashscope
except ImportError:
    raise ImportError("dashscope is required. Install with: pip install dashscope")


logger = logging.getLogger(__name__)


class QwenVLClient:
    """Client for Qwen-VL multimodal model."""
    
    def __init__(
        self,
        api_key: str,
        model_name: str = 'qwen-vl-max-latest',
        timeout: int = 60
    ):
        """
        Initialize Qwen-VL client.
        
        Args:
            api_key: DashScope API key
            model_name: Model name
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        
        # Set API key
        dashscope.api_key = api_key
    
    def extract(
        self,
        image_path: str,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> str:
        """
        Extract data from image using Qwen-VL.
        
        Args:
            image_path: Path to image file
            system_prompt: System instruction
            user_prompt: User query/instruction
            **kwargs: Additional parameters
            
        Returns:
            Model response text
            
        Raises:
            Exception: If API call fails
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Construct messages
        messages = [
            {
                'role': 'system',
                'content': [{'text': system_prompt}]
            },
            {
                'role': 'user',
                'content': [
                    {'image': f'data:image/jpeg;base64,{image_data}'},
                    {'text': user_prompt}
                ]
            }
        ]
        
        try:
            logger.info(f"Calling Qwen-VL API with model: {self.model_name}")
            
            response = MultiModalConversation.call(
                model=self.model_name,
                messages=messages,
                timeout=self.timeout,
                **kwargs
            )
            
            if response.status_code == 200:
                result = response.output.choices[0].message.content[0]['text']
                logger.info("Qwen-VL API call successful")
                return result
            else:
                error_msg = f"Qwen-VL API error: {response.code} - {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Failed to call Qwen-VL API: {e}")
            raise
    
    def validate_response(self, response: str) -> bool:
        """
        Validate API response.
        
        Args:
            response: Response text
            
        Returns:
            True if response is valid
        """
        return bool(response and len(response) > 0)
