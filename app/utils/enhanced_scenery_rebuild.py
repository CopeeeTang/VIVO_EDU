# -*- coding: utf-8 -*-
"""
优化后的场景重建模块
使用function calling返回结构化数据
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional
from .api_clients import api_client
from .prompt import Scenery_user_prompt, Scenery_system_prompt

logger = logging.getLogger(__name__)


class EnhancedSceneryRebuild:
    """优化后的场景重建器"""
    
    def __init__(self):
        self.api_client = api_client
        self.tools = self._define_tools()
        
    def _define_tools(self) -> List[Dict[str, Any]]:
        """定义function calling工具"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "rebuild_scene",
                    "description": "分析亲子对话以重建家庭教育场景",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "场景数量": {
                                "type": "integer",
                                "description": "在对话中识别出的不同场景数量。除了考虑对话间隔，还应关注主题变化、参与者变动、情感基调转变等因素来判断新场景的开始。"
                            },
                            "场景摘要": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "场景ID": {
                                            "type": "integer",
                                            "description": "场景的唯一标识符"
                                        },
                                        "事件": {
                                            "type": "string",
                                            "description": "详细描述场景中的主要教育事件，包括主题（如作业辅导、行为管教）、参与者、核心互动过程和结果。"
                                        },
                                        "变化": {
                                            "type": "string",
                                            "description": "这个场景中家长行为和孩子行为的动态变化过程。"
                                        },
                                        "关键细节": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            },
                                            "description": "提取能体现场景特点的关键对话片段。包括情感强烈、体现教育方法或反映问题核心的对话。每个片段应标注说话者和情感色彩。"
                                        },
                                        "时间范围": {
                                            "type": "string",
                                            "description": "场景发生的时间段（开始时间-结束时间）"
                                        },
                                        "参与者": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            },
                                            "description": "参与此场景的人员列表"
                                        },
                                        "情感基调": {
                                            "type": "string",
                                            "description": "场景的整体情感氛围（积极、消极、中性）"
                                        }
                                    },
                                    "required": ["场景ID", "事件", "变化", "关键细节"]
                                },
                                "description": "每个识别出场景的详细摘要，结构化呈现以便于后续的知识库检索和相似案例匹配。"
                            }
                        },
                        "required": ["场景数量", "场景摘要"]
                    }
                }
            }
        ]
        return tools
    
    def rebuild_scene(self, transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
        """重建场景"""
        logger.info("开始场景重建")
        
        try:
            # 准备输入数据
            formatted_transcript = self._format_transcript(transcript)
            
            # 构建消息
            messages = [
                {"role": "system", "content": Scenery_system_prompt},
                {"role": "user", "content": f"{Scenery_user_prompt}\n\n对话记录:\n{formatted_transcript}"}
            ]
            
            # 调用API with function calling
            if self.api_client.vivo_client:
                # vivo API暂时不支持function calling，使用结构化文本返回
                result = self._call_vivo_api(messages)
            else:
                # 使用支持function calling的API
                result = self._call_openai_api(messages)
            
            logger.info("场景重建完成")
            return result
            
        except Exception as e:
            logger.error(f"场景重建失败: {e}")
            return {"error": str(e)}
    
    def _format_transcript(self, transcript: List[Dict[str, Any]]) -> str:
        """格式化对话记录"""
        formatted_lines = []
        total_chars = 0
        max_chars = 8000  # 限制总字符数，避免prompt过长
        
        for item in transcript:
            speaker = item.get('speaker', 'unknown')
            content = item.get('content', '')
            timestamp = item.get('start_time', '') or item.get('timestamp', '')
            
            if timestamp:
                line = f"[{timestamp}] {speaker}: {content}"
            else:
                line = f"{speaker}: {content}"
            
            # 检查是否超过长度限制
            if total_chars + len(line) > max_chars:
                formatted_lines.append("... (对话内容过长，已截断)")
                break
            
            formatted_lines.append(line)
            total_chars += len(line) + 1  # +1 for newline
        
        return "\n".join(formatted_lines)
    
    def _call_vivo_api(self, messages: List[Dict]) -> Dict[str, Any]:
        """调用vivo API（不支持function calling）"""
        try:
            # 修改system prompt，要求返回JSON格式
            system_prompt = messages[0]["content"] + "\n\n请以JSON格式返回分析结果，包含场景数量和场景摘要。"
            user_content = messages[1]["content"]
            
            result = self.api_client.chat_with_vivo(system_prompt, user_content)
            
            # 解析JSON结果
            if isinstance(result, str):
                try:
                    # 尝试从文本中提取JSON
                    if "```json" in result:
                        json_str = result.split("```json")[1].split("```")[0].strip()
                        return json.loads(json_str)
                    else:
                        return json.loads(result)
                except Exception as e:
                    logger.warning(f"解析vivo API结果失败: {e}")
                    return {"error": f"解析失败: {result}"}
            
            return result
            
        except Exception as e:
            logger.error(f"调用vivo API失败: {e}")
            return {"error": str(e)}
    
    def _call_openai_api(self, messages: List[Dict]) -> Dict[str, Any]:
        """调用支持function calling的OpenAI API"""
        try:
            # 优先使用deepseek API
            if self.api_client.deepseek_v3_client:
                response = self.api_client.deepseek_v3_client.chat.completions.create(
                    model="ep-20250331105849-cbfg5",
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0.1
                )
                
                # 处理function calling结果
                if response.choices[0].message.tool_calls:
                    tool_call = response.choices[0].message.tool_calls[0]
                    function_args = json.loads(tool_call.function.arguments)
                    return function_args
                else:
                    # 没有function call，解析文本内容
                    content = response.choices[0].message.content
                    return self._parse_text_result(content)
            
            # 如果没有deepseek，使用其他API
            elif self.api_client.openai_client:
                response = self.api_client.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0.1
                )
                
                if response.choices[0].message.tool_calls:
                    tool_call = response.choices[0].message.tool_calls[0]
                    function_args = json.loads(tool_call.function.arguments)
                    return function_args
                else:
                    content = response.choices[0].message.content
                    return self._parse_text_result(content)
            
            else:
                return {"error": "没有可用的API客户端"}
                
        except Exception as e:
            logger.error(f"调用OpenAI API失败: {e}")
            return {"error": str(e)}
    
    def _parse_text_result(self, content: str) -> Dict[str, Any]:
        """解析文本结果"""
        try:
            # 尝试从文本中提取JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "{" in content and "}" in content:
                # 查找第一个完整的JSON对象
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                # 创建默认结构
                return {
                    "场景数量": 1,
                    "场景摘要": [{
                        "场景ID": 1,
                        "事件": "场景重建解析失败",
                        "变化": "无法解析场景变化",
                        "关键细节": [content],
                        "时间范围": "未知",
                        "参与者": ["unknown"],
                        "情感基调": "中性"
                    }]
                }
        except Exception as e:
            logger.warning(f"解析文本结果失败: {e}")
            return {"error": f"解析失败: {content}"}
    
    def validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证和规范化结果"""
        if "error" in result:
            return result
        
        try:
            # 确保必需字段存在
            if "场景数量" not in result:
                result["场景数量"] = len(result.get("场景摘要", []))
            
            if "场景摘要" not in result:
                result["场景摘要"] = []
            
            # 规范化场景摘要
            for i, scene in enumerate(result["场景摘要"]):
                if "场景ID" not in scene:
                    scene["场景ID"] = i + 1
                
                # 确保必需字段存在
                required_fields = ["事件", "变化", "关键细节"]
                for field in required_fields:
                    if field not in scene:
                        scene[field] = "未知" if field != "关键细节" else []
                
                # 确保可选字段存在
                optional_fields = {
                    "时间范围": "未知",
                    "参与者": ["unknown"],
                    "情感基调": "中性"
                }
                for field, default_value in optional_fields.items():
                    if field not in scene:
                        scene[field] = default_value
            
            return result
            
        except Exception as e:
            logger.error(f"验证结果失败: {e}")
            return {"error": str(e)}


# 全局实例
scenery_rebuilder = EnhancedSceneryRebuild()


# 便捷函数
def rebuild_scene(conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    重建家庭教育场景
    
    Args:
        conversations: 对话列表，格式为 [{"speaker": "...", "content": "..."}]
    
    Returns:
        Dict: 场景重建结果
    """
    logger.info("开始场景重建")
    
    try:
        # 格式化转录文本
        formatted_text = _format_transcript(conversations)
        
        if not formatted_text or len(formatted_text.strip()) < 50:
            logger.warning("转录文本内容过少，无法进行场景重建")
            return {
                "场景数量": 0,
                "场景摘要": [],
                "error": "转录文本内容过少"
            }
        
        # 使用zhizhengzheng接口的function calling进行场景重建
        system_prompt = """
        你是一个专业的亲子教育场景分析师。请根据提供的亲子对话记录，重建家庭教育场景。
        你需要识别对话中的不同场景，每个场景应该包含完整的教育互动过程。
        
        除了考虑对话间隔，还应关注主题变化、参与者变动、情感基调转变等因素来判断新场景的开始。
        """
        
        user_prompt = """
        请分析以下亲子对话，识别并重建家庭教育场景。对每个场景提供详细分析，包括：
        1. 场景中的主要教育事件
        2. 家长和孩子行为的动态变化过程  
        3. 能体现场景特点的关键对话片段
        
        请使用提供的工具函数来结构化输出结果。
        """
        
        # 使用tx_deepseek模块的Scenery_rebuild类
        from .tx_deepseek import Scenery_rebuild
        
        logger.info("使用zhizhengzheng接口进行场景重建")
        scenery_rebuild = Scenery_rebuild(
            input_data=formatted_text,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        # 执行场景重建
        result = scenery_rebuild.final_handle()
        
        if isinstance(result, dict) and "场景摘要" in result:
            logger.info(f"场景重建完成，识别出{result.get('场景数量', 0)}个场景")
            return result
        else:
            logger.warning("场景重建返回格式异常")
            return {
                "场景数量": 0,
                "场景摘要": [],
                "error": "场景重建返回格式异常"
            }
            
    except Exception as e:
        logger.error(f"场景重建失败: {e}")
        return {
            "场景数量": 0,
            "场景摘要": [],
            "error": f"场景重建失败: {str(e)}"
        }


# 兼容性类 - 保持与原有代码的兼容性
class Scenery_rebuild:
    """兼容性类，保持与原有代码的兼容性"""
    
    def __init__(self):
        self.enhanced_rebuilder = scenery_rebuilder
    
    def rebuild_scene(self, transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
        """重建场景"""
        return rebuild_scene(transcript)
    
    def Scenery_rebuild(self, arguments: List[Dict[str, Any]]) -> str:
        """兼容性方法"""
        try:
            if isinstance(arguments, dict):
                return json.dumps(arguments, ensure_ascii=False)
            elif isinstance(arguments, list):
                result = {
                    "场景数量": len(arguments),
                    "场景摘要": arguments
                }
                return json.dumps(result, ensure_ascii=False)
            else:
                return json.dumps({"error": "Invalid arguments"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False) 