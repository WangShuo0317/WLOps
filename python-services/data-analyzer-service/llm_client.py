"""
LLM客户端封装
支持OpenAI API和兼容接口
"""
from typing import Optional
from loguru import logger
from config import config

class LLMClient:
    """LLM客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.base_url = base_url or config.OPENAI_BASE_URL
        self.model = model or config.OPENAI_MODEL
        
        if not self.api_key:
            logger.warning("OpenAI API Key未配置，LLM功能将不可用")
            self.client = None
        else:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                logger.info(f"LLM客户端初始化成功，模型: {self.model}")
            except Exception as e:
                logger.error(f"LLM客户端初始化失败: {e}")
                self.client = None
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            生成的文本
        """
        if not self.client:
            raise Exception("LLM客户端未初始化")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的数据分析和生成助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM生成失败: {e}")
            raise
    
    def is_available(self) -> bool:
        """检查LLM是否可用"""
        return self.client is not None
