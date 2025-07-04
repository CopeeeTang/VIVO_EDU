# -*- coding: utf-8 -*-
"""
预处理模块 - 音频转写与文本标准化

本模块处理音频文件的转写和标准化，包括：
- 音频转写（调用讯飞API）
- 提取日期信息
- 转写文本标准化
"""

import os
import re
import json
import logging
import datetime
import asyncio
import time
import requests
import hmac
import hashlib
import base64
from typing import List, Dict, Any, Optional, Union

# 导入API模块的配置和重试设置
from .api import XFYUN_CONFIG, RETRY_SETTINGS

# 配置日志
logger = logging.getLogger(__name__)

# 日期提取正则表达式（支持多种格式）
DATE_PATTERNS = [
    r'(\d{4})[-_/]?(\d{1,2})[-_/]?(\d{1,2})',  # 2023-01-01, 2023_01_01, 20230101
    r'(\d{1,2})[-_/]?(\d{1,2})[-_/]?(\d{4})',  # 01-01-2023, 01_01_2023
    r'(\d{2})(\d{2})(\d{2})',                   # 230101 (简化年份)
]

def extract_date_from_filename(filename: str) -> Optional[str]:
    """
    从文件名中提取日期信息，返回标准化的YYYYMMDD格式
    
    Args:
        filename: 文件名
        
    Returns:
        标准化的日期字符串 (YYYYMMDD) 或 None
    """
    try:
        # 移除扩展名
        base_filename = os.path.splitext(os.path.basename(filename))[0]
        
        # 尝试各种日期格式
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, base_filename)
            if match:
                groups = match.groups()
                
                # 处理不同的日期格式
                if len(groups[0]) == 4:  # YYYY-MM-DD
                    year, month, day = groups
                elif len(groups[2]) == 4:  # DD-MM-YYYY
                    day, month, year = groups
                elif len(groups[0]) == 2:  # YY-MM-DD
                    year, month, day = groups
                    # 对于两位数年份，如果小于当前年份的后两位，则认为是21世纪，否则是20世纪
                    current_year = datetime.datetime.now().year
                    current_yy = current_year % 100
                    century = 2000 if int(year) <= current_yy else 1900
                    year = str(century + int(year))
                else:
                    continue
                
                # 确保月和日是两位数
                month = month.zfill(2)
                day = day.zfill(2)
                
                # 验证日期是否有效
                try:
                    datetime.datetime(int(year), int(month), int(day))
                    return f"{year}{month}{day}"
                except ValueError:
                    continue
        
        # 如果未找到有效日期，返回当前日期
        logger.warning(f"无法从文件名 '{filename}' 提取日期，使用当前日期")
        return datetime.datetime.now().strftime('%Y%m%d')
        
    except Exception as e:
        logger.error(f"日期提取失败: {e}")
        return None

