# -*- coding: utf-8 -*-
import logging
import asyncio
import json
import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError

# 数据库模型导入 (从顶层 app 导入)
from ..extensions import db
from ..models import (
    ConflictScene as ConflictSceneDBModel, # 使用别名区分数据库模型
    BehaviorScene as BehaviorSceneDBModel, # 使用别名区分数据库模型
    ConflictTypeEnum,
    ConflictSeverityEnum,
    BehaviorTypeEnum,
    BehaviorSeverityEnum
)

# API 和 Prompt 导入
from .api import call_llm_async
# 假设这些 Prompt 已在 prompt.py 定义
# 注意：确保 prompt.py 包含这些变量的定义
try:
    from .prompt import (
        CONFLICT_ANALYSIS_SYSTEM_PROMPT, CONFLICT_ANALYSIS_USER_TEMPLATE,
        BEHAVIOR_ANALYSIS_SYSTEM_PROMPT, BEHAVIOR_ANALYSIS_USER_TEMPLATE
    )
except ImportError:
    # 如果 prompt.py 尚未创建或缺少这些变量，提供默认值或记录错误
    logger = logging.getLogger(__name__)
    logger.error("无法从 prompt.py 导入分析 Prompts, 请确保文件存在且包含所需变量. 将使用占位符.")
    CONFLICT_ANALYSIS_SYSTEM_PROMPT = "System prompt for conflict analysis needed."
    CONFLICT_ANALYSIS_USER_TEMPLATE = "Analyze conflict: {transcript} Date: {date}"
    BEHAVIOR_ANALYSIS_SYSTEM_PROMPT = "System prompt for behavior analysis needed."
    BEHAVIOR_ANALYSIS_USER_TEMPLATE = "Analyze behavior: {transcript} Date: {date}"


logger = logging.getLogger(__name__)

# --- Pydantic 模型定义 (用于 API 输出解析和类型检查) ---

class ConflictTypeData(str, Enum):
    """冲突类型 - Pydantic Enum (与 DB Enum 保持一致)"""
    EC = "期望和目标冲突"
    CC = "沟通和互动方式冲突"
    LMC = "学习过程与方法冲突"
    RC = "规则与控制冲突"
    TMC = "时间与精力管理冲突"
    KC = "知识水平与理解差异冲突"
    FC = "注意力和专注度冲突"
    # 根据 script_analysis.py 添加其他类型
    OT = "其他"

class SeverityLevelData(str, Enum):
    """严重程度 - Pydantic Enum (与 DB Enum 保持一致)"""
    High = "高"
    Medium = "中"
    Low = "低"

class ConflictSceneData(BaseModel):
    """冲突场景的数据模型 (Pydantic)"""
    scene_id: int
    trigger: str = Field(..., description="用中文描述冲突触发点")
    process: str = Field(..., description="用中文描述冲突发展过程")
    conflict_type: ConflictTypeData = Field(..., description="冲突类型")
    severity: SeverityLevelData = Field(..., description="冲突强度等级")
    dt: str = Field(..., description="格式为 YYYYMMDD") # LLM 返回字符串，保存时转换

class ConflictAnalysisOutput(BaseModel):
    """冲突分析的整体输出模型"""
    scenes: List[ConflictSceneData]

class BehaviorTypeData(str, Enum):
    """行为类型 - Pydantic Enum (与 DB Enum 保持一致)"""
    ENC = "鼓励"
    SP = "有标注表扬"
    GP = "无标注表扬"
    GI = "启发式指导"
    SR = "设定规则"
    SRS = "敏感性回应"
    DI = "非启发式指导"
    IT = "信息教授"
    EC = "纠正错误"
    MON = "监督检查"
    DC = "直接命令"
    IC = "间接命令"
    CB = "批评责备"
    FT = "强迫威胁"
    NI = "忽视冷漠"
    BD = "贬低质疑"
    FD = "沮丧失望"
    II = "急躁不耐"
    OT = "其他"

class BehaviorSeverityData(str, Enum):
    """行为严重性/分类 - Pydantic Enum (与 DB Enum 保持一致)"""
    积极 = "积极"
    中性 = "中性"
    消极 = "消极"

class BehaviorSceneData(BaseModel):
    """行为场景的数据模型 (Pydantic)"""
    behaviour_id: int
    description: str = Field(..., description="用中文描述行为")
    code: BehaviorTypeData = Field(..., description="行为种类")
    type: BehaviorSeverityData = Field(..., description="行为类型 (积极/中性/消极)")
    dt: str = Field(..., description="日期时间，格式为 YYYYMMDD")

class BehaviorAnalysisOutput(BaseModel):
    """行为分析的整体输出模型"""
    scenes: List[BehaviorSceneData]

# --- 分析类定义 ---

