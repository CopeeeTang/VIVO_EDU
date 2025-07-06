# -*- coding: utf-8 -*-
import os
import time
import uuid
import hmac
import hashlib
import json
import asyncio
import aiohttp
import requests
import base64
import urllib.parse
from typing import Optional, Dict, Any, List, Union
from openai import OpenAI, AsyncOpenAI
from enum import Enum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK_V3 = "deepseek_v3"
    DEEPSEEK_R1 = "deepseek_r1"
    VIVO_BLUE_LM = "vivo_blue_lm"
    ZHIZENGZENG = "zhizengzeng"


class VivoAuth:
    """vivo API鉴权工具类"""
    
    @staticmethod
    def gen_sign_headers(app_id: str, app_key: str, method: str, uri: str, params: dict = None) -> dict:
        """生成vivo API签名头部"""
        timestamp = str(int(time.time()))
        nonce = str(uuid.uuid4())[:8]
        
        signed_headers = "x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce"
        
        # 生成canonical_query_string
        canonical_query_string = ""
        if params:
            # URL编码并按字典顺序排序
            encoded_params = []
            for k, v in sorted(params.items()):
                encoded_key = urllib.parse.quote(str(k), safe='')
                encoded_value = urllib.parse.quote(str(v), safe='')
                encoded_params.append(f"{encoded_key}={encoded_value}")
            canonical_query_string = "&".join(encoded_params)
        
        # 生成signed_headers_string
        signed_headers_string = f"x-ai-gateway-app-id:{app_id}\nx-ai-gateway-timestamp:{timestamp}\nx-ai-gateway-nonce:{nonce}"
        
        # 生成signing_string
        signing_string = f"{method}\n{uri}\n{canonical_query_string}\n{app_id}\n{timestamp}\n{signed_headers_string}"
        
        # 计算签名
        signature = base64.b64encode(
            hmac.new(
                app_key.encode('utf-8'),
                signing_string.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return {
            'X-AI-GATEWAY-APP-ID': app_id,
            'X-AI-GATEWAY-TIMESTAMP': timestamp,
            'X-AI-GATEWAY-NONCE': nonce,
            'X-AI-GATEWAY-SIGNED-HEADERS': signed_headers,
            'X-AI-GATEWAY-SIGNATURE': signature
        }


class VivoBlueLMClient:
    """vivo蓝心大模型API客户端"""
    
    def __init__(self, app_id: str, app_key: str, base_url: str = 'https://api-ai.vivo.com.cn'):
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = base_url
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """同步聊天完成"""
        model = kwargs.get('model', 'vivo-BlueLM-TB-Pro')
        temperature = kwargs.get('temperature', 0.9)
        max_tokens = kwargs.get('max_new_tokens', 2048)
        tools = kwargs.get('tools', None)
        
        request_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # 准备请求参数
        params = {'requestId': request_id}
        
        # 准备请求体
        data = {
            'messages': messages,
            'model': model,
            'sessionId': session_id,
            'extra': {
                'temperature': temperature,
                'max_new_tokens': max_tokens
            }
        }
        
        # 如果有tools，添加到请求体中
        if tools:
            data['tools'] = tools
        
        # 生成签名头部
        headers = VivoAuth.gen_sign_headers(
            self.app_id, 
            self.app_key, 
            'POST', 
            '/vivogpt/completions',
            params
        )
        headers['Content-Type'] = 'application/json'
        
        try:
            url = f"{self.base_url}/vivogpt/completions"
            response = requests.post(
                url,
                json=data,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0 and result.get('data'):
                    return result['data']['content']
                else:
                    raise Exception(f"vivo API返回错误: {result.get('msg', 'Unknown error')}")
            else:
                raise Exception(f"vivo API请求失败: {response.status_code}, {response.text}")
                
        except Exception as e:
            logger.error(f"vivo蓝心大模型API调用失败: {e}")
            raise
    
    def chat_completion_with_function_calling(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **kwargs) -> str:
        """支持function calling的聊天完成"""
        # 构建system prompt，包含function calling格式
        system_message = {
            "role": "system",
            "content": self._build_function_calling_system_prompt(tools)
        }
        
        # 合并messages
        all_messages = [system_message] + messages
        
        return self.chat_completion(all_messages, **kwargs)
    
    def _build_function_calling_system_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """构建function calling的system prompt"""
        tools_json = json.dumps(tools, ensure_ascii=False, indent=2)
        
        return f"""你是一个AI助手，尽你所能回答用户的问题。

你可以使用的工具如下:
<APIs>
{tools_json}
</APIs>

如果用户的问题需要调用工具，输出格式为：
<APIs>
[{{"name": "函数名","parameters": {{"参数名": "参数"}}}}]
</APIs>
否则直接回复用户。"""
    
    async def chat_completion_async(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """异步聊天完成"""
        model = kwargs.get('model', 'vivo-BlueLM-TB-Pro')
        temperature = kwargs.get('temperature', 0.9)
        max_tokens = kwargs.get('max_new_tokens', 2048)
        tools = kwargs.get('tools', None)
        
        request_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # 准备请求参数
        params = {'requestId': request_id}
        
        # 准备请求体
        data = {
            'messages': messages,
            'model': model,
            'sessionId': session_id,
            'extra': {
                'temperature': temperature,
                'max_new_tokens': max_tokens
            }
        }
        
        # 如果有tools，添加到请求体中
        if tools:
            data['tools'] = tools
        
        # 生成签名头部
        headers = VivoAuth.gen_sign_headers(
            self.app_id, 
            self.app_key, 
            'POST', 
            '/vivogpt/completions',
            params
        )
        headers['Content-Type'] = 'application/json'
        
        try:
            url = f"{self.base_url}/vivogpt/completions"
            
            # 调试日志
            logger.debug(f"vivo API异步调用URL: {url}")
            logger.debug(f"vivo API异步调用参数: {params}")
            logger.debug(f"vivo API异步调用头部: {headers}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=data,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    # 获取响应内容类型
                    content_type = response.headers.get('Content-Type', '')
                    logger.debug(f"vivo API响应状态: {response.status}, Content-Type: {content_type}")
                    
                    if response.status == 200:
                        # 检查响应内容类型
                        if 'application/json' in content_type:
                            result = await response.json()
                            if result.get('code') == 0 and result.get('data'):
                                return result['data']['content']
                            else:
                                raise Exception(f"vivo API返回错误: {result.get('msg', 'Unknown error')}")
                        else:
                            # 返回的不是JSON，获取文本内容用于调试
                            text = await response.text()
                            logger.error(f"vivo API返回非JSON响应: {text[:500]}")
                            raise Exception(f"vivo API返回非JSON响应，Content-Type: {content_type}")
                    else:
                        text = await response.text()
                        logger.error(f"vivo API请求失败: {response.status}, {text[:500]}")
                        raise Exception(f"vivo API请求失败: {response.status}, {text[:200]}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"vivo蓝心大模型API异步调用网络错误: {e}")
            raise Exception(f"网络请求失败: {e}")
        except Exception as e:
            logger.error(f"vivo蓝心大模型API异步调用失败: {e}")
            raise


class ZhizengzengClient:
    """zhizengzeng API客户端"""
    
    def __init__(self, api_key: str, base_url: str = 'https://api.zhizengzeng.com'):
        self.api_key = api_key
        self.base_url = base_url
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """同步聊天完成"""
        model = kwargs.get('model', 'gpt-4.1')
        temperature = kwargs.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens', 2048)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        try:
            url = f"{self.base_url}/v1/chat/completions"
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    raise Exception(f"zhizengzeng API返回无效响应: {result}")
            else:
                raise Exception(f"zhizengzeng API请求失败: {response.status_code}, {response.text}")
                
        except Exception as e:
            logger.error(f"zhizengzeng API调用失败: {e}")
            raise
    
    async def chat_completion_async(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """异步聊天完成"""
        model = kwargs.get('model', 'gpt-4.1')
        temperature = kwargs.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens', 2048)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        try:
            url = f"{self.base_url}/v1/chat/completions"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        if result.get('choices') and len(result['choices']) > 0:
                            return result['choices'][0]['message']['content']
                        else:
                            raise Exception(f"zhizengzeng API返回无效响应: {result}")
                    else:
                        text = await response.text()
                        raise Exception(f"zhizengzeng API请求失败: {response.status}, {text}")
                        
        except Exception as e:
            logger.error(f"zhizengzeng API异步调用失败: {e}")
            raise


class UnifiedAPIClient:
    """统一API客户端管理器"""
    
    def __init__(self):
        self.vivo_client = None
        self.openai_client = None
        self.deepseek_v3_client = None
        self.deepseek_r1_client = None
        self.zhizengzeng_client = None
        self._init_clients()
    
    def _init_clients(self):
        """初始化所有客户端"""
        try:
            # 初始化vivo客户端
            vivo_app_id = os.getenv('VIVO_BLUE_LM_APP_ID')
            vivo_app_key = os.getenv('VIVO_BLUE_LM_APP_KEY')
            if vivo_app_id and vivo_app_key:
                self.vivo_client = VivoBlueLMClient(vivo_app_id, vivo_app_key)
                logger.info("vivo客户端初始化成功")
            
            # 初始化OpenAI客户端
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("OpenAI客户端初始化成功")
            
            # 初始化DeepSeek客户端（火山引擎）
            deepseek_api_key = "a306bf91-ca05-442f-b09d-8ebaca556f0a"
            deepseek_base_url = "https://ark.cn-beijing.volces.com/api/v3"
            
            self.deepseek_v3_client = OpenAI(
                api_key=deepseek_api_key,
                base_url=deepseek_base_url
            )
            self.deepseek_r1_client = OpenAI(
                api_key=deepseek_api_key,
                base_url=deepseek_base_url,
                timeout=10
            )
            logger.info("DeepSeek客户端（火山引擎）初始化成功")
            
            # 初始化zhizengzeng客户端
            zhizengzeng_api_key = os.getenv('ZHIZENGZENG_API_KEY')
            if zhizengzeng_api_key:
                self.zhizengzeng_client = ZhizengzengClient(zhizengzeng_api_key)
                logger.info("zhizengzeng客户端初始化成功")
                
        except Exception as e:
            logger.error(f"初始化API客户端失败: {e}")
    
    def chat_with_fallback(self, system_prompt: str, user_input: str, **kwargs) -> str:
        """使用回退策略的聊天完成"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # 优先使用vivo
        if self.vivo_client:
            try:
                logger.info("尝试使用vivo客户端")
                return self.vivo_client.chat_completion(messages, **kwargs)
            except Exception as e:
                logger.warning(f"vivo客户端调用失败: {e}")
        
        # 回退到zhizengzeng
        if self.zhizengzeng_client:
            try:
                logger.info("回退到zhizengzeng客户端")
                return self.zhizengzeng_client.chat_completion(messages, **kwargs)
            except Exception as e:
                logger.warning(f"zhizengzeng客户端调用失败: {e}")
        
        # 回退到DeepSeek
        if self.deepseek_v3_client:
            try:
                logger.info("回退到DeepSeek客户端")
                response = self.deepseek_v3_client.chat.completions.create(
                    model="ep-20250331105849-cbfg5",
                    messages=messages,
                    temperature=kwargs.get('temperature', 0.1)
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"DeepSeek客户端调用失败: {e}")
        
        # 回退到OpenAI
        if self.openai_client:
            try:
                logger.info("回退到OpenAI客户端")
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=kwargs.get('temperature', 0.1)
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenAI客户端调用失败: {e}")
        
        raise Exception("所有API客户端都不可用")
    
    def chat_with_function_calling(self, system_prompt: str, user_input: str, tools: List[Dict[str, Any]], **kwargs) -> str:
        """带function calling的聊天完成"""
        messages = [
            {"role": "user", "content": user_input}
        ]
        
        # 优先使用vivo的function calling
        if self.vivo_client:
            try:
                logger.info("尝试使用vivo客户端的function calling")
                return self.vivo_client.chat_completion_with_function_calling(messages, tools, **kwargs)
            except Exception as e:
                logger.warning(f"vivo function calling调用失败: {e}")
        
        # 回退到OpenAI的function calling
        if self.openai_client:
            try:
                logger.info("回退到OpenAI的function calling")
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    tools=tools,
                    temperature=kwargs.get('temperature', 0.1)
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenAI function calling调用失败: {e}")
        
        # 如果都不可用，使用普通聊天
        logger.info("回退到普通聊天模式")
        return self.chat_with_fallback(system_prompt, user_input, **kwargs)
    
    async def chat_with_fallback_async(self, system_prompt: str, user_input: str, **kwargs) -> str:
        """异步使用回退策略的聊天完成"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # 优先使用vivo
        if self.vivo_client:
            try:
                logger.info("尝试使用vivo客户端（异步）")
                return await self.vivo_client.chat_completion_async(messages, **kwargs)
            except Exception as e:
                logger.warning(f"vivo客户端异步调用失败: {e}")
        
        # 回退到zhizengzeng
        if self.zhizengzeng_client:
            try:
                logger.info("回退到zhizengzeng客户端（异步）")
                return await self.zhizengzeng_client.chat_completion_async(messages, **kwargs)
            except Exception as e:
                logger.warning(f"zhizengzeng客户端异步调用失败: {e}")
        
        # 回退到DeepSeek
        if self.deepseek_v3_client:
            try:
                logger.info("回退到DeepSeek客户端（异步）")
                async_client = AsyncOpenAI(
                    api_key="a306bf91-ca05-442f-b09d-8ebaca556f0a",
                    base_url="https://ark.cn-beijing.volces.com/api/v3"
                )
                response = await async_client.chat.completions.create(
                    model="ep-20250331105849-cbfg5",
                    messages=messages,
                    temperature=kwargs.get('temperature', 0.1)
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"DeepSeek客户端异步调用失败: {e}")
        
        # 回退到OpenAI
        if self.openai_client:
            try:
                logger.info("回退到OpenAI客户端（异步）")
                async_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                response = await async_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=kwargs.get('temperature', 0.1)
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenAI客户端异步调用失败: {e}")
        
        raise Exception("所有API客户端都不可用")
    
    def chat_with_vivo(self, system_prompt: str, user_input: str, **kwargs) -> str:
        """直接使用vivo客户端"""
        if not self.vivo_client:
            raise Exception("vivo客户端未初始化")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        return self.vivo_client.chat_completion(messages, **kwargs)
    
    async def chat_with_vivo_async(self, system_prompt: str, user_input: str, **kwargs) -> str:
        """异步直接使用vivo客户端"""
        if not self.vivo_client:
            raise Exception("vivo客户端未初始化")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        return await self.vivo_client.chat_completion_async(messages, **kwargs)
    
    def get_best_available_client(self) -> str:
        """获取最佳可用客户端"""
        if self.vivo_client:
            return "vivo"
        elif self.zhizengzeng_client:
            return "zhizengzeng"
        elif self.deepseek_v3_client:
            return "deepseek"
        elif self.openai_client:
            return "openai"
        else:
            return "none"


# 全局实例
api_client = UnifiedAPIClient()


# 兼容性函数
def chat_with_vivo(system_prompt: str, user_input: str, **kwargs) -> str:
    """兼容性函数：使用vivo客户端聊天"""
    return api_client.chat_with_vivo(system_prompt, user_input, **kwargs)


def chat_with_fallback(system_prompt: str, user_input: str, **kwargs) -> str:
    """使用回退策略的聊天完成"""
    return api_client.chat_with_fallback(system_prompt, user_input, **kwargs)


async def chat_with_vivo_async(system_prompt: str, user_input: str, **kwargs) -> str:
    """兼容性函数：异步使用vivo客户端聊天"""
    return await api_client.chat_with_vivo_async(system_prompt, user_input, **kwargs)


async def chat_with_fallback_async(system_prompt: str, user_input: str, **kwargs) -> str:
    """异步使用回退策略的聊天完成"""
    return await api_client.chat_with_fallback_async(system_prompt, user_input, **kwargs)


def get_best_available_client() -> str:
    """获取最佳可用客户端"""
    return api_client.get_best_available_client() 