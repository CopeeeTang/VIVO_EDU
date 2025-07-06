# -*- coding: utf-8 -*-
"""
亲子画像模块
包含教养方式、情感变化、对话模式、主题分析、冲突分析、优势劣势分析等功能
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from .api_clients import api_client, chat_with_fallback, chat_with_fallback_async
from .prompt import style_prompt, sentiment_prompt, patterns_prompt, topics_prompt, conflict_prompt, advantage_prompt

logger = logging.getLogger(__name__)


class ParentChildProfiler:
    """亲子画像分析器"""
    
    def __init__(self):
        self.api_client = api_client
    
    def analyze_parenting_style(self, transcript: List[Dict]) -> Dict[str, Any]:
        """分析教养方式"""
        logger.info("开始分析教养方式")
        try:
            data = [{'id': d['id'], 'speaker': d['speaker'], 'content': d['content']} for d in transcript]
            
            # 使用回退策略调用API
            try:
                result = chat_with_fallback(style_prompt, f"Transcripts of conversations: \n{str(data)}")
                
                logger.info("教养方式分析完成")
                return self._parse_analysis_result(result)
            except Exception as e:
                logger.error(f"分析教养方式时发生错误: {e}")
                return {"error": str(e)}
        except Exception as e:
            logger.error(f"教养方式分析失败: {e}")
            return {"error": str(e)}
    
    def analyze_sentiment(self, transcript: List[Dict]) -> Dict[str, Any]:
        """分析情感变化"""
        logger.info("开始分析情感变化")
        try:
            data = [{'id': d['id'], 'speaker': d['speaker'], 'content': d['content']} for d in transcript]
            
            try:
                result = chat_with_fallback(sentiment_prompt, f"Transcripts of conversations: \n{str(data)}")
                
                logger.info("情感变化分析完成")
                return self._parse_analysis_result(result)
            except Exception as e:
                logger.error(f"分析情感变化时发生错误: {e}")
                return {"error": str(e)}
        except Exception as e:
            logger.error(f"情感变化分析失败: {e}")
            return {"error": str(e)}
    
    def analyze_communication_patterns(self, transcript: List[Dict]) -> Dict[str, Any]:
        """分析对话模式"""
        logger.info("开始分析对话模式")
        try:
            data = [{'id': d['id'], 'speaker': d['speaker'], 'content': d['content']} for d in transcript]
            
            try:
                result = chat_with_fallback(patterns_prompt, f"Transcripts of conversations: \n{str(data)}")
                
                logger.info("对话模式分析完成")
                return self._parse_analysis_result(result)
            except Exception as e:
                logger.error(f"分析对话模式时发生错误: {e}")
                return {"error": str(e)}
        except Exception as e:
            logger.error(f"对话模式分析失败: {e}")
            return {"error": str(e)}
    
    def analyze_topics(self, transcript: List[Dict]) -> Dict[str, Any]:
        """分析主题"""
        logger.info("开始分析主题")
        try:
            data = [{'id': d['id'], 'speaker': d['speaker'], 'content': d['content']} for d in transcript]
            
            try:
                result = chat_with_fallback(topics_prompt, f"Transcripts of conversations: \n{str(data)}")
                
                logger.info("主题分析完成")
                return self._parse_analysis_result(result)
            except Exception as e:
                logger.error(f"分析主题时发生错误: {e}")
                return {"error": str(e)}
        except Exception as e:
            logger.error(f"主题分析失败: {e}")
            return {"error": str(e)}
    
    def analyze_conflicts(self, transcript: List[Dict]) -> Dict[str, Any]:
        """分析冲突"""
        logger.info("开始分析冲突")
        try:
            data = [{'id': d['id'], 'speaker': d['speaker'], 'content': d['content']} for d in transcript]
            
            try:
                result = chat_with_fallback(conflict_prompt, f"Transcripts of conversations: \n{str(data)}")
                
                logger.info("冲突分析完成")
                return self._parse_analysis_result(result)
            except Exception as e:
                logger.error(f"分析冲突时发生错误: {e}")
                return {"error": str(e)}
        except Exception as e:
            logger.error(f"冲突分析失败: {e}")
            return {"error": str(e)}
    
    def analyze_advantages(self, transcript: List[Dict]) -> Dict[str, Any]:
        """分析优势劣势"""
        logger.info("开始分析优势劣势")
        try:
            data = [{'id': d['id'], 'speaker': d['speaker'], 'content': d['content']} for d in transcript]
            
            try:
                result = chat_with_fallback(advantage_prompt, f"Transcripts of conversations: \n{str(data)}")
                
                logger.info("优势劣势分析完成")
                return self._parse_analysis_result(result)
            except Exception as e:
                logger.error(f"分析优势劣势时发生错误: {e}")
                return {"error": str(e)}
        except Exception as e:
            logger.error(f"优势劣势分析失败: {e}")
            return {"error": str(e)}
    
    def analyze_complete_profile(self, transcript: List[Dict]) -> Dict[str, Any]:
        """完整亲子画像分析"""
        logger.info("开始完整亲子画像分析")
        
        results = {
            'parenting_style': self.analyze_parenting_style(transcript),
            'sentiment_analysis': self.analyze_sentiment(transcript),
            'communication_patterns': self.analyze_communication_patterns(transcript),
            'topic_analysis': self.analyze_topics(transcript),
            'conflict_analysis': self.analyze_conflicts(transcript),
            'advantage_analysis': self.analyze_advantages(transcript)
        }
        
        logger.info("完整亲子画像分析完成")
        return results
    
    async def analyze_complete_profile_async(self, transcript: List[Dict]) -> Dict[str, Any]:
        """异步完整亲子画像分析"""
        logger.info("开始异步完整亲子画像分析")
        
        data = [{'id': d['id'], 'speaker': d['speaker'], 'content': d['content']} for d in transcript]
        data_str = str(data)
        
        async def analyze_with_prompt(prompt):
            try:
                result = await chat_with_fallback_async(prompt, f"Transcripts of conversations: \n{data_str}")
                return self._parse_analysis_result(result)
            except Exception as e:
                logger.error(f"异步分析时发生错误: {e}")
                return {"error": str(e)}
        
        # 并行执行所有分析任务
        tasks = [
            analyze_with_prompt(style_prompt),
            analyze_with_prompt(sentiment_prompt),
            analyze_with_prompt(patterns_prompt),
            analyze_with_prompt(topics_prompt),
            analyze_with_prompt(conflict_prompt),
            analyze_with_prompt(advantage_prompt)
        ]
        
        results_list = await asyncio.gather(*tasks)
        
        results = {
            'parenting_style': results_list[0],
            'sentiment_analysis': results_list[1],
            'communication_patterns': results_list[2],
            'topic_analysis': results_list[3],
            'conflict_analysis': results_list[4],
            'advantage_analysis': results_list[5]
        }
        
        logger.info("异步完整亲子画像分析完成")
        return results
    
    def _parse_analysis_result(self, result: str) -> Dict[str, Any]:
        """解析分析结果"""
        try:
            # 如果结果是JSON格式，尝试解析
            if result.strip().startswith('{') and result.strip().endswith('}'):
                import json
                return json.loads(result)
            else:
                # 如果不是JSON，返回原始文本
                return {"analysis": result}
        except Exception as e:
            logger.warning(f"解析分析结果失败: {e}")
            return {"analysis": result}


# 便捷函数
def analyze_audio(transcript: List[Dict]) -> tuple:
    """分析音频转录，返回各项分析结果"""
    profiler = ParentChildProfiler()
    
    style = profiler.analyze_parenting_style(transcript)
    sentiment = profiler.analyze_sentiment(transcript)
    patterns = profiler.analyze_communication_patterns(transcript)
    topics = profiler.analyze_topics(transcript)
    conflicts = profiler.analyze_conflicts(transcript)
    advantages = profiler.analyze_advantages(transcript)
    
    return style, sentiment, patterns, topics, conflicts, advantages


async def analyze_audio_async(transcript: List[Dict]) -> tuple:
    """异步分析音频转录，返回各项分析结果"""
    profiler = ParentChildProfiler()
    
    results = await profiler.analyze_complete_profile_async(transcript)
    
    return (
        results['parenting_style'],
        results['sentiment_analysis'],
        results['communication_patterns'],
        results['topic_analysis'],
        results['conflict_analysis'],
        results['advantage_analysis']
    ) 