class ConflictAnalysis:
    """执行冲突场景分析"""
    def __init__(self):
        # 这里可以初始化客户端或其他配置，但现在api.py处理了客户端
        pass

    async def analyze_conflict(self, transcripts: List[dict], date: str) -> ConflictAnalysisOutput:
        """异步执行冲突分析"""
        logger.info(f"开始冲突分析, 日期: {date}")
        transcript_text = "\n".join([f"{seg['speaker']}: {seg['text']}" for seg in transcripts])
        user_content = CONFLICT_ANALYSIS_USER_TEMPLATE.format(transcript=transcript_text, date=date)
        
        messages = [
            {"role": "system", "content": CONFLICT_ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        # 调用 LLM API (示例: 使用智增增的 deepseek-chat)
        # 需要根据实际效果选择合适的模型和 client_type
        response_str = await call_llm_async(
            client_type='zhizengzeng', 
            model='deepseek-chat', # 或其他模型如 gpt-4o (azure)
            messages=messages,
            temperature=0.1, # 低温以获得更一致的结构化输出
            response_format={"type": "json_object"} # 请求 JSON 输出
        )

        if not response_str:
            logger.error("冲突分析 LLM 调用失败或返回空")
            # 返回空的有效 Pydantic 对象
            return ConflictAnalysisOutput(scenes=[])

        try:
            # 尝试解析 JSON
            result_data = json.loads(response_str)
            # 使用 Pydantic 进行验证和转换
            validated_output = ConflictAnalysisOutput.parse_obj(result_data)
            logger.info(f"冲突分析成功, 识别到 {len(validated_output.scenes)} 个场景.")
            return validated_output
        except json.JSONDecodeError as e:
            logger.error(f"冲突分析 LLM 响应 JSON 解析失败: {e}\n响应内容: {response_str}")
        except ValidationError as e:
             logger.error(f"冲突分析 Pydantic 验证失败: {e}\n响应内容: {response_str}")
        except Exception as e:
            logger.error(f"处理冲突分析结果时发生未知错误: {e}\n响应内容: {response_str}")
            
        # 如果解析或验证失败，返回空结果
        return ConflictAnalysisOutput(scenes=[])

class BehaviorAnalysis:
    """执行行为场景分析"""
    def __init__(self):
        pass

    async def analyze_behavior(self, transcripts: List[dict], date: str) -> BehaviorAnalysisOutput:
        """异步执行行为分析"""
        logger.info(f"开始行为分析, 日期: {date}")
        transcript_text = "\n".join([f"{seg['speaker']}: {seg['text']}" for seg in transcripts])
        user_content = BEHAVIOR_ANALYSIS_USER_TEMPLATE.format(transcript=transcript_text, date=date)
        
        messages = [
            {"role": "system", "content": BEHAVIOR_ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        # 调用 LLM API (示例: 使用智增增的 deepseek-chat)
        response_str = await call_llm_async(
            client_type='zhizengzeng', 
            model='deepseek-chat',
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        if not response_str:
            logger.error("行为分析 LLM 调用失败或返回空")
            return BehaviorAnalysisOutput(scenes=[])

        try:
            result_data = json.loads(response_str)
            validated_output = BehaviorAnalysisOutput.parse_obj(result_data)
            logger.info(f"行为分析成功, 识别到 {len(validated_output.scenes)} 个场景.")
            return validated_output
        except json.JSONDecodeError as e:
            logger.error(f"行为分析 LLM 响应 JSON 解析失败: {e}\n响应内容: {response_str}")
        except ValidationError as e:
             logger.error(f"行为分析 Pydantic 验证失败: {e}\n响应内容: {response_str}")
        except Exception as e:
            logger.error(f"处理行为分析结果时发生未知错误: {e}\n响应内容: {response_str}")

        return BehaviorAnalysisOutput(scenes=[])

# --- 核心分析函数 --- 

async def analyze_transcripts_for_profile(
    transcripts: List[dict], 
    date: str, 
    file_id: str, # file_id 可能不需要传入分析类，但在日志中有用
    analysis_id: int # analysis_id 可能不需要传入分析类
) -> Tuple[ConflictAnalysisOutput, BehaviorAnalysisOutput]:
    """
    异步执行亲子画像分析 (冲突和行为)。
    调用分析类，返回 Pydantic 模型结果，不执行数据库保存。
    """
    logger.info(f"开始亲子画像分析 (冲突和行为): file_id={file_id}, analysis_id={analysis_id}")
    
    conflict_analyzer = ConflictAnalysis()
    behavior_analyzer = BehaviorAnalysis()

    # 并行执行冲突和行为分析
    analysis_tasks = [
        asyncio.create_task(conflict_analyzer.analyze_conflict(transcripts, date)),
        asyncio.create_task(behavior_analyzer.analyze_behavior(transcripts, date))
    ]
    
    results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
    
    conflict_result = results[0]
    behavior_result = results[1]

    # 检查是否有异常
    if isinstance(conflict_result, Exception):
        logger.error(f"冲突分析任务失败: {conflict_result}", exc_info=conflict_result)
        # 即使一个失败，也尝试返回另一个的结果 (如果成功的话)
        # 或者根据业务逻辑决定是否整体失败
        conflict_result = ConflictAnalysisOutput(scenes=[]) # 返回空结果
        # raise ValueError("冲突分析失败") from conflict_result # 或者抛出异常
        
    if isinstance(behavior_result, Exception):
        logger.error(f"行为分析任务失败: {behavior_result}", exc_info=behavior_result)
        behavior_result = BehaviorAnalysisOutput(scenes=[]) # 返回空结果
        # raise ValueError("行为分析失败") from behavior_result
        
    # 确保返回的是正确的 Pydantic 类型实例
    if not isinstance(conflict_result, ConflictAnalysisOutput):
         logger.error("冲突分析返回了非预期的类型")
         conflict_result = ConflictAnalysisOutput(scenes=[])
    if not isinstance(behavior_result, BehaviorAnalysisOutput):
         logger.error("行为分析返回了非预期的类型")
         behavior_result = BehaviorAnalysisOutput(scenes=[])

    logger.info(f"亲子画像分析完成: file_id={file_id}")
    return conflict_result, behavior_result

# --- 数据库保存函数 ---

async def save_analysis_results_to_db(
    conflict_result: ConflictAnalysisOutput, 
    behavior_result: BehaviorAnalysisOutput, 
    file_id: str, 
    analysis_id: int
):
    """
    将分析结果（冲突场景和行为场景）保存到数据库。
    
    Args:
        conflict_result: 冲突分析的 Pydantic 结果对象
        behavior_result: 行为分析的 Pydantic 结果对象
        file_id: 音频文件 ID
        analysis_id: 分析记录 ID
    """
    logger.info(f"开始保存分析场景到数据库: file_id={file_id}, analysis_id={analysis_id}")
    try:
        def sync_save():
            # 使用 db.session.begin() 来确保事务的原子性
            with db.session.begin():
                saved_conflicts = 0
                # 保存冲突场景
                for scene_data in conflict_result.scenes:
                    try:
                        dt_obj = datetime.datetime.strptime(scene_data.dt, '%Y%m%d').date()
                        # 检查 Enum 值是否存在于数据库 Enum 中
                        conflict_type_enum = ConflictTypeEnum[scene_data.conflict_type.name]
                        severity_enum = ConflictSeverityEnum[scene_data.severity.name]
                        
                        new_scene = ConflictSceneDBModel(
                            file_id=file_id,
                            analysis_id=analysis_id,
                            scene_id=scene_data.scene_id,
                            trigger=scene_data.trigger,
                            process=scene_data.process,
                            conflict_type=conflict_type_enum,
                            severity=severity_enum,
                            dt=dt_obj
                        )
                        db.session.add(new_scene)
                        saved_conflicts += 1
                    except (KeyError, ValueError) as e:
                            logger.warning(f"跳过无效的冲突场景数据 (Enum或日期格式错误): {scene_data}, error: {e}")
                    except Exception as e:
                            logger.error(f"保存冲突场景 #{scene_data.scene_id} 时发生意外错误: {e}", exc_info=True)
                            # 选择继续处理其他场景

                saved_behaviors = 0
                # 保存行为场景
                for scene_data in behavior_result.scenes:
                    try:
                        dt_obj = datetime.datetime.strptime(scene_data.dt, '%Y%m%d').date()
                        # 检查 Enum 值
                        code_enum = BehaviorTypeEnum[scene_data.code.name]
                        type_enum = BehaviorSeverityEnum[scene_data.type.name]
                        
                        new_scene = BehaviorSceneDBModel(
                            file_id=file_id,
                            analysis_id=analysis_id,
                            behaviour_id=scene_data.behaviour_id,
                            description=scene_data.description,
                            code=code_enum,
                            type=type_enum,
                            dt=dt_obj
                        )
                        db.session.add(new_scene)
                        saved_behaviors += 1
                    except (KeyError, ValueError) as e:
                        logger.warning(f"跳过无效的行为场景数据 (Enum或日期格式错误): {scene_data}, error: {e}")
                    except Exception as e:
                        logger.error(f"保存行为场景 #{scene_data.behaviour_id} 时发生意外错误: {e}", exc_info=True)
                
                # db.session.commit() # db.session.begin() 会自动提交或回滚
                logger.info(f"成功处理 {saved_conflicts} 个冲突场景和 {saved_behaviors} 个行为场景的保存操作.")

        # 使用 to_thread 执行同步数据库操作
        await asyncio.to_thread(sync_save)
        
    except Exception as e:
        # sync_save 内部的 db.session.begin() 应该已经处理了回滚
        logger.error(f"保存分析场景到数据库的事务处理中发生错误: {e}", exc_info=True)
        # 根据需要决定是否需要在这里再次尝试回滚
        # try:
        #      await asyncio.to_thread(db.session.rollback)
        # except Exception as rb_err:
        #      logger.error(f"数据库回滚尝试失败: {rb_err}")
        raise ValueError("保存分析场景到数据库时发生错误") from e # 重新抛出包装后的异常 