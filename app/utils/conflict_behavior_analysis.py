# -*- coding: utf-8 -*-
"""
冲突行为分析模块
包含冲突类型分析和行为模式分析功能
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from .api_clients import api_client, chat_with_fallback, chat_with_fallback_async
from .prompt import conflict_analysis, behavior_analysis

logger = logging.getLogger(__name__)


class ConflictType(str, Enum):
    """冲突类型枚举"""
    EC = "期望和目标冲突"
    CC = "沟通和互动方式冲突"
    LMC = "学习过程与方法冲突"
    RC = "规则与控制冲突"
    TMC = "时间与精力管理冲突"
    KC = "知识水平与理解差异冲突"
    FC = "注意力和专注度冲突"


class SeverityLevel(str, Enum):
    """严重程度等级"""
    High = "高"
    Medium = "中"
    Low = "低"


class ConflictScene(BaseModel):
    """冲突场景模型"""
    scene_id: int
    trigger: str  # 用中文描述冲突触发点
    process: str  # 用中文描述冲突发展过程
    conflict_type: ConflictType  # 冲突类型
    severity: SeverityLevel  # 冲突强度等级
    dt: int  # 格式为"YYYYMMDD"


class ConflictAnalysisOutput(BaseModel):
    """冲突分析输出模型"""
    scenes: List[ConflictScene]


class ConflictAnalysis:
    """冲突分析器"""
    
    def __init__(self):
        self.api_client = api_client
        self.new_template = """
        你是一个专业的家庭关系分析师，请根据以下对话记录分析亲子互动中存在的冲突。
        
        请分析以下几个方面：
        1. 冲突触发点 - 导致冲突的具体事件或话题
        2. 冲突发展过程 - 冲突是如何升级或缓解的
        3. 冲突类型 - 从以下类型中选择最匹配的：
           - EC: 期望和目标冲突
           - CC: 沟通和互动方式冲突
           - LMC: 学习过程与方法冲突
           - RC: 规则与控制冲突
           - TMC: 时间与精力管理冲突
           - KC: 知识水平与理解差异冲突
           - FC: 注意力和专注度冲突
        4. 严重程度 - 评估冲突的严重程度（高/中/低）
        
        请以JSON格式返回分析结果，包含以下字段：
        - scene_id: 场景编号
        - trigger: 冲突触发点描述
        - process: 冲突发展过程描述
        - conflict_type: 冲突类型代码
        - severity: 严重程度
        - dt: 日期（格式YYYYMMDD）
        
        对话记录：
        {transcript}
        """
    
    def analyze_conflict(self, transcripts: List[dict], date: str, use_original_prompt: bool = False) -> ConflictAnalysisOutput:
        """分析冲突"""
        logger.info(f"开始分析冲突，日期: {date}, 使用原始prompt: {use_original_prompt}")
        
        try:
            # 计算输入token数量
            input_text = str(transcripts)
            
            # 格式化日期
            formatted_date = date.replace('-', '') if '-' in date else date
            
            # 选择prompt模板
            if use_original_prompt:
                # 使用原有的prompt
                prompt = conflict_analysis(input_text)
            else:
                # 使用新的prompt
                prompt = self.new_template.format(transcript=input_text)
            
            # 使用回退策略调用API
            try:
                result = chat_with_fallback(prompt, "请分析以上对话中的冲突。")
                
                # 解析结果
                scenes = self._parse_conflict_result(result, formatted_date)
                logger.info(f"冲突分析完成，识别出 {len(scenes)} 个冲突场景")
                
                return ConflictAnalysisOutput(scenes=scenes)
                
            except Exception as e:
                logger.error(f"分析冲突时发生错误: {e}")
                return ConflictAnalysisOutput(scenes=[])
                
        except Exception as e:
            logger.error(f"冲突分析失败: {e}")
            return ConflictAnalysisOutput(scenes=[])
    
    async def analyze_conflict_async(self, transcripts: List[dict], date: str, use_original_prompt: bool = False) -> ConflictAnalysisOutput:
        """异步分析冲突"""
        logger.info(f"开始异步分析冲突，日期: {date}, 使用原始prompt: {use_original_prompt}")
        
        try:
            # 计算输入token数量
            input_text = str(transcripts)
            
            # 格式化日期
            formatted_date = date.replace('-', '') if '-' in date else date
            
            # 选择prompt模板
            if use_original_prompt:
                # 使用原有的prompt
                prompt = conflict_analysis(input_text)
            else:
                # 使用新的prompt
                prompt = self.new_template.format(transcript=input_text)
            
            # 使用回退策略调用API
            try:
                result = await chat_with_fallback_async(prompt, "请分析以上对话中的冲突。")
                
                # 解析结果
                scenes = self._parse_conflict_result(result, formatted_date)
                logger.info(f"异步冲突分析完成，识别出 {len(scenes)} 个冲突场景")
                
                return ConflictAnalysisOutput(scenes=scenes)
                
            except Exception as e:
                logger.error(f"异步分析冲突时发生错误: {e}")
                return ConflictAnalysisOutput(scenes=[])
                
        except Exception as e:
            logger.error(f"异步冲突分析失败: {e}")
            return ConflictAnalysisOutput(scenes=[])
    
    def _parse_conflict_result(self, result: str, date: str) -> List[ConflictScene]:
        """解析冲突分析结果"""
        scenes = []
        
        try:
            # 尝试解析JSON
            import json
            
            # 清理结果字符串
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(result)
            
            # 处理单个场景或场景列表
            if isinstance(data, dict):
                if "scenes" in data:
                    scenes_data = data["scenes"]
                else:
                    scenes_data = [data]
            else:
                scenes_data = data
            
            # 构建场景对象
            for i, scene_data in enumerate(scenes_data):
                scene = ConflictScene(
                    scene_id=scene_data.get("scene_id", i + 1),
                    trigger=scene_data.get("trigger", "未知触发点"),
                    process=scene_data.get("process", "未知过程"),
                    conflict_type=ConflictType(scene_data.get("conflict_type", "EC")),
                    severity=SeverityLevel(scene_data.get("severity", "Medium")),
                    dt=int(date)
                )
                scenes.append(scene)
                
        except Exception as e:
            logger.warning(f"解析冲突结果失败: {e}")
            # 返回默认场景
            scenes = [ConflictScene(
                scene_id=1,
                trigger="解析失败",
                process="无法解析分析结果",
                conflict_type=ConflictType.EC,
                severity=SeverityLevel.Medium,
                dt=int(date)
            )]
        
        return scenes


class BehaviorType(str, Enum):
    """行为类型枚举"""
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


class BehaviorSeverityLevel(str, Enum):
    """行为严重程度等级"""
    积极 = "积极"
    中性 = "中性"
    消极 = "消极"


class BehaviorScene(BaseModel):
    """行为场景模型"""
    behaviour_id: int
    description: str  # 用中文描述行为
    code: BehaviorType  # 行为种类
    type: BehaviorSeverityLevel  # 行为类型
    dt: str  # 日期时间，格式为"YYYYMMDD"


class BehaviorAnalysisOutput(BaseModel):
    """行为分析输出模型"""
    scenes: List[BehaviorScene]


class BehaviorAnalysis:
    """行为分析器"""
    
    def __init__(self):
        self.api_client = api_client
        self.new_template = """
        你是一个专业的亲子行为分析师，请根据以下对话记录分析父母的教育行为。
        
        请识别并分析以下行为类型：
        积极行为：
        - ENC: 鼓励
        - SP: 有标注表扬
        - GP: 无标注表扬
        - GI: 启发式指导
        - SR: 设定规则
        - SRS: 敏感性回应
        - DI: 非启发式指导
        - IT: 信息教授
        - EC: 纠正错误
        - MON: 监督检查
        
        中性行为：
        - DC: 直接命令
        - IC: 间接命令
        
        消极行为：
        - CB: 批评责备
        - FT: 强迫威胁
        - NI: 忽视冷漠
        - BD: 贬低质疑
        - FD: 沮丧失望
        - II: 急躁不耐
        
        请以JSON格式返回分析结果，包含以下字段：
        - behaviour_id: 行为编号
        - description: 行为描述
        - code: 行为类型代码
        - type: 行为倾向（积极/中性/消极）
        - dt: 日期（格式YYYYMMDD）
        
        对话记录：
        {transcript}
        """
    
    def analyze_behavior(self, transcripts: List[dict], date: str, use_original_prompt: bool = False) -> BehaviorAnalysisOutput:
        """分析行为"""
        logger.info(f"开始分析行为，日期: {date}, 使用原始prompt: {use_original_prompt}")
        
        try:
            # 计算输入token数量
            input_text = str(transcripts)
            
            # 格式化日期
            formatted_date = date.replace('-', '') if '-' in date else date
            
            # 选择prompt模板
            if use_original_prompt:
                # 使用原有的prompt
                prompt = behavior_analysis(input_text, None)  # 假设不需要第二个参数
            else:
                # 使用新的prompt
                prompt = self.new_template.format(transcript=input_text)
            
            # 使用回退策略调用API
            try:
                result = chat_with_fallback(prompt, "请分析以上对话中的行为模式。")
                
                # 解析结果
                scenes = self._parse_behavior_result(result, formatted_date)
                logger.info(f"行为分析完成，识别出 {len(scenes)} 个行为场景")
                
                return BehaviorAnalysisOutput(scenes=scenes)
                
            except Exception as e:
                logger.error(f"分析行为时发生错误: {e}")
                return BehaviorAnalysisOutput(scenes=[])
                
        except Exception as e:
            logger.error(f"行为分析失败: {e}")
            return BehaviorAnalysisOutput(scenes=[])
    
    async def analyze_behavior_async(self, transcripts: List[dict], date: str, use_original_prompt: bool = False) -> BehaviorAnalysisOutput:
        """异步分析行为"""
        logger.info(f"开始异步分析行为，日期: {date}, 使用原始prompt: {use_original_prompt}")
        
        try:
            # 计算输入token数量
            input_text = str(transcripts)
            
            # 格式化日期
            formatted_date = date.replace('-', '') if '-' in date else date
            
            # 选择prompt模板
            if use_original_prompt:
                # 使用原有的prompt
                prompt = behavior_analysis(input_text, None)  # 假设不需要第二个参数
            else:
                # 使用新的prompt
                prompt = self.new_template.format(transcript=input_text)
            
            # 使用回退策略调用API
            try:
                result = await chat_with_fallback_async(prompt, "请分析以上对话中的行为模式。")
                
                # 解析结果
                scenes = self._parse_behavior_result(result, formatted_date)
                logger.info(f"异步行为分析完成，识别出 {len(scenes)} 个行为场景")
                
                return BehaviorAnalysisOutput(scenes=scenes)
                
            except Exception as e:
                logger.error(f"异步分析行为时发生错误: {e}")
                return BehaviorAnalysisOutput(scenes=[])
                
        except Exception as e:
            logger.error(f"异步行为分析失败: {e}")
            return BehaviorAnalysisOutput(scenes=[])
    
    def _parse_behavior_result(self, result: str, date: str) -> List[BehaviorScene]:
        """解析行为分析结果"""
        scenes = []
        
        try:
            # 尝试解析JSON
            import json
            
            # 清理结果字符串
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(result)
            
            # 处理单个场景或场景列表
            if isinstance(data, dict):
                if "scenes" in data:
                    scenes_data = data["scenes"]
                else:
                    scenes_data = [data]
            else:
                scenes_data = data
            
            # 构建场景对象
            for i, scene_data in enumerate(scenes_data):
                scene = BehaviorScene(
                    behaviour_id=scene_data.get("behaviour_id", i + 1),
                    description=scene_data.get("description", "未知行为"),
                    code=BehaviorType(scene_data.get("code", "ENC")),
                    type=BehaviorSeverityLevel(scene_data.get("type", "中性")),
                    dt=date
                )
                scenes.append(scene)
                
        except Exception as e:
            logger.warning(f"解析行为结果失败: {e}")
            # 返回默认场景
            scenes = [BehaviorScene(
                behaviour_id=1,
                description="解析失败",
                code=BehaviorType.ENC,
                type=BehaviorSeverityLevel.中性,
                dt=date
            )]
        
        return scenes


def analyze_conflict_and_behavior(transcripts: List[dict], date: str, use_original_prompt: bool = False) -> tuple:
    """分析冲突和行为"""
    conflict_analyzer = ConflictAnalysis()
    behavior_analyzer = BehaviorAnalysis()
    
    conflict_result = conflict_analyzer.analyze_conflict(transcripts, date, use_original_prompt)
    behavior_result = behavior_analyzer.analyze_behavior(transcripts, date, use_original_prompt)
    
    return conflict_result, behavior_result


async def analyze_conflict_and_behavior_async(transcripts: List[dict], date: str, use_original_prompt: bool = False) -> tuple:
    """异步分析冲突和行为"""
    conflict_analyzer = ConflictAnalysis()
    behavior_analyzer = BehaviorAnalysis()
    
    # 并行执行
    conflict_task = conflict_analyzer.analyze_conflict_async(transcripts, date, use_original_prompt)
    behavior_task = behavior_analyzer.analyze_behavior_async(transcripts, date, use_original_prompt)
    
    conflict_result, behavior_result = await asyncio.gather(conflict_task, behavior_task)
    
    return conflict_result, behavior_result 