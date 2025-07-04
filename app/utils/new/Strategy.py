# -*- coding: utf-8 -*-
import asyncio
import logging
from typing import List, Dict, Any, Optional

# API 和 Prompt 导入
from .api import call_llm_async
# 假设这些 Prompt 生成函数已在 prompt.py 定义
try:
    from .prompt import (
        generate_family_overview, generate_conversation_analysis, 
        emotion_analysis, generate_reflection_questions, 
        conflict_analysis, behavior_analysis, strategy_generation
    )
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("无法从 prompt.py 导入策略生成 Prompts，请确保文件存在且包含所需函数。将使用占位符。")
    # 定义占位符函数或引发错误，这里使用简单返回 None
    def generate_family_overview(*args): return None
    def generate_conversation_analysis(*args): return None
    def emotion_analysis(*args): return None
    def generate_reflection_questions(*args): return None
    def conflict_analysis(*args): return None
    def behavior_analysis(*args): return None
    def strategy_generation(*args): return None

logger = logging.getLogger(__name__)

async def generate_intervention_strategy_async(
    processed_transcript: List[Dict[str, Any]], # 原始转录可能仍需要
    profile_results: Optional[Dict[str, Any]] = None, # 来自 role_model.py 的分析结果
    rag_results: Optional[Dict[str, Any]] = None, # 来自 RAG.py 的结果 (a1-a5)
    scenarios: Optional[List[Dict[str, Any]]] = None # 来自 Scenery.py 的结果
) -> Dict[str, Optional[str]]:
    """
    异步生成干预策略的各个部分。

    Args:
        processed_transcript: 标准化后的转录列表。
        profile_results: 包含亲子画像分析结果的字典，例如:
            {'conflict': ConflictAnalysisOutput, 'behavior': BehaviorAnalysisOutput, 
             'style': ..., 'sentiment': ..., 'patterns': ..., 'topics': ..., 
             'advantage': ..., 'user_profile': ...}
        rag_results: 包含 RAG 检索和生成结果的字典，例如:
            {'a1': ..., 'a2': ..., 'a3': ..., 'a4': ..., 'a5': ...}
        scenarios: 包含场景重建结果的列表。

    Returns:
        一个字典，包含生成报告所需的各个部分文本，键名对应 AnalysisResult 模型字段。
        如果某个部分生成失败，对应的值可能为 None。
    """
    logger.info("开始生成干预策略...")
    
    # --- 数据准备 --- 
    # 从输入字典中安全地提取所需数据，提供默认值以防 None
    profile_results = profile_results or {}
    rag_results = rag_results or {}
    scenarios = scenarios or []

    # 从 profile_results 提取 (需要确认 role_model.py 最终输出的结构)
    # 这里假设 profile_results 包含所有需要的键，实际可能需要调整
    result_style = profile_results.get('style')
    result_patterns = profile_results.get('patterns')
    result_advantage = profile_results.get('advantage')
    user_profile = profile_results.get('user_profile') # 这本身可能是LLM生成的
    result_sentiment = profile_results.get('sentiment')
    result_conflict = profile_results.get('conflict') # 这是 Pydantic 对象
    # 注意：behavior_analysis prompt 需要 conflict 和 scenarios
    
    # 从 rag_results 提取
    a1 = rag_results.get('a1')
    a2 = rag_results.get('a2')
    a3 = rag_results.get('a3')
    a4 = rag_results.get('a4')
    a5 = rag_results.get('a5')
    
    # --- 构建并行任务列表 --- 
    tasks = []
    task_map = {}

    # 任务 1: 家庭概览 (family_overview)
    try:
        family_overview_prompt_str = generate_family_overview(result_style, result_patterns, result_advantage, user_profile)
        if family_overview_prompt_str:
             tasks.append(call_llm_async(
                 client_type='zhizengzeng', model='deepseek-chat',
                 messages=[{"role": "user", "content": family_overview_prompt_str}]
             ))
             task_map[len(tasks)-1] = 'family_overview'
        else:
             logger.warning("家庭概览 prompt 生成失败或为空，跳过此部分。")
    except Exception as e:
         logger.error(f"准备家庭概览任务时出错: {e}", exc_info=True)

    # 任务 2: 对话分析 (conversation_analysis)
    try:
        convo_analysis_prompt_str = generate_conversation_analysis(a3, a4)
        if convo_analysis_prompt_str:
            tasks.append(call_llm_async(
                client_type='zhizengzeng', model='deepseek-chat',
                messages=[{"role": "user", "content": convo_analysis_prompt_str}]
            ))
            task_map[len(tasks)-1] = 'conversation_analysis'
        else:
            logger.warning("对话分析 prompt 生成失败或为空，跳过此部分。")
    except Exception as e:
         logger.error(f"准备对话分析任务时出错: {e}", exc_info=True)

    # 任务 3: 情绪分析 (emotion_analysis_result)
    try:
        emotion_analysis_prompt_str = emotion_analysis(result_sentiment)
        if emotion_analysis_prompt_str:
            tasks.append(call_llm_async(
                client_type='zhizengzeng', model='deepseek-chat',
                messages=[{"role": "user", "content": emotion_analysis_prompt_str}]
            ))
            task_map[len(tasks)-1] = 'emotion_analysis_result'
        else:
             logger.warning("情绪分析 prompt 生成失败或为空，跳过此部分。")
    except Exception as e:
         logger.error(f"准备情绪分析任务时出错: {e}", exc_info=True)

    # 任务 4: 反思问题 (reflection_questions)
    try:
        reflection_prompt_str = generate_reflection_questions(a5)
        if reflection_prompt_str:
            tasks.append(call_llm_async(
                client_type='zhizengzeng', model='deepseek-chat',
                messages=[{"role": "user", "content": reflection_prompt_str}]
            ))
            task_map[len(tasks)-1] = 'reflection_questions'
        else:
             logger.warning("反思问题 prompt 生成失败或为空，跳过此部分。")
    except Exception as e:
         logger.error(f"准备反思问题任务时出错: {e}", exc_info=True)

    # 任务 5: 冲突分析总结 (conflict_analysis_result) 
    # 注意：这里的 conflict_analysis 是生成报告文本，不是提取冲突
    try:
        # conflict_analysis prompt 可能需要 Pydantic 对象 result_conflict
        conflict_summary_prompt_str = conflict_analysis(result_conflict)
        if conflict_summary_prompt_str:
            tasks.append(call_llm_async(
                client_type='zhizengzeng', model='deepseek-chat',
                messages=[{"role": "user", "content": conflict_summary_prompt_str}]
            ))
            task_map[len(tasks)-1] = 'conflict_analysis_result'
        else:
             logger.warning("冲突分析总结 prompt 生成失败或为空，跳过此部分。")
    except Exception as e:
         logger.error(f"准备冲突分析总结任务时出错: {e}", exc_info=True)

    # 任务 6: 行为分析总结 (behavior_analysis_result)
    # 注意：这里的 behavior_analysis 是生成报告文本，不是提取行为
    try:
        # behavior_analysis prompt 可能需要 result_conflict 和 scenarios
        behavior_summary_prompt_str = behavior_analysis(result_conflict, scenarios)
        if behavior_summary_prompt_str:
            tasks.append(call_llm_async(
                client_type='zhizengzeng', model='deepseek-chat',
                messages=[{"role": "user", "content": behavior_summary_prompt_str}]
            ))
            task_map[len(tasks)-1] = 'behavior_analysis_result'
        else:
             logger.warning("行为分析总结 prompt 生成失败或为空，跳过此部分。")
    except Exception as e:
         logger.error(f"准备行为分析总结任务时出错: {e}", exc_info=True)

    # 任务 7: 策略建议 (strategy_generation_result)
    try:
        # strategy_generation 可能需要 result_sentiment, a1, a2
        strategy_prompt_str = strategy_generation(result_sentiment, a1, a2)
        if strategy_prompt_str:
            tasks.append(call_llm_async(
                client_type='zhizengzeng', model='deepseek-chat',
                messages=[{"role": "user", "content": strategy_prompt_str}]
            ))
            task_map[len(tasks)-1] = 'strategy_generation_result'
        else:
             logger.warning("策略建议 prompt 生成失败或为空，跳过此部分。")
    except Exception as e:
         logger.error(f"准备策略建议任务时出错: {e}", exc_info=True)
    
    # --- 执行任务并收集结果 --- 
    results = {} # 用于存储最终结果的字典
    if tasks:
        logger.info(f"开始并行执行 {len(tasks)} 个策略生成子任务...")
        llm_results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("所有策略生成子任务已完成.")
        
        # 收集结果，处理异常
        for i, result in enumerate(llm_results):
            task_name = task_map.get(i)
            if task_name:
                if isinstance(result, Exception):
                    logger.error(f"生成策略部分 '{task_name}' 时失败: {result}")
                    results[task_name] = None # 或者记录错误信息
                elif result is None:
                     logger.warning(f"生成策略部分 '{task_name}' 返回 None")
                     results[task_name] = None
                else:
                    results[task_name] = str(result) # 确保存储为字符串
            else:
                 logger.error(f"无法找到索引 {i} 对应的任务名称")
    else:
        logger.warning("没有可执行的策略生成子任务。")

    # 确保所有 AnalysisResult 模型的字段都有一个值 (即使是 None)
    final_strategy_parts = {
        'family_overview': results.get('family_overview'),
        'conversation_analysis': results.get('conversation_analysis'),
        'emotion_analysis_result': results.get('emotion_analysis_result'),
        'reflection_questions': results.get('reflection_questions'),
        'conflict_analysis_result': results.get('conflict_analysis_result'),
        'behavior_analysis_result': results.get('behavior_analysis_result'),
        'strategy_generation_result': results.get('strategy_generation_result')
    }

    logger.info("干预策略生成流程结束.")
    return final_strategy_parts 