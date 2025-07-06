# -*- coding: utf-8 -*-
"""
重构后的脚本分析模块
主要用于协调各个算法模块，保留核心的数据处理和分析协调功能
"""

import os
import json
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# 导入新的模块
from .api_clients import api_client
from .parent_child_profiling import analyze_audio, analyze_audio_async
from .conflict_behavior_analysis import (
    analyze_conflict_and_behavior, 
    analyze_conflict_and_behavior_async
)
from .tx_deepseek import Scenery_rebuild, Knowledge_Base
from .prompt import (
    generate_user_profile_prompt, scene_construct, return_prompt,
    generate_family_overview, generate_conversation_analysis, 
    emotion_analysis, generate_reflection_questions, 
    conflict_analysis, behavior_analysis, strategy_generation,
    style_prompt, sentiment_prompt, patterns_prompt, topics_prompt, 
    conflict_prompt, advantage_prompt
)

logger = logging.getLogger(__name__)


# 数据处理函数
def read_json(file_path: str) -> Dict[str, Any]:
    """读取JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"读取JSON文件失败: {e}")
        return {}


def preprocess_data(data: List[Dict]) -> pd.DataFrame:
    """预处理数据"""
    try:
        # 转换为DataFrame
        df = pd.DataFrame(data)
        
        # 如果有时间列，转换为datetime
        if 'start_time' in df.columns:
            df['start_time'] = pd.to_datetime(df['start_time'])
        if 'end_time' in df.columns:
            df['end_time'] = pd.to_datetime(df['end_time'])
        
        return df
    except Exception as e:
        logger.error(f"预处理数据失败: {e}")
        return pd.DataFrame()


def segment_conversations(df: pd.DataFrame, gap_threshold: timedelta = timedelta(minutes=1.5)) -> List[pd.DataFrame]:
    """分段对话"""
    try:
        if df.empty or 'start_time' not in df.columns:
            return [df]
        
        segments = []
        current_segment = []
        
        for i, row in df.iterrows():
            if current_segment:
                # 计算与上一条记录的时间间隔
                time_gap = row['start_time'] - current_segment[-1]['start_time']
                if time_gap > gap_threshold:
                    # 时间间隔过大，开始新段
                    segments.append(pd.DataFrame(current_segment))
                    current_segment = [row]
                else:
                    current_segment.append(row)
            else:
                current_segment.append(row)
        
        # 添加最后一段
        if current_segment:
            segments.append(pd.DataFrame(current_segment))
        
        return segments
    except Exception as e:
        logger.error(f"分段对话失败: {e}")
        return [df]


def transform_conversation(conversation: List[Dict]) -> Dict[str, Any]:
    """转换对话格式"""
    try:
        transformed = {
            'total_turns': len(conversation),
            'speakers': list(set(item.get('speaker', 'unknown') for item in conversation)),
            'content': [item.get('content', '') for item in conversation],
            'duration': None
        }
        
        # 计算总时长
        if conversation and 'start_time' in conversation[0] and 'end_time' in conversation[-1]:
            start_time = pd.to_datetime(conversation[0]['start_time'])
            end_time = pd.to_datetime(conversation[-1]['end_time'])
            transformed['duration'] = (end_time - start_time).total_seconds()
        
        return transformed
    except Exception as e:
        logger.error(f"转换对话格式失败: {e}")
        return {'total_turns': 0, 'speakers': [], 'content': [], 'duration': None}


# 音频分析函数
def analyze_audio(transcript: List[Dict]) -> Tuple[Any, Any, Any, Any, Any, Any]:
    """分析音频转录文本 - 同步版本"""
    logger.info("开始音频分析")
    
    try:
        # 标准化数据格式
        data = [{'id': d['id'], 'speaker': d['speaker'], 'content': d['content']} for d in transcript]
        
        # 使用api_client进行分析
        from .api_clients import api_client
        
        # 并行分析各个方面
        result_style = api_client.chat_with_fallback(style_prompt, str(data))
        result_sentiment = api_client.chat_with_fallback(sentiment_prompt, str(data))
        result_patterns = api_client.chat_with_fallback(patterns_prompt, str(data))
        result_topics = api_client.chat_with_fallback(topics_prompt, str(data))
        result_conflict = api_client.chat_with_fallback(conflict_prompt, str(data))
        result_advantage = api_client.chat_with_fallback(advantage_prompt, str(data))
        
        logger.info("音频分析完成")
        return result_style, result_sentiment, result_patterns, result_topics, result_conflict, result_advantage
        
    except Exception as e:
        logger.error(f"音频分析失败: {e}")
        return None, None, None, None, None, None


async def analyze_audio_async(transcript: List[Dict]) -> Tuple[Any, Any, Any, Any, Any, Any]:
    """分析音频转录文本 - 异步版本"""
    logger.info("开始异步音频分析")
    
    try:
        # 标准化数据格式
        data = [{'id': d['id'], 'speaker': d['speaker'], 'content': d['content']} for d in transcript]
        
        # 使用api_client进行异步分析
        from .api_clients import api_client
        
        # 并行分析各个方面
        tasks = [
            api_client.chat_with_fallback_async(style_prompt, str(data)),
            api_client.chat_with_fallback_async(sentiment_prompt, str(data)),
            api_client.chat_with_fallback_async(patterns_prompt, str(data)),
            api_client.chat_with_fallback_async(topics_prompt, str(data)),
            api_client.chat_with_fallback_async(conflict_prompt, str(data)),
            api_client.chat_with_fallback_async(advantage_prompt, str(data))
        ]
        
        results = await asyncio.gather(*tasks)
        result_style, result_sentiment, result_patterns, result_topics, result_conflict, result_advantage = results
        
        logger.info("异步音频分析完成")
        return result_style, result_sentiment, result_patterns, result_topics, result_conflict, result_advantage
        
    except Exception as e:
        logger.error(f"异步音频分析失败: {e}")
        return None, None, None, None, None, None


# 主要的分析协调函数
def analyze_complete_transcript(transcript: List[Dict], date: str = None) -> Dict[str, Any]:
    """完整的转录分析"""
    logger.info("开始完整的转录分析")
    
    if not date:
        date = datetime.now().strftime('%Y%m%d')
    
    try:
        # 1. 亲子画像分析
        logger.info("开始亲子画像分析")
        style, sentiment, patterns, topics, conflicts, advantages = analyze_audio(transcript)
        
        # 2. 冲突行为分析
        logger.info("开始冲突行为分析")
        conflict_result, behavior_result = analyze_conflict_and_behavior(transcript, date)
        
        # 3. 场景重建
        logger.info("开始场景重建")
        scenery_result = perform_scenery_rebuild(transcript)
        
        # 4. 知识库检索
        logger.info("开始知识库检索")
        knowledge_result = perform_knowledge_retrieval(transcript)
        
        # 5. 干预策略生成
        logger.info("开始干预策略生成")
        intervention_result = generate_intervention_strategy(transcript, knowledge_result)
        
        # 整合结果
        result = {
            'analysis_date': date,
            'parent_child_profile': {
                'parenting_style': style,
                'sentiment_analysis': sentiment,
                'communication_patterns': patterns,
                'topic_analysis': topics,
                'conflict_analysis': conflicts,
                'advantage_analysis': advantages
            },
            'conflict_behavior': {
                'conflict_scenes': conflict_result,
                'behavior_scenes': behavior_result
            },
            'scenery_rebuild': scenery_result,
            'knowledge_retrieval': knowledge_result,
            'intervention_strategy': intervention_result
        }
        
        logger.info("完整的转录分析完成")
        return result

    except Exception as e:
        logger.error(f"完整转录分析失败: {e}")
        return {'error': str(e)}


async def analyze_complete_transcript_async(transcript: List[Dict], date: str = None) -> Dict[str, Any]:
    """异步完整的转录分析"""
    logger.info("开始异步完整的转录分析")
    
    if not date:
        date = datetime.now().strftime('%Y%m%d')
    
    try:
        # 并行执行各个分析任务
        tasks = [
            # 亲子画像分析
            analyze_audio_async(transcript),
            # 冲突行为分析
            analyze_conflict_and_behavior_async(transcript, date),
            # 场景重建
            perform_scenery_rebuild_async(transcript),
            # 知识库检索
            perform_knowledge_retrieval_async(transcript)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 解析结果
        profile_result = results[0]
        conflict_behavior_result = results[1]
        scenery_result = results[2]
        knowledge_result = results[3]
        
        # 生成干预策略
        intervention_result = await generate_intervention_strategy_async(transcript, knowledge_result)
        
        # 整合结果
        result = {
            'analysis_date': date,
            'parent_child_profile': {
                'parenting_style': profile_result[0],
                'sentiment_analysis': profile_result[1],
                'communication_patterns': profile_result[2],
                'topic_analysis': profile_result[3],
                'conflict_analysis': profile_result[4],
                'advantage_analysis': profile_result[5]
            },
            'conflict_behavior': {
                'conflict_scenes': conflict_behavior_result[0],
                'behavior_scenes': conflict_behavior_result[1]
            },
            'scenery_rebuild': scenery_result,
            'knowledge_retrieval': knowledge_result,
            'intervention_strategy': intervention_result
        }
        
        logger.info("异步完整的转录分析完成")
        return result
    except Exception as e:
        logger.error(f"异步完整转录分析失败: {e}")
        return {'error': str(e)}


# 场景重建函数
def perform_scenery_rebuild(transcript: List[Dict]) -> Dict[str, Any]:
    """执行场景重建"""
    logger.info("开始场景重建")
    
    try:
        # 使用tx_deepseek模块进行场景重建
        scenery_rebuilder = Scenery_rebuild()
        
        # 将transcript转换为适合的格式
        formatted_transcript = [
            {
                'speaker': item.get('speaker', 'unknown'),
                'content': item.get('content', ''),
                'timestamp': item.get('start_time', '')
            }
            for item in transcript
        ]
        
        # 执行场景重建
        result = scenery_rebuilder.rebuild_scene(formatted_transcript)
        
        logger.info("场景重建完成")
        return result
        
    except Exception as e:
        logger.error(f"场景重建失败: {e}")
        return {'error': str(e)}


async def perform_scenery_rebuild_async(transcript: List[Dict]) -> Dict[str, Any]:
    """异步执行场景重建"""
    logger.info("开始异步场景重建")
    
    try:
        # 在线程池中执行场景重建
        result = await asyncio.get_event_loop().run_in_executor(
            None, 
            perform_scenery_rebuild, 
            transcript
        )
        
        logger.info("异步场景重建完成")
        return result
        
    except Exception as e:
        logger.error(f"异步场景重建失败: {e}")
        return {'error': str(e)}


# 知识库检索函数
def perform_knowledge_retrieval(transcript: List[Dict]) -> Dict[str, Any]:
    """执行知识库检索"""
    logger.info("开始知识库检索")
    
    try:
        # 使用tx_deepseek模块进行知识库检索
        knowledge_base = Knowledge_Base()
        
        # 提取查询文本
        query_text = ' '.join([item.get('content', '') for item in transcript])
        
        # 执行知识库检索
        result = knowledge_base.search_knowledge(query_text)
        
        logger.info("知识库检索完成")
        return result
        
    except Exception as e:
        logger.error(f"知识库检索失败: {e}")
        return {'error': str(e)}


async def perform_knowledge_retrieval_async(transcript: List[Dict]) -> Dict[str, Any]:
    """异步执行知识库检索"""
    logger.info("开始异步知识库检索")
    
    try:
        # 在线程池中执行知识库检索
        result = await asyncio.get_event_loop().run_in_executor(
            None, 
            perform_knowledge_retrieval, 
            transcript
        )
        
        logger.info("异步知识库检索完成")
        return result
        
    except Exception as e:
        logger.error(f"异步知识库检索失败: {e}")
        return {'error': str(e)}


# 干预策略生成函数
def generate_intervention_strategy(transcript: List[Dict], docs: Dict[str, Any] = None) -> Dict[str, Any]:
    """生成干预策略 - 返回7个分析结果"""
    logger.info("开始生成干预策略")
    
    try:
        # 1. 获取基础分析结果
        logger.info("开始基础分析")
        result_style, result_sentiment, result_patterns, result_topics, result_conflict, result_advantage = analyze_audio(transcript)
        
        # 2. 场景重建
        logger.info("开始场景重建")
        scenery_result = perform_scenery_rebuild(transcript)
        
        # 3. 知识库检索（如果没有提供docs）
        if docs is None:
            logger.info("开始知识库检索")
            docs = perform_knowledge_retrieval(transcript)
        
        # 4. 使用场景重建结果进行知识库查询
        logger.info("处理知识库结果")
        knowledge = Knowledge_Base(docs=docs, input_data=scenery_result, index_folder_path='./checkpoints/index')
        a1, a2, a3, a4, a5 = knowledge.result()
        
        # 5. 生成7个分析结果
        logger.info("开始生成7个分析结果")
        
        # 使用api_client进行调用
        from .api_clients import api_client
        
        # 家庭概览
        family_overview_prompt = generate_family_overview(result_style, result_patterns, result_advantage)
        family_overview = api_client.chat_with_fallback("", family_overview_prompt)
        
        # 对话分析
        conversation_analysis_prompt = generate_conversation_analysis(a3, a4)
        conversation_analysis = api_client.chat_with_fallback("", conversation_analysis_prompt)
        
        # 情绪分析
        emotion_analysis_prompt = emotion_analysis(result_sentiment)
        emotion_analysis_result = api_client.chat_with_fallback("", emotion_analysis_prompt)
        
        # 反思问题
        reflection_questions_prompt = generate_reflection_questions(a5)
        reflection_questions = api_client.chat_with_fallback("", reflection_questions_prompt)
        
        # 冲突分析
        conflict_analysis_prompt = conflict_analysis(result_conflict)
        conflict_analysis_result = api_client.chat_with_fallback("", conflict_analysis_prompt)
        
        # 行为分析
        behavior_analysis_prompt = behavior_analysis(result_conflict, scenery_result)
        behavior_analysis_result = api_client.chat_with_fallback("", behavior_analysis_prompt)
        
        # 策略生成
        strategy_generation_prompt = strategy_generation(result_sentiment, a1, a2)
        strategy_generation_result = api_client.chat_with_fallback("", strategy_generation_prompt)
        
        # 构建返回结果
        result = {
            'family_overview': family_overview,
            'conversation_analysis': conversation_analysis,
            'emotion_analysis': emotion_analysis_result,
            'reflection_questions': reflection_questions,
            'conflict_analysis': conflict_analysis_result,
            'behavior_analysis': behavior_analysis_result,
            'strategy_generation': strategy_generation_result
        }
        
        logger.info("干预策略生成完成")
        return result
        
    except Exception as e:
        logger.error(f"干预策略生成失败: {e}")
        return {
            'family_overview': f"生成失败: {str(e)}",
            'conversation_analysis': f"生成失败: {str(e)}",
            'emotion_analysis': f"生成失败: {str(e)}",
            'reflection_questions': f"生成失败: {str(e)}",
            'conflict_analysis': f"生成失败: {str(e)}",
            'behavior_analysis': f"生成失败: {str(e)}",
            'strategy_generation': f"生成失败: {str(e)}"
        }


async def generate_intervention_strategy_async(transcript: List[Dict], docs: Dict[str, Any] = None) -> Dict[str, Any]:
    """异步生成干预策略 - 返回7个分析结果"""
    logger.info("开始异步生成干预策略")
    
    try:
        # 1. 获取基础分析结果
        logger.info("开始基础分析")
        result_style, result_sentiment, result_patterns, result_topics, result_conflict, result_advantage = await analyze_audio_async(transcript)
        
        # 2. 场景重建
        logger.info("开始场景重建")
        scenery_result = await perform_scenery_rebuild_async(transcript)
        
        # 3. 知识库检索（如果没有提供docs）
        if docs is None:
            logger.info("开始知识库检索")
            docs = await perform_knowledge_retrieval_async(transcript)
        
        # 4. 使用场景重建结果进行知识库查询
        logger.info("处理知识库结果")
        knowledge = Knowledge_Base(docs=docs, input_data=scenery_result, index_folder_path='./checkpoints/index')
        a1, a2, a3, a4, a5 = await asyncio.to_thread(knowledge.result)
        
        # 5. 并行生成7个分析结果
        logger.info("开始并行生成7个分析结果")
        
        # 使用api_client进行异步调用
        from .api_clients import api_client
        
        tasks = []
        
        # 家庭概览
        family_overview_prompt = generate_family_overview(result_style, result_patterns, result_advantage)
        tasks.append(api_client.chat_with_fallback_async("", family_overview_prompt))
        
        # 对话分析
        conversation_analysis_prompt = generate_conversation_analysis(a3, a4)
        tasks.append(api_client.chat_with_fallback_async("", conversation_analysis_prompt))
        
        # 情绪分析
        emotion_analysis_prompt = emotion_analysis(result_sentiment)
        tasks.append(api_client.chat_with_fallback_async("", emotion_analysis_prompt))
        
        # 反思问题
        reflection_questions_prompt = generate_reflection_questions(a5)
        tasks.append(api_client.chat_with_fallback_async("", reflection_questions_prompt))
        
        # 冲突分析
        conflict_analysis_prompt = conflict_analysis(result_conflict)
        tasks.append(api_client.chat_with_fallback_async("", conflict_analysis_prompt))
        
        # 行为分析
        behavior_analysis_prompt = behavior_analysis(result_conflict, scenery_result)
        tasks.append(api_client.chat_with_fallback_async("", behavior_analysis_prompt))
        
        # 策略生成
        strategy_generation_prompt = strategy_generation(result_sentiment, a1, a2)
        tasks.append(api_client.chat_with_fallback_async("", strategy_generation_prompt))
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        
        # 构建返回结果
        result = {
            'family_overview': results[0],
            'conversation_analysis': results[1],
            'emotion_analysis': results[2],
            'reflection_questions': results[3],
            'conflict_analysis': results[4],
            'behavior_analysis': results[5],
            'strategy_generation': results[6]
        }
        
        logger.info("异步干预策略生成完成")
        return result
        
    except Exception as e:
        logger.error(f"异步干预策略生成失败: {e}")
        return {
            'family_overview': f"生成失败: {str(e)}",
            'conversation_analysis': f"生成失败: {str(e)}",
            'emotion_analysis': f"生成失败: {str(e)}",
            'reflection_questions': f"生成失败: {str(e)}",
            'conflict_analysis': f"生成失败: {str(e)}",
            'behavior_analysis': f"生成失败: {str(e)}",
            'strategy_generation': f"生成失败: {str(e)}"
        }


# 兼容性函数 - 保持向后兼容
def transcribe_audio(file_path: str) -> Dict[str, Any]:
    """转录音频文件 - 兼容性函数"""
    logger.info(f"转录音频文件: {file_path}")
    
    try:
        # 调用request_api中的转录功能
        from .request_api import transcribe_audio as transcribe_func
        return transcribe_func(file_path)
    except Exception as e:
        logger.error(f"转录音频失败: {e}")
        return {'error': str(e)}


async def transcribe_audio_async(file_path: str) -> Dict[str, Any]:
    """异步转录音频文件 - 兼容性函数"""
    logger.info(f"异步转录音频文件: {file_path}")
    
    try:
        # 在线程池中执行转录
        result = await asyncio.get_event_loop().run_in_executor(
            None, 
            transcribe_audio, 
            file_path
        )
        
        logger.info("异步音频转录完成")
        return result
        
    except Exception as e:
        logger.error(f"异步转录音频失败: {e}")
        return {'error': str(e)}


# 主函数入口
def main():
    """主函数"""
    logger.info("脚本分析模块已重构完成")
    
    # 示例使用
    sample_transcript = [
        {
            'id': 0,
            'speaker': 'parent',
            'start_time': '00:00:00.000',
            'end_time': '00:00:05.000',
            'content': '你今天作业做完了吗？'
        },
        {
            'id': 1,
            'speaker': 'child',
            'start_time': '00:00:05.500',
            'end_time': '00:00:10.000',
            'content': '还没有，我想先玩一会儿游戏。'
        }
    ]
    
    # 执行分析
    result = analyze_complete_transcript(sample_transcript)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main() 