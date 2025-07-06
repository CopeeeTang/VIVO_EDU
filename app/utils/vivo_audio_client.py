# -*- coding: utf-8 -*-
import os
import time
import uuid
import hmac
import hashlib
import json
import math
import requests
import base64
import urllib.parse
from typing import Optional, Dict, Any, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VivoAudioAuth:
    """vivo语音转录API鉴权工具类"""
    
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


class VivoAudioClient:
    """vivo语音转录API客户端"""
    
    def __init__(self, app_id: str, app_key: str, base_url: str = 'https://api-ai.vivo.com.cn'):
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = base_url
        self.slice_size = 5 * 1024 * 1024  # 5MB per slice
        
        # 必需的URL参数
        self.url_params = {
            'client_version': 'v1.0.0',
            'package': 'vivo_edu_app',
            'user_id': str(uuid.uuid4()).replace('-', ''),
            'system_time': str(int(time.time() * 1000)),
            'engineid': 'fileasrrecorder'
        }
    
    def _get_headers_and_params(self, uri: str, additional_params: dict = None) -> tuple:
        """生成请求头和参数"""
        params = self.url_params.copy()
        if additional_params:
            params.update(additional_params)
        
        headers = VivoAudioAuth.gen_sign_headers(
            self.app_id, self.app_key, 'POST', uri, params
        )
        
        return headers, params
    
    def create_audio(self, file_path: str, audio_type: str = 'auto') -> tuple:
        """创建音频任务"""
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 计算分片数量
        slice_num = math.ceil(file_size / self.slice_size)
        
        # 生成session ID
        session_id = str(uuid.uuid4())
        
        # 准备请求数据
        data = {
            'audio_type': audio_type,
            'x-sessionId': session_id,
            'slice_num': slice_num
        }
        
        # 生成请求头和参数
        headers, params = self._get_headers_and_params('/lasr/create')
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        
        try:
            url = f"{self.base_url}/lasr/create"
            response = requests.post(
                url,
                json=data,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info(f"音频创建成功: {result}")
                    audio_id = result.get('data', {}).get('audio_id')
                    if not audio_id:
                        raise Exception("创建音频任务成功但未返回audio_id")
                    return session_id, audio_id, file_size
                else:
                    raise Exception(f"创建音频失败: {result.get('desc', 'Unknown error')}")
            else:
                raise Exception(f"创建音频请求失败: {response.status_code}, {response.text}")
                
        except Exception as e:
            logger.error(f"创建音频任务失败: {e}")
            raise
    
    def upload_audio_slice(self, session_id: str, audio_id: str, slice_data: bytes, slice_index: int) -> bool:
        """上传音频分片"""
        # 准备URL参数，包含必需的audio_id, x-sessionId, slice_index
        upload_params = {
            'audio_id': audio_id,
            'x-sessionId': session_id,
            'slice_index': slice_index
        }
        
        # 生成请求头和参数
        headers, params = self._get_headers_and_params('/lasr/upload', upload_params)
        
        try:
            url = f"{self.base_url}/lasr/upload"
            
            # 准备文件数据
            files = {
                'slice_data': ('audio_slice', slice_data, 'application/octet-stream')
            }
            
            response = requests.post(
                url,
                files=files,
                headers=headers,
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info(f"分片 {slice_index} 上传成功")
                    return True
                else:
                    raise Exception(f"上传分片失败: {result.get('desc', 'Unknown error')}")
            else:
                raise Exception(f"上传分片请求失败: {response.status_code}, {response.text}")
                
        except Exception as e:
            logger.error(f"上传分片失败: {e}")
            raise
    
    def start_transcription(self, session_id: str, audio_id: str) -> str:
        """开始转写任务"""
        # 准备请求数据 - 根据audio.mdc文档，只需要audio_id和x-sessionId
        data = {
            'audio_id': audio_id,
            'x-sessionId': session_id
        }
        
        # 生成请求头和参数 - 使用正确的API路径/lasr/run
        headers, params = self._get_headers_and_params('/lasr/run')
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        
        try:
            url = f"{self.base_url}/lasr/run"
            response = requests.post(
                url,
                json=data,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    task_id = result.get('data', {}).get('task_id')
                    logger.info(f"转写任务启动成功: {task_id}")
                    return task_id
                else:
                    raise Exception(f"启动转写任务失败: {result.get('desc', 'Unknown error')}")
            else:
                raise Exception(f"启动转写任务请求失败: {response.status_code}, {response.text}")
                
        except Exception as e:
            logger.error(f"启动转写任务失败: {e}")
            raise
    
    def query_progress(self, task_id: str, session_id: str) -> dict:
        """查询转写进度"""
        # 准备请求数据
        data = {
            'task_id': task_id,
            'x-sessionId': session_id
        }
        
        # 生成请求头和参数
        headers, params = self._get_headers_and_params('/lasr/progress')
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        
        try:
            url = f"{self.base_url}/lasr/progress"
            response = requests.post(
                url,
                json=data,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    return result.get('data', {})
                else:
                    raise Exception(f"查询进度失败: {result.get('desc', 'Unknown error')}")
            else:
                raise Exception(f"查询进度请求失败: {response.status_code}, {response.text}")
                
        except Exception as e:
            logger.error(f"查询转写进度失败: {e}")
            raise
    
    def get_result(self, task_id: str, session_id: str) -> dict:
        """获取转写结果"""
        # 准备请求数据
        data = {
            'task_id': task_id,
            'x-sessionId': session_id
        }
        
        # 生成请求头和参数
        headers, params = self._get_headers_and_params('/lasr/result')
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        
        try:
            url = f"{self.base_url}/lasr/result"
            response = requests.post(
                url,
                json=data,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    data_result = result.get('data', {})
                    # 添加详细的调试日志
                    logger.info(f"vivo API原始返回数据: {json.dumps(data_result, ensure_ascii=False, indent=2)}")
                    return data_result
                else:
                    raise Exception(f"获取结果失败: {result.get('desc', 'Unknown error')}")
            else:
                raise Exception(f"获取结果请求失败: {response.status_code}, {response.text}")
                
        except Exception as e:
            logger.error(f"获取转写结果失败: {e}")
            raise
    
    def transcribe_file(self, file_path: str, audio_type: str = 'auto') -> dict:
        """完整的转写流程"""
        logger.info(f"开始转写音频文件: {file_path}")
        
        try:
            # 1. 创建音频任务
            session_id, audio_id, file_size = self.create_audio(file_path, audio_type)
            
            # 2. 分片上传音频
            with open(file_path, 'rb') as f:
                slice_index = 0
                while True:
                    slice_data = f.read(self.slice_size)
                    if not slice_data:
                        break
                    
                    self.upload_audio_slice(session_id, audio_id, slice_data, slice_index)
                    slice_index += 1
            
            # 3. 开始转写
            task_id = self.start_transcription(session_id, audio_id)
            
            # 4. 轮询查询进度
            while True:
                progress_data = self.query_progress(task_id, session_id)
                progress = progress_data.get('progress', 0)
                
                if progress == 100:
                    logger.info("转写任务完成")
                    break
                else:
                    logger.info(f"转写进度: {progress}%")
                    time.sleep(5)  # 等待5秒后再次查询
            
            # 5. 获取结果
            result = self.get_result(task_id, session_id)
            logger.info("转写完成")
            return result
            
        except Exception as e:
            logger.error(f"转写过程中发生错误: {e}")
            raise


def create_vivo_audio_client() -> VivoAudioClient:
    """创建vivo语音转录客户端"""
    # 获取环境变量
    app_id = os.environ.get('VIVO_AUDIO_APP_ID')
    app_key = os.environ.get('VIVO_AUDIO_APP_KEY')
    
    if not app_id or not app_key:
        raise ValueError("VIVO_AUDIO_APP_ID and VIVO_AUDIO_APP_KEY environment variables are required")
    
    return VivoAudioClient(app_id, app_key) 