def normalize_transcript(raw_transcript: Union[List, Dict]) -> List[Dict]:
    """
    标准化转写格式，统一为 [{id, speaker, text, start_time, end_time}] 结构
    
    Args:
        raw_transcript: 原始转写数据（可能是多种格式）
        
    Returns:
        标准化的转写列表
    """
    try:
        # 如果输入是字典，尝试找到转写数据的主要字段
        if isinstance(raw_transcript, dict):
            # 寻找可能包含转写列表的字段
            if 'data' in raw_transcript and isinstance(raw_transcript['data'], list):
                raw_transcript = raw_transcript['data']
            elif 'results' in raw_transcript and isinstance(raw_transcript['results'], list):
                raw_transcript = raw_transcript['results']
            elif 'segments' in raw_transcript and isinstance(raw_transcript['segments'], list):
                raw_transcript = raw_transcript['segments']
            else:
                # 如果找不到列表，可能整个字典就是一个片段
                raw_transcript = [raw_transcript]
        
        # 确保此时raw_transcript是列表
        if not isinstance(raw_transcript, list):
            raise ValueError(f"无法处理的转写格式: {type(raw_transcript)}")
        
        normalized = []
        for i, segment in enumerate(raw_transcript):
            # 根据不同的API输出格式提取字段
            if isinstance(segment, dict):
                # 提取ID
                segment_id = segment.get('id', segment.get('segment_id', i + 1))
                
                # 提取说话者信息
                speaker = segment.get('speaker', 'unknown')
                # 一些API可能用不同的字段名表示说话者
                if 'speaker' not in segment:
                    if 'speaker_id' in segment:
                        speaker = f"speaker_{segment['speaker_id']}"
                    elif 'channel' in segment:
                        speaker = f"channel_{segment['channel']}"
                
                # 尝试识别家长和孩子
                if isinstance(speaker, str) and speaker.lower() in ['parent', 'father', 'mother', 'dad', 'mom']:
                    speaker = '家长'
                elif isinstance(speaker, str) and speaker.lower() in ['child', 'kid', 'son', 'daughter']:
                    speaker = '孩子'
                
                # 提取文本内容
                text = segment.get('text', segment.get('content', segment.get('onebest', '')))
                
                # 提取时间戳（如果有）
                start_time = segment.get('start_time', segment.get('start', segment.get('bg', 0)))
                if isinstance(start_time, str):
                    try:
                        start_time = float(start_time.replace('s', ''))
                    except ValueError:
                        start_time = 0
                
                end_time = segment.get('end_time', segment.get('end', segment.get('ed', 0)))
                if isinstance(end_time, str):
                    try:
                        end_time = float(end_time.replace('s', ''))
                    except ValueError:
                        end_time = 0
                
                # 添加标准化的片段
                normalized.append({
                    'id': segment_id,
                    'speaker': speaker,
                    'text': text,
                    'start_time': start_time,
                    'end_time': end_time
                })
            elif isinstance(segment, str):
                # 如果是纯文本数组，简单分配ID和文本
                normalized.append({
                    'id': i + 1,
                    'speaker': 'unknown',
                    'text': segment,
                    'start_time': 0,
                    'end_time': 0
                })
        
        # 确保ID是连续的整数
        for i, segment in enumerate(normalized):
            segment['id'] = i + 1
        
        # 尝试识别说话者（如果尚未标识）
        if all(segment['speaker'] == 'unknown' for segment in normalized):
            _try_identify_speakers(normalized)
        
        return normalized
        
    except Exception as e:
        logger.error(f"转写标准化失败: {e}")
        # 返回一个最小的有效结构，避免下游处理错误
        return [{'id': 1, 'speaker': 'unknown', 'text': '转写处理失败', 'start_time': 0, 'end_time': 0}]

def _try_identify_speakers(transcript: List[Dict]) -> None:
    """
    尝试识别对话中的说话者角色（家长/孩子）
    这是一个启发式方法，假设对话是交替的，且从家长开始
    
    Args:
        transcript: 转写列表，将直接修改这个列表
    """
    if not transcript:
        return
    
    # 假设从家长开始，然后交替
    for i, segment in enumerate(transcript):
        if segment['speaker'] == 'unknown':
            segment['speaker'] = '家长' if i % 2 == 0 else '孩子'

