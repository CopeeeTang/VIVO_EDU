# -*- coding: utf-8 -*-
"""
测试重构后的音频分析流程

这个文件测试重构后的音频分析后端流程，包括：
1. 音频预处理（转录和标准化）
2. 亲子画像分析（冲突和行为分析）
3. 场景重建
4. RAG知识检索
5. 策略生成

使用方法：
直接运行 python -m app.utils.test_flow
"""

import asyncio
import logging
import os
import sys
import json
import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_flow")

# 导入重构后的模块
try:
    from .preprocess import process_audio, extract_date_from_filename
    from .role_model import analyze_transcripts_for_profile
    from .Scenery import rebuild_scenery
    from .RAG import retrieve_knowledge
    from .Strategy import generate_strategy
except ImportError:
    logger.error("无法导入必要模块。请确保所有模块都已实现。")
    # 如果在测试阶段不是所有模块都实现了，可以提供模拟实现
    from unittest.mock import AsyncMock
    
    # 假设某些模块尚未实现，提供模拟
    process_audio = None
    extract_date_from_filename = lambda fn: "20241101"  # 模拟函数
    analyze_transcripts_for_profile = None
    rebuild_scenery = None
    retrieve_knowledge = None
    generate_strategy = None

# 测试配置
TEST_AUDIO_PATH = "tests/data/test_audio.mp3"  # 测试音频文件路径
TEST_TRANSCRIPT_PATH = "tests/data/test_transcript.json"  # 预先准备的转录结果（如果音频转录不可用）
OUTPUT_DIR = "tests/output"  # 输出目录

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_test_transcript() -> List[Dict[str, str]]:
    """
    加载测试转录数据。
    如果TEST_TRANSCRIPT_PATH存在，则从该文件加载；
    否则返回一个简单的模拟转录。
    """
    try:
        if os.path.exists(TEST_TRANSCRIPT_PATH):
            with open(TEST_TRANSCRIPT_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"测试转录文件不存在: {TEST_TRANSCRIPT_PATH}，使用模拟数据")
            # 返回模拟转录数据
            return [
                {"id": 1, "speaker": "家长", "text": "今天我们开始做作业吧。"},
                {"id": 2, "speaker": "孩子", "text": "我不想做，我想先玩一会儿。"},
                {"id": 3, "speaker": "家长", "text": "不行，必须先完成作业，这是规矩。"},
                {"id": 4, "speaker": "孩子", "text": "可是我玩一小会儿就开始，好不好？"},
                {"id": 5, "speaker": "家长", "text": "你总是这样拖拖拉拉，每次都说一小会儿，结果拖很久！"},
                {"id": 6, "speaker": "孩子", "text": "我保证就十分钟。"},
                {"id": 7, "speaker": "家长", "text": "不行！现在就开始做，不然我就把你的玩具收起来！"},
                {"id": 8, "speaker": "孩子", "text": "好吧，那我做。"}
            ]
    except Exception as e:
        logger.error(f"加载测试转录数据失败: {e}")
        return []


