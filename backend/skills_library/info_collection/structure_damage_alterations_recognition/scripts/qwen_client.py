"""
Qwen VL Model Client
通义千问视觉模型客户端
"""

import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
import dashscope
from dashscope import MultiModalConversation


class QwenClient:
    """通义千问VL模型客户端"""

    def __init__(self, api_key: str, model: str = 'qwen-vl-max-latest',
                 max_retries: int = 3, timeout: int = 60):
        """
        初始化客户端
        
        Args:
            api_key: DashScope API Key
            model: 模型名称
            max_retries: 最大重试次数
            timeout: 超时时间(秒)
        """
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        
        # 设置API Key
        dashscope.api_key = api_key

    def extract(self, image_path: str, messages: List[Dict[str, Any]],
                json_schema: Optional[Dict[str, Any]] = None) -> str:
        """
        从图片中提取数据
        
        Args:
            image_path: 图片路径
            messages: 消息列表
            json_schema: JSON Schema(可选)
            
        Returns:
            模型响应文本
        """
        # 准备消息
        qwen_messages = self._prepare_messages(image_path, messages)

        # 调用API
        for attempt in range(self.max_retries):
            try:
                response = MultiModalConversation.call(
                    model=self.model,
                    messages=qwen_messages
                )

                if response.status_code == 200:
                    # 提取响应文本
                    result_text = response.output.choices[0].message.content[0]['text']
                    return result_text
                else:
                    error_msg = f"API调用失败: {response.code} - {response.message}"
                    if attempt < self.max_retries - 1:
                        print(f"重试 {attempt + 1}/{self.max_retries}: {error_msg}")
                        continue
                    else:
                        raise Exception(error_msg)

            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"重试 {attempt + 1}/{self.max_retries}: {str(e)}")
                    continue
                else:
                    raise

        raise Exception(f"达到最大重试次数({self.max_retries})")

    def _prepare_messages(self, image_path: str,
                         messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        准备Qwen格式的消息
        
        Args:
            image_path: 图片路径
            messages: 原始消息列表
            
        Returns:
            Qwen格式的消息列表
        """
        qwen_messages = []

        # 处理系统消息和用户消息
        system_content = ""
        user_content = ""

        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')

            if role == 'system':
                system_content = content
            elif role == 'user':
                user_content = content

        # 合并系统提示和用户提示
        combined_text = f"{system_content}\n\n{user_content}".strip()

        # 读取图片
        image_url = self._image_to_url(image_path)

        # 构建Qwen消息格式
        qwen_messages.append({
            'role': 'user',
            'content': [
                {'image': image_url},
                {'text': combined_text}
            ]
        })

        return qwen_messages

    def _image_to_url(self, image_path: str) -> str:
        """
        将图片转换为URL或base64
        
        Args:
            image_path: 图片路径
            
        Returns:
            图片URL
        """
        image_path = Path(image_path)

        # 如果是URL,直接返回
        if str(image_path).startswith(('http://', 'https://')):
            return str(image_path)

        # 否则使用file://协议
        return f"file://{image_path.absolute()}"

    def test_connection(self) -> tuple[bool, str]:
        """
        测试API连接
        
        Returns:
            (是否成功, 消息)
        """
        try:
            # 简单的API调用测试
            response = dashscope.Generation.call(
                model='qwen-turbo',
                prompt='Hello',
                max_tokens=10
            )

            if response.status_code == 200:
                return True, "连接成功"
            else:
                return False, f"连接失败: {response.code} - {response.message}"

        except Exception as e:
            return False, f"连接失败: {str(e)}"
