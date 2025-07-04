# -*- coding: utf-8 -*-
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field, ValidationError # 如果需要返回 Pydantic 模型

# API 和 Prompt 导入
from .api import call_llm_async
try:
    from .prompt import SCENERY_SYSTEM_PROMPT, SCENERY_USER_TEMPLATE
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("无法从 prompt.py 导入场景重建 Prompts。将使用占位符。")
    SCENERY_SYSTEM_PROMPT = "You are an expert in analyzing parent-child dialogues to reconstruct educational scenarios."
    SCENERY_USER_TEMPLATE = "Analyze the following transcript and identify distinct educational scenarios:\n\n{transcript}"

logger = logging.getLogger(__name__)

# --- Pydantic 模型 (可选，用于定义输出结构) ---
class ScenarioDetail(BaseModel):
    事件: str = Field(..., description="详细描述场景中的主要教育事件，包括主题（如作业辅导、行为管教）、参与者、核心互动过程和结果。")
    变化: str = Field(..., description="这个场景中家长行为和孩子行为的动态变化过程。")
    关键细节: List[str] = Field(..., description="提取能体现场景特点的关键对话片段。包括情感强烈、体现教育方法或反映问题核心的对话。每个片段应标注说话者和情感色彩。")

class SceneryRebuildOutput(BaseModel):
    场景数量: int
    场景摘要: List[ScenarioDetail]