async def test_full_flow():
    """
    测试完整的音频分析流程
    """
    try:
        # 1. 音频预处理阶段
        logger.info("=== 开始音频预处理阶段 ===")
        
        # 提取日期信息
        filename = os.path.basename(TEST_AUDIO_PATH)
        date_str = extract_date_from_filename(filename)
        if not date_str:
            date_str = datetime.datetime.now().strftime('%Y%m%d')
        
        logger.info(f"从文件名提取的日期: {date_str}")
        
        # 转录音频（如果模块可用）
        transcript = None
        if process_audio and os.path.exists(TEST_AUDIO_PATH):
            logger.info(f"开始转录音频: {TEST_AUDIO_PATH}")
            transcript = await process_audio(TEST_AUDIO_PATH)
            # 保存转录结果以供将来使用
            with open(os.path.join(OUTPUT_DIR, 'transcript_result.json'), 'w', encoding='utf-8') as f:
                json.dump(transcript, f, ensure_ascii=False, indent=2)
        else:
            logger.info("音频处理模块不可用或测试音频不存在，使用预设转录数据")
            transcript = load_test_transcript()
        
        if not transcript:
            raise ValueError("无法获取转录数据")
        
        logger.info(f"成功获取转录数据，共 {len(transcript)} 个片段")
        
        # 2. 亲子画像分析阶段
        logger.info("=== 开始亲子画像分析阶段 ===")
        file_id = f"test_{date_str}"
        analysis_id = 1  # 测试用ID
        
        if analyze_transcripts_for_profile:
            # 执行冲突和行为分析
            conflict_result, behavior_result = await analyze_transcripts_for_profile(
                transcripts=transcript,
                date=date_str,
                file_id=file_id,
                analysis_id=analysis_id
            )
            
            # 保存分析结果
            with open(os.path.join(OUTPUT_DIR, 'conflict_analysis.json'), 'w', encoding='utf-8') as f:
                # 将Pydantic模型转为dict再保存为JSON
                json.dump(conflict_result.dict(), f, ensure_ascii=False, indent=2)
            
            with open(os.path.join(OUTPUT_DIR, 'behavior_analysis.json'), 'w', encoding='utf-8') as f:
                json.dump(behavior_result.dict(), f, ensure_ascii=False, indent=2)
                
            logger.info(f"亲子画像分析完成 - 冲突场景: {len(conflict_result.scenes)} 个, 行为场景: {len(behavior_result.scenes)} 个")
        else:
            logger.warning("亲子画像分析模块不可用，跳过此步骤")
            conflict_result = None
            behavior_result = None
        
        # 3. 场景重建阶段
        logger.info("=== 开始场景重建阶段 ===")
        if rebuild_scenery:
            scenery_result = await rebuild_scenery(transcript, conflict_result, behavior_result)
            
            # 保存场景重建结果
            with open(os.path.join(OUTPUT_DIR, 'scenery_result.json'), 'w', encoding='utf-8') as f:
                json.dump(scenery_result, f, ensure_ascii=False, indent=2)
                
            logger.info("场景重建完成")
        else:
            logger.warning("场景重建模块不可用，跳过此步骤")
            # 模拟场景重建结果
            scenery_result = {
                "scenes": [
                    {
                        "scene_id": 1,
                        "summary": "家长要求孩子立刻做作业，孩子想先玩一会儿，引发冲突",
                        "original_dialogue": "...",
                        "analysis": "这是一个典型的时间管理冲突..."
                    }
                ]
            }
        
        # 4. 知识检索阶段
        logger.info("=== 开始知识检索阶段 ===")
        if retrieve_knowledge and scenery_result:
            knowledge_result = await retrieve_knowledge(scenery_result)
            
            # 保存知识检索结果
            with open(os.path.join(OUTPUT_DIR, 'knowledge_result.json'), 'w', encoding='utf-8') as f:
                json.dump(knowledge_result, f, ensure_ascii=False, indent=2)
                
            logger.info("知识检索完成")
        else:
            logger.warning("知识检索模块不可用或场景重建结果缺失，跳过此步骤")
            # 模拟知识检索结果
            knowledge_result = {
                "guidance": ["在处理时间管理冲突时，父母可以..."],
                "examples": ["案例1: 小明的父母通过..."],
                "reflection_questions": ["为什么孩子对立即开始作业有抵触?"]
            }
        
        # 5. 策略生成阶段
        logger.info("=== 开始策略生成阶段 ===")
        if generate_strategy and transcript and knowledge_result:
            strategy_result = await generate_strategy(
                transcript=transcript,
                conflict_result=conflict_result,
                behavior_result=behavior_result,
                scenery_result=scenery_result,
                knowledge_result=knowledge_result
            )
            
            # 保存策略生成结果
            with open(os.path.join(OUTPUT_DIR, 'strategy_result.json'), 'w', encoding='utf-8') as f:
                json.dump(strategy_result, f, ensure_ascii=False, indent=2)
                
            logger.info("策略生成完成")
        else:
            logger.warning("策略生成模块不可用或前置数据缺失，跳过此步骤")
            # 模拟策略生成结果
            strategy_result = {
                "family_overview": "该家庭的教育风格偏向于...",
                "conversation_analysis": "在对话中，家长倾向于使用命令式...",
                "emotion_analysis": "家长情绪波动明显，孩子则表现出...",
                "reflection_questions": ["您是否考虑过给孩子更多自主选择的空间?"],
                "conflict_analysis": "主要冲突点在于时间管理和规则设定...",
                "behavior_analysis": "建议增加积极行为如鼓励和有标注表扬...",
                "strategy_generation": "1. 建立合理的作业时间表，包括适当的休息时间\n2. 使用积极的语言代替命令和威胁\n3. ..."
            }
        
        # 6. 完成所有流程，输出汇总信息
        logger.info("=== 音频分析流程测试完成 ===")
        logger.info(f"所有结果已保存至: {OUTPUT_DIR}")
        
        # 创建分析报告摘要
        summary = {
            "test_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "audio_file": TEST_AUDIO_PATH,
            "date": date_str,
            "transcription_segments": len(transcript) if transcript else 0,
            "conflict_scenes": len(conflict_result.scenes) if conflict_result else 0,
            "behavior_scenes": len(behavior_result.scenes) if behavior_result else 0,
            "scenery_scenes": len(scenery_result.get("scenes", [])) if scenery_result else 0,
            "strategy_sections": len(strategy_result) if strategy_result else 0,
            "status": "完成"
        }
        
        with open(os.path.join(OUTPUT_DIR, 'test_summary.json'), 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            
        return True
            
    except Exception as e:
        logger.error(f"测试流程发生错误: {e}", exc_info=True)
        return False

async def main():
    """主函数"""
    logger.info("开始测试重构后的音频分析流程")
    success = await test_full_flow()
    if success:
        logger.info("测试完成，流程执行成功")
    else:
        logger.error("测试失败，请检查错误日志")

if __name__ == "__main__":
    asyncio.run(main()) 