def save_transcript(transcript: List[Dict], output_path: str) -> bool:
    """
    保存标准化的转写到文件
    
    Args:
        transcript: 标准化的转写列表
        output_path: 输出文件路径
        
    Returns:
        是否保存成功
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
        logger.info(f"转写保存成功: {output_path}")
        return True
    except Exception as e:
        logger.error(f"转写保存失败: {e}")
        return False

def _transcribe_xfyun(audio_path: str, config=None, **kwargs) -> List[Dict]:
    """
    使用讯飞API进行音频转写 (同步实现)
    
    Args:
        audio_path: 音频文件路径
        config: 讯飞API配置
        **kwargs: 额外参数
    
    Returns:
        转写结果列表，失败时抛出异常
    """
    if not config:
        config = XFYUN_CONFIG
    
    app_id = config.get('app_id')
    api_secret = config.get('api_secret')
    api_key = config.get('api_key')
    
    if not (app_id and api_secret and api_key):
        raise ValueError("讯飞API配置不完整，请提供app_id, api_secret和api_key")
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"找不到音频文件: {audio_path}")
    
    retry_settings = RETRY_SETTINGS.get("xfyun", {"max_retries": 3, "base_delay": 2, "max_delay": 10})
    max_retries = retry_settings["max_retries"]
    base_delay = retry_settings["base_delay"]
    max_delay = retry_settings["max_delay"]
    
    # API参数
    lfasr_type = '0'  # 表示长语音（大于60秒）
    has_participle = 'false'  # 不进行分词处理
    engine_type = kwargs.get('engine_type', 'aisound')  # 默认使用aisound引擎
    
    # API URL
    api_prepare = "https://raasr.xfyun.cn/v2/api/prepare"
    api_upload = "https://raasr.xfyun.cn/v2/api/upload"
    api_merge = "https://raasr.xfyun.cn/v2/api/merge"
    api_query = "https://raasr.xfyun.cn/v2/api/getResult"
    
    # 预处理
    data = {
        "app_id": app_id,
        "signa": "",
        "ts": int(time.time()),
        "file_len": os.path.getsize(audio_path),
        "file_name": os.path.basename(audio_path),
        "lfasr_type": lfasr_type,
        "has_participle": has_participle,
        "eng_type": engine_type
    }
    
    attempts = 0
    last_error = None
    
    while attempts < max_retries:
        try:
            # 步骤1: 预处理
            logger.info(f"开始讯飞语音转写 (同步): {audio_path}")
            prepare_response = requests.post(api_prepare, data=data).json()
            
            if prepare_response["ok"] != 0:
                raise Exception(f"讯飞预处理失败: {prepare_response['failed']}")
            
            task_id = prepare_response["data"]
            logger.info(f"讯飞转写任务ID: {task_id}")
            
            # 步骤2: 上传音频文件
            with open(audio_path, 'rb') as f:
                file_content = f.read()
            
            slice_num = 0
            for i in range(0, len(file_content), 10485760):  # 10MB分片
                upload_data = {
                    "app_id": app_id,
                    "signa": "",
                    "ts": int(time.time()),
                    "task_id": task_id,
                    "slice_id": slice_num
                }
                files = {
                    "content": (os.path.basename(audio_path), file_content[i:i+10485760])
                }
                upload_response = requests.post(api_upload, data=upload_data, files=files).json()
                
                if upload_response["ok"] != 0:
                    raise Exception(f"讯飞上传片段 {slice_num} 失败: {upload_response['failed']}")
                
                slice_num += 1
                logger.info(f"已上传片段 {slice_num}")
            
            # 步骤3: 合并请求
            merge_data = {
                "app_id": app_id,
                "signa": "",
                "ts": int(time.time()),
                "task_id": task_id
            }
            merge_response = requests.post(api_merge, data=merge_data).json()
            
            if merge_response["ok"] != 0:
                raise Exception(f"讯飞合并请求失败: {merge_response['failed']}")
            
            logger.info("音频合并成功，开始等待转写结果")
            
            # 步骤4: 轮询获取结果
            query_data = {
                "app_id": app_id,
                "signa": "",
                "ts": int(time.time()),
                "task_id": task_id
            }
            
            wait_time = 3  # 初始等待时间
            max_wait_time = 300  # 最大等待时间（5分钟）
            start_time = time.time()
            
            while True:
                # 检查是否超过最大等待时间
                current_time = time.time()
                if current_time - start_time > max_wait_time:
                    raise TimeoutError(f"讯飞转写超时，已等待 {max_wait_time} 秒")
                
                # 轮询结果
                query_response = requests.post(api_query, data=query_data).json()
                
                if query_response["ok"] != 0:
                    raise Exception(f"讯飞查询结果失败: {query_response['failed']}")
                
                if query_response["data"]["status"] == 9:  # 转写完成
                    logger.info("讯飞转写完成")
                    result = json.loads(query_response["data"]["result"])
                    return result # 返回原始的讯飞结果列表
                    
                elif query_response["data"]["status"] == 3:  # 转写失败
                    raise Exception(f"讯飞转写失败: {query_response['data']['error']}")
                
                # 等待一段时间后再次查询
                logger.info(f"转写进行中，状态: {query_response['data']['status']}, 等待 {wait_time} 秒后重新查询")
                time.sleep(wait_time)
                wait_time = min(wait_time * 1.5, 30)  # 递增等待时间，但最多30秒
                
        except Exception as e:
            attempts += 1
            last_error = e
            delay = min(base_delay * (2 ** (attempts - 1)), max_delay)
            
            logger.warning(f"讯飞转写失败，尝试 {attempts}/{max_retries}，将在 {delay}秒后重试: {e}")
            time.sleep(delay)
    
    logger.error(f"讯飞转写失败，已达到最大重试次数: {last_error}")
    raise last_error or RuntimeError("讯飞API调用失败")

async def process_audio(audio_path: str, **kwargs) -> List[Dict]:
    """
    异步处理音频文件，返回标准化的转写结果
    
    Args:
        audio_path: 音频文件路径
        **kwargs: 传递给转写API的额外参数
        
    Returns:
        标准化的转写列表
    """
    try:
        logger.info(f"开始异步处理音频: {audio_path}")
        
        # 检查文件是否存在
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 获取文件大小（MB）
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        logger.info(f"音频文件大小: {file_size_mb:.2f} MB")
        
        # 调用转写API（在线程中执行同步转写）
        raw_transcript = await asyncio.to_thread(_transcribe_xfyun, audio_path, **kwargs)
        logger.info(f"音频转写完成 (异步调用): {len(raw_transcript) if raw_transcript else 0} 个片段")
        
        # 标准化转写格式
        normalized_transcript = normalize_transcript(raw_transcript)
        logger.info(f"转写标准化完成: {len(normalized_transcript)} 个片段")
        
        # 可选: 保存转写结果
        save_path = kwargs.get('save_path')
        if save_path:
            save_transcript(normalized_transcript, save_path)
        
        return normalized_transcript
        
    except Exception as e:
        logger.error(f"异步音频处理失败: {e}")
        # 返回一个最小的有效结构，避免下游处理错误
        return [{'id': 1, 'speaker': 'unknown', 'text': f'音频处理失败: {str(e)}', 'start_time': 0, 'end_time': 0}]

def process_audio_sync(audio_path: str, **kwargs) -> List[Dict]:
    """
    同步处理音频文件，返回标准化的转写结果
    
    Args:
        audio_path: 音频文件路径
        **kwargs: 传递给转写API的额外参数
        
    Returns:
        标准化的转写列表
    """
    try:
        logger.info(f"开始同步处理音频: {audio_path}")
        
        # 检查文件是否存在
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 获取文件大小（MB）
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        logger.info(f"音频文件大小: {file_size_mb:.2f} MB")
        
        # 调用转写API
        raw_transcript = _transcribe_xfyun(audio_path, **kwargs)
        logger.info(f"音频转写完成 (同步调用): {len(raw_transcript) if raw_transcript else 0} 个片段")
        
        # 标准化转写格式
        normalized_transcript = normalize_transcript(raw_transcript)
        logger.info(f"转写标准化完成: {len(normalized_transcript)} 个片段")
        
        # 可选: 保存转写结果
        save_path = kwargs.get('save_path')
        if save_path:
            save_transcript(normalized_transcript, save_path)
        
        return normalized_transcript
        
    except Exception as e:
        logger.error(f"同步音频处理失败: {e}")
        # 返回一个最小的有效结构，避免下游处理错误
        return [{'id': 1, 'speaker': 'unknown', 'text': f'音频处理失败: {str(e)}', 'start_time': 0, 'end_time': 0}]
    
# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试日期提取
    test_filenames = [
        "conversation_20230531.mp3",
        "2023-05-31_recording.wav",
        "audio_05-31-2023.m4a",
        "230531_class.mp3"
    ]
    
    print("测试日期提取:")
    for filename in test_filenames:
        date = extract_date_from_filename(filename)
        print(f"{filename} -> {date}")
    
    # 测试转写格式标准化
    test_xfyun_result = [
        {"speaker": "1", "onebest": "今天我们开始做作业吧。", "bg": 15620, "ed": 25390},
        {"speaker": "2", "onebest": "我不想做，我想先玩一会儿。", "bg": 26150, "ed": 35940}
    ]
    
    print("\n测试转写标准化:")
    normalized = normalize_transcript(test_xfyun_result)
    print(json.dumps(normalized, ensure_ascii=False, indent=2))
    
    # 异步测试音频处理
    async def test_process_audio():
        # 假设有一个测试音频文件
        test_audio = "tests/data/test_audio.mp3"
        if os.path.exists(test_audio):
            # 需要在环境变量或XFYUN_CONFIG中设置讯飞的app_id, api_secret, api_key
            if not (XFYUN_CONFIG.get("app_id") and XFYUN_CONFIG.get("api_secret") and XFYUN_CONFIG.get("api_key")):
                print("\n跳过音频处理测试，讯飞API配置不完整。请设置环境变量或在api.py中配置XFYUN_CONFIG。")
                return
            
            result = await process_audio(test_audio, save_path="tests/output/transcript.json")
            print(f"\n音频处理完成，共 {len(result)} 个片段")
        else:
            print(f"\n测试音频文件不存在: {test_audio}")
    
    # 执行异步测试
    if os.path.exists("tests/data"):
        asyncio.run(test_process_audio())
    else:
        print("\n跳过音频处理测试，测试目录不存在") 