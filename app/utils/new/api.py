# -*- coding: utf-8 -*-
"""
API模块 - 统一管理所有大模型API和语音API的调用

本模块提供了对各种API的统一接口，支持:
- Azure OpenAI API (GPT-4o)
- 智增增 API (GPT-4o)
- 火山引擎 API (DeepSeek)
- 讯飞语音转写API (这部分逻辑将移至 preprocess.py)

每个API都有同步和异步版本，并提供错误处理、重试机制和日志记录。
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

# OpenAI和AsyncOpenAI库
from openai import OpenAI, AsyncOpenAI, AzureOpenAI, AsyncAzureOpenAI
import tiktoken

# 配置日志
logger = logging.getLogger(__name__)

# 默认API密钥和配置（生产环境应从环境变量或安全存储获取）
AZURE_CONFIG = {
    "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
    "azure_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT", "https://pcg-west-us-3.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"),
    "api_version": os.environ.get("AZURE_API_VERSION", "2025-01-01")
}

DEEPSEEK_CONFIG = {
    "api_key": os.environ.get("DEEPSEEK_API_KEY"),
    "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
}

ZHIZENGZENG_CONFIG = {
            "api_key": os.environ.get("ZHIZENGZENG_API_KEY"),
    "base_url": os.environ.get("ZHIZENGZENG_BASE_URL", "https://api.zhizengzeng.com/v1")
}

XFYUN_CONFIG = {
    "app_id": os.environ.get("XFYUN_APP_ID", ""),
    "api_secret": os.environ.get("XFYUN_API_SECRET", ""),
    "api_key": os.environ.get("XFYUN_API_KEY", "")
}

# 默认模型映射
DEFAULT_MODELS = {
    "azure": "gpt-4o",
    "zhizengzeng": "gpt-4o", 
    "deepseek": "ep-20250331105849-cbfg5",  # DeepSeek-Chat V3
    "deepseek-r1": "ep-20250213154525-wkfdb"  # DeepSeek-Chat R1
}

# 为每种客户端类型提供重试设置
RETRY_SETTINGS = {
    "azure": {"max_retries": 3, "base_delay": 2, "max_delay": 10},
    "zhizengzeng": {"max_retries": 3, "base_delay": 2, "max_delay": 10},
    "deepseek": {"max_retries": 5, "base_delay": 3, "max_delay": 15},
    "deepseek-r1": {"max_retries": 5, "base_delay": 3, "max_delay": 15},
    "xfyun": {"max_retries": 3, "base_delay": 2, "max_delay": 10} # 保留讯飞的重试设置，供preprocess使用
}

def get_llm_client(client_type: str, timeout: int = 30, **kwargs) -> OpenAI:
    """
    获取同步LLM客户端
    
    Args:
        client_type: 客户端类型 ('azure'/'zhizengzeng'/'deepseek'/'deepseek-r1')
        timeout: 请求超时时间（秒）
        **kwargs: 传递给客户端构造函数的额外参数
        
    Returns:
        初始化的OpenAI客户端
    """
    try:
        if client_type == 'azure':
            client = AzureOpenAI(
                api_key=kwargs.get('api_key', AZURE_CONFIG['api_key']),
                azure_endpoint=kwargs.get('azure_endpoint', AZURE_CONFIG['azure_endpoint']),
                api_version=kwargs.get('api_version', AZURE_CONFIG['api_version']),
                timeout=timeout
            )
        elif client_type == 'zhizengzeng':
            client = OpenAI(
                api_key=kwargs.get('api_key', ZHIZENGZENG_CONFIG['api_key']),
                base_url=kwargs.get('base_url', ZHIZENGZENG_CONFIG['base_url']),
                timeout=timeout
            )
        elif client_type == 'deepseek' or client_type == 'deepseek-r1':
            client = OpenAI(
                api_key=kwargs.get('api_key', DEEPSEEK_CONFIG['api_key']),
                base_url=kwargs.get('base_url', DEEPSEEK_CONFIG['base_url']),
                timeout=timeout
            )
        else:
            raise ValueError(f"不支持的客户端类型: {client_type}")
        
        logger.info(f"成功初始化 {client_type} 同步客户端")
        return client
    except Exception as e:
        logger.error(f"创建 {client_type} 客户端失败: {e}")
        raise

async def get_llm_async_client(client_type: str, timeout: int = 30, **kwargs) -> AsyncOpenAI:
    """
    获取异步LLM客户端
    
    Args:
        client_type: 客户端类型 ('azure'/'zhizengzeng'/'deepseek'/'deepseek-r1')
        timeout: 请求超时时间（秒）
        **kwargs: 传递给客户端构造函数的额外参数
        
    Returns:
        初始化的AsyncOpenAI客户端
    """
    try:
        if client_type == 'azure':
            client = AsyncAzureOpenAI(
                api_key=kwargs.get('api_key', AZURE_CONFIG['api_key']),
                azure_endpoint=kwargs.get('azure_endpoint', AZURE_CONFIG['azure_endpoint']),
                api_version=kwargs.get('api_version', AZURE_CONFIG['api_version']),
                timeout=timeout
            )
        elif client_type == 'zhizengzeng':
            client = AsyncOpenAI(
                api_key=kwargs.get('api_key', ZHIZENGZENG_CONFIG['api_key']),
                base_url=kwargs.get('base_url', ZHIZENGZENG_CONFIG['base_url']),
                timeout=timeout
            )
        elif client_type == 'deepseek' or client_type == 'deepseek-r1':
            client = AsyncOpenAI(
                api_key=kwargs.get('api_key', DEEPSEEK_CONFIG['api_key']),
                base_url=kwargs.get('base_url', DEEPSEEK_CONFIG['base_url']),
                timeout=timeout
            )
        else:
            raise ValueError(f"不支持的客户端类型: {client_type}")
        
        logger.info(f"成功初始化 {client_type} 异步客户端")
        return client
    except Exception as e:
        logger.error(f"创建 {client_type} 异步客户端失败: {e}")
        raise

def call_llm(
    client_type: str,
    model: Optional[str] = None,
    messages: List[Dict[str, str]] = None,
    temperature: float = 0.1,
    timeout: int = 60,
    **kwargs
) -> str:
    """
    同步调用LLM API
    
    Args:
        client_type: 客户端类型 ('azure'/'zhizengzeng'/'deepseek'/'deepseek-r1')
        model: 模型名称，如果未提供则使用默认映射
        messages: 消息列表
        temperature: 温度参数 (0-1)
        timeout: 请求超时（秒）
        **kwargs: 传递给API调用的额外参数
        
    Returns:
        模型响应文本
    """
    retry_settings = RETRY_SETTINGS.get(client_type, {"max_retries": 3, "base_delay": 2, "max_delay": 10})
    max_retries = retry_settings["max_retries"]
    base_delay = retry_settings["base_delay"]
    max_delay = retry_settings["max_delay"]
    
    # 如果未提供模型，使用默认映射
    if not model:
        model = DEFAULT_MODELS.get(client_type, DEFAULT_MODELS["azure"])
    
    # 如果未提供消息，使用空列表（但这通常不应该发生）
    if not messages:
        messages = [{"role": "user", "content": "Hello"}]
    
    attempts = 0
    last_error = None
    
    # 记录请求信息（仅记录第一条消息内容的前100个字符，避免过长日志）
    first_msg_preview = messages[0]["content"][:100] + "..." if len(messages[0]["content"]) > 100 else messages[0]["content"]
    logger.info(f"开始 {client_type} 模型 {model} 调用，消息起始内容: {first_msg_preview}")
    
    while attempts < max_retries:
        try:
            start_time = time.time()
            client = get_llm_client(client_type, timeout=timeout)
            
            chat_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }
            
            # Azure API需要不同的参数命名
            if client_type == "azure":
                # Azure可能需要调整参数名称 (如果API需要)
                pass
            
            # 执行API调用
            response = client.chat.completions.create(**chat_params)
            
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"{client_type} 模型 {model} 调用成功，用时: {duration:.2f}秒")
            
            # 返回文本内容
            return response.choices[0].message.content
            
        except Exception as e:
            attempts += 1
            last_error = e
            delay = min(base_delay * (2 ** (attempts - 1)), max_delay)
            
            logger.warning(f"{client_type} 调用失败，尝试 {attempts}/{max_retries}，将在 {delay}秒后重试: {e}")
            time.sleep(delay)
    
    logger.error(f"{client_type} 模型 {model} 调用失败，已达到最大重试次数: {last_error}")
    raise last_error or RuntimeError(f"{client_type} API调用失败")

async def call_llm_async(
    client_type: str,
    model: Optional[str] = None,
    messages: List[Dict[str, str]] = None,
    temperature: float = 0.1,
    timeout: int = 60,
    **kwargs
) -> str:
    """
    异步调用LLM API
    
    Args:
        client_type: 客户端类型 ('azure'/'zhizengzeng'/'deepseek'/'deepseek-r1')
        model: 模型名称，如果未提供则使用默认映射
        messages: 消息列表
        temperature: 温度参数 (0-1)
        timeout: 请求超时（秒）
        **kwargs: 传递给API调用的额外参数
        
    Returns:
        模型响应文本
    """
    retry_settings = RETRY_SETTINGS.get(client_type, {"max_retries": 3, "base_delay": 2, "max_delay": 10})
    max_retries = retry_settings["max_retries"]
    base_delay = retry_settings["base_delay"]
    max_delay = retry_settings["max_delay"]
    
    # 如果未提供模型，使用默认映射
    if not model:
        model = DEFAULT_MODELS.get(client_type, DEFAULT_MODELS["azure"])
    
    # 如果未提供消息，使用空列表
    if not messages:
        messages = [{"role": "user", "content": "Hello"}]
    
    attempts = 0
    last_error = None
    
    # 记录请求信息（仅记录第一条消息内容的前100个字符，避免过长日志）
    first_msg_preview = messages[0]["content"][:100] + "..." if len(messages[0]["content"]) > 100 else messages[0]["content"]
    logger.info(f"开始异步 {client_type} 模型 {model} 调用，消息起始内容: {first_msg_preview}")
    
    # 尝试使用备用客户端，如果指定
    backup_client_types = kwargs.pop("backup_client_types", [])
    
    while attempts < max_retries:
        try:
            start_time = time.time()
            client = await get_llm_async_client(client_type, timeout=timeout)
            
            chat_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }
            
            # Azure API可能需要不同的参数命名
            if client_type == "azure":
                # Azure可能需要调整参数名称 (如果API需要)
                pass
            
            # 执行API调用
            response = await client.chat.completions.create(**chat_params)
            
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"异步 {client_type} 模型 {model} 调用成功，用时: {duration:.2f}秒")
            
            # 返回文本内容
            return response.choices[0].message.content
            
        except Exception as e:
            attempts += 1
            last_error = e
            delay = min(base_delay * (2 ** (attempts - 1)), max_delay)
            
            logger.warning(f"异步 {client_type} 调用失败，尝试 {attempts}/{max_retries}，将在 {delay}秒后重试: {e}")
            
            # 如果当前客户端已达到最大重试次数，但还有备用客户端，则尝试备用客户端
            if attempts >= max_retries and backup_client_types:
                backup_type = backup_client_types.pop(0)
                logger.info(f"尝试使用备用客户端 {backup_type}")
                # 使用备用客户端递归调用，但不传递backup_client_types参数以避免无限循环
                kwargs_copy = kwargs.copy()
                try:
                    return await call_llm_async(
                        client_type=backup_type,
                        model=DEFAULT_MODELS.get(backup_type, model),
                        messages=messages,
                        temperature=temperature,
                        timeout=timeout,
                        **kwargs_copy
                    )
                except Exception as be:
                    logger.warning(f"备用客户端 {backup_type} 调用也失败: {be}")
                    # 继续尝试下一个备用客户端或回到原客户端重试
            
            await asyncio.sleep(delay)
    
    logger.error(f"异步 {client_type} 模型 {model} 调用失败，已达到最大重试次数: {last_error}")
    raise last_error or RuntimeError(f"{client_type} API异步调用失败")

def num_tokens_from_messages(messages, model="gpt-4o"):
    """
    计算消息的token数量
    
    Args:
        messages: 消息列表
        model: 使用的模型
        
    Returns:
        消息的token数量
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")  # 如果模型不在tiktoken的内置模型中，使用通用编码
    
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # 每条消息基础token
        for key, value in message.items():
            if key != "role" and key != "content":
                continue
            num_tokens += len(encoding.encode(value))
            if key == "role":
                num_tokens += 1  # role的基础token
    
    num_tokens += 2  # 对话结束token
    return num_tokens

# --- 讯飞语音转写相关代码 (已移除) ---
# 以下函数已移至 preprocess.py
# def get_current_time(): ...
# def generate_signature(...): ...
# def transcribe_audio(...): ...
# async def transcribe_audio_async(...): ...

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试同步LLM调用
    try:
        response = call_llm(
            client_type="zhizengzeng",
            messages=[{"role": "user", "content": "你好，请用一句话介绍自己。"}]
        )
        print(f"同步调用结果: {response}")
    except Exception as e:
        print(f"同步调用测试失败: {e}")
    
    # 测试异步LLM调用
    async def test_async():
        try:
            response = await call_llm_async(
                client_type="deepseek",
                messages=[{"role": "user", "content": "你好，请用一句话介绍自己。"}]
            )
            print(f"异步调用结果: {response}")
        except Exception as e:
            print(f"异步调用测试失败: {e}")
    
    # 运行异步测试
    asyncio.run(test_async()) 