# --- 场景重建类 ---
class SceneryRebuilder:
    """
    使用 LLM (具备 Function Calling 能力) 分析亲子对话以重建家庭教育场景。
    """
    def __init__(self):
        # 无需初始化客户端，将在调用时使用 api.py 中的函数
        self.tool_name = "Scenery_rebuild_tool" # 工具名称保持一致
        self.tools = self._define_tools()
        logger.info("Initialized SceneryRebuilder")

    def _define_tools(self) -> List[Dict[str, Any]]:
        """定义 LLM Function Calling 的工具结构"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": self.tool_name,
                    "description": "根据提供的亲子对话文本分析并结构化地提取不同的家庭教育场景",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "场景摘要": {
                                "type": "array",
                                "description": "识别出的所有独立教育场景的列表。每个场景应侧重一个核心主题或互动。",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "事件": {
                                            "type": "string",
                                            "description": "用简洁的语言概括这个场景的核心教育事件或互动主题 (例如：'辅导数学作业', '讨论屏幕时间规则', '睡前故事')。"
                                        },
                                        "变化": {
                                            "type": "string",
                                            "description": "描述在此场景中观察到的主要互动模式或行为/情绪变化 (例如：'从耐心指导转变为不耐烦', '孩子从抗拒变为合作', '家长提出要求，孩子回避')。"
                                        },
                                        "关键细节": {
                                            "type": "array",
                                            "description": "引用1-3句最能体现此场景特点或转折点的关键对话原文。需包含说话者标识 (如 '家长:' 或 '孩子:')。",
                                            "items": {
                                                "type": "string"
                                            }
                                        }
                                    },
                                    "required": ["事件", "变化", "关键细节"]
                                }
                            }
                        },
                        "required": ["场景摘要"]
                    }
                }
            }
        ]
        return tools

    async def rebuild_scenarios_async(
        self, 
        transcript: List[Dict[str, Any]],
        client_type: str = 'zhizengzeng', # 默认使用的 LLM 客户端
        model: str = 'deepseek-chat'     # 默认使用的模型
    ) -> Optional[SceneryRebuildOutput]: # 返回 Pydantic 模型或 None
        """
        异步调用 LLM 进行场景重建。

        Args:
            transcript: 标准化后的转录列表。
            client_type: 要使用的 LLM 客户端类型 ('azure', 'volcengine', 'zhizengzeng')。
            model: 要使用的 LLM 模型名称。

        Returns:
            包含场景重建结果的 Pydantic 对象，如果失败则返回 None。
        """
        logger.info(f"开始场景重建，使用模型: {client_type}/{model}")
        if not transcript:
            logger.warning("输入的转录为空，无法进行场景重建。")
            return None
            
        transcript_text = "\n".join([f"{seg.get('speaker','未知')}: {seg.get('text','')}" for seg in transcript])
        user_content = SCENERY_USER_TEMPLATE.format(transcript=transcript_text)

        messages = [
            {"role": "system", "content": SCENERY_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        try:
            # 调用 LLM 并强制使用定义的工具
            response = await call_llm_async(
                client_type=client_type,
                model=model,
                messages=messages,
                tools=self.tools,
                tool_choice={"type": "function", "function": {"name": self.tool_name}},
                temperature=0.0 # Function calling 通常需要确定性
            )
            
            # call_llm_async 返回的是 content 字符串，对于 tool_calls 需要额外处理
            # 或者修改 call_llm_async 返回完整的 completion 对象
            # --- 假设 call_llm_async 需要修改以支持返回 tool_calls --- 
            # TODO: 修改 api.py 中的 call_llm_async 以便能获取 tool_calls
            # 以下是假设能获取 tool_calls 后的逻辑

            # --- 临时替代逻辑：假设 LLM 直接在 content 中返回 JSON --- 
            # 这种方式不稳定，强烈建议修改 call_llm_async 支持 tool_calls
            if not response: 
                logger.error(f"场景重建 LLM ({client_type}/{model}) 调用返回空")
                return None
                
            logger.debug(f"场景重建 LLM 原始响应: {response}")
            
            # 尝试解析响应字符串为 JSON
            try:
                # 清理可能的 markdown 代码块
                if response.startswith("```json"):
                     response = response[len("```json"): -len("```")].strip()
                elif response.startswith("```"):
                     response = response[len("```"): -len("```")].strip()
                     
                arguments_json = json.loads(response) 
                
                # 假设 JSON 结构直接是 parameters 的内容
                if "场景摘要" not in arguments_json:
                     logger.error("场景重建 LLM 响应 JSON 缺少 '场景摘要' 键。")
                     return None
                     
                # 添加场景数量
                arguments_json["场景数量"] = len(arguments_json["场景摘要"])
                
                # 使用 Pydantic 模型进行验证
                validated_output = SceneryRebuildOutput.parse_obj(arguments_json)
                logger.info(f"场景重建成功，识别到 {validated_output.场景数量} 个场景。")
                return validated_output
                
            except json.JSONDecodeError as e:
                logger.error(f"场景重建 LLM 响应 JSON 解析失败: {e}. 响应: {response}")
                return None
            except ValidationError as e:
                logger.error(f"场景重建 Pydantic 验证失败: {e}. 响应: {response}")
                return None
            except Exception as e:
                 logger.error(f"处理场景重建响应时发生未知错误: {e}. 响应: {response}", exc_info=True)
                 return None
                 
            # --- End of 临时替代逻辑 ---
            
        except Exception as e:
            logger.error(f"调用场景重建 LLM 时出错: {e}", exc_info=True)
            return None

# --- 示例用法 (可选) ---
# async def main():
#     # 示例转录数据
#     sample_transcript = [
#         {'speaker': '家长', 'text': '快点写作业，别磨蹭了。'},
#         {'speaker': '孩子', 'text': '我还在想刚才那个问题呢。'},
#         {'speaker': '家长', 'text': '有什么好想的，赶紧写！'},
#         {'speaker': '孩子', 'text': '可是...好吧。'},
#         {'speaker': '家长', 'text': '吃饭了，别看电视了。'},
#         {'speaker': '孩子', 'text': '就看一小会儿嘛。'}
#     ]
#     
#     rebuilder = SceneryRebuilder()
#     scenarios_output = await rebuilder.rebuild_scenarios_async(sample_transcript)
#     
#     if scenarios_output:
#         print("场景重建结果:")
#         print(scenarios_output.json(indent=4, ensure_ascii=False))
#     else:
#         print("场景重建失败。")
# 
# if __name__ == "__main__":
#     asyncio.run(main()) 