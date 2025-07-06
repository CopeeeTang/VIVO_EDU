# -*- coding: utf-8 -*-
"""
优化后的知识库检索模块
在教育知识库中寻找匹配案例
"""

import json
import logging
import pickle
import time
import functools
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import os
import psutil

# 导入向量检索相关模块
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_openai.embeddings import OpenAIEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("Langchain相关模块未安装，将使用简化版本")

from .api_clients import api_client

logger = logging.getLogger(__name__)


def cache_result(func):
    """缓存装饰器"""
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 创建缓存键
        cache_key = str(args) + str(sorted(kwargs.items()))
        if cache_key in cache:
            return cache[cache_key]
        
        result = func(*args, **kwargs)
        cache[cache_key] = result
        return result
    
    return wrapper


class EnhancedKnowledgeBase:
    """优化后的知识库检索器"""
    
    def __init__(self, index_folder_path: str = "checkpoints/index/", docs_path: str = None):
        self.index_folder_path = Path(index_folder_path)
        self.docs_path = docs_path
        self.vector_store = None
        self.embeddings = None
        self.docs = []
        self.fallback_knowledge = self._create_fallback_knowledge()
        
        # 初始化知识库
        self._initialize()
    
    def _initialize(self):
        """初始化知识库"""
        logger.info("初始化知识库...")
        
        if LANGCHAIN_AVAILABLE:
            try:
                # 尝试加载已有的FAISS索引
                self._load_faiss_index()
                logger.info("知识库初始化成功")
            except Exception as e:
                logger.warning(f"加载FAISS索引失败: {e}")
                self._create_fallback_retriever()
        else:
            self._create_fallback_retriever()
    
    def _load_faiss_index(self):
        """加载FAISS索引"""
        if not self.index_folder_path.exists():
            logger.warning(f"索引文件夹不存在: {self.index_folder_path}")
            raise FileNotFoundError("索引文件夹不存在")
        
        try:
            # 检查可用内存
            available_memory_gb = psutil.virtual_memory().available / (1024**3)
            logger.info(f"可用内存: {available_memory_gb:.2f}GB")
            
            if available_memory_gb < 1.0:  # 可用内存少于1GB
                logger.warning("可用内存不足1GB，使用备用检索器")
                raise MemoryError("可用内存不足")
            
            # 初始化embeddings（使用较小的模型）
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=os.environ.get('OPENAI_API_KEY'),
                model="text-embedding-3-small"  # 使用小模型减少内存占用
            )
            
            # 分块加载FAISS索引以减少内存压力
            logger.info("正在加载FAISS索引...")
            
            try:
                # 尝试直接加载
                self.vector_store = FAISS.load_local(
                    str(self.index_folder_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("FAISS索引加载成功")
                
                # 测试检索功能
                test_results = self.vector_store.similarity_search("测试", k=1)
                if not test_results:
                    logger.warning("FAISS索引测试失败，使用备用方案")
                    raise ValueError("索引测试失败")
                    
            except MemoryError as me:
                logger.error(f"内存不足，无法加载FAISS索引: {me}")
                raise
            except Exception as load_error:
                logger.error(f"FAISS索引加载失败: {load_error}")
                # 尝试清理内存后重试
                import gc
                gc.collect()
                raise
                
        except (MemoryError, Exception) as e:
            logger.error(f"加载FAISS索引失败: {e}")
            # 使用备用检索器
            self._create_fallback_retriever()
            raise
    
    def _create_fallback_retriever(self):
        """创建备用知识库检索器"""
        logger.info("创建备用知识库检索器")
        self.vector_store = None
        self.embeddings = None
    
    def _create_fallback_knowledge(self) -> Dict[str, Any]:
        """创建备用知识库"""
        return {
            "教育方法": [
                "正面管教：通过理解孩子的行为动机，使用鼓励和引导的方式帮助孩子学习",
                "启发式教学：通过提问和引导，让孩子自己发现问题和解决方案",
                "情感支持：理解和接纳孩子的情感，提供安全的情感表达空间"
            ],
            "沟通技巧": [
                "积极倾听：全神贯注地听孩子说话，理解他们的想法和感受",
                "共情回应：用孩子能理解的方式表达对他们情感的理解",
                "开放式提问：使用开放式问题鼓励孩子表达更多想法"
            ],
            "冲突解决": [
                "冷静处理：在冲突发生时，先让自己冷静下来，避免情绪化反应",
                "问题导向：关注问题本身，而不是指责孩子的行为",
                "合作解决：与孩子一起寻找解决方案，让他们参与决策过程"
            ],
            "学习支持": [
                "个性化学习：根据孩子的学习风格和兴趣调整教学方法",
                "及时反馈：在学习过程中给予及时的正面反馈和建设性建议",
                "创造环境：营造有利于学习的环境和氛围"
            ]
        }
    
    @cache_result
    def search_knowledge(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """搜索知识库"""
        logger.info(f"搜索知识库: {query[:50]}...")
        
        try:
            if self.vector_store is not None:
                # 使用FAISS进行向量搜索
                return self._vector_search(query, top_k)
            else:
                # 使用备用搜索
                return self._fallback_search(query, top_k)
        except Exception as e:
            logger.error(f"知识库搜索失败: {e}")
            return self._fallback_search(query, top_k)
    
    def _vector_search(self, query: str, top_k: int) -> Dict[str, Any]:
        """向量搜索"""
        try:
            # 执行相似性搜索
            docs = self.vector_store.similarity_search_with_score(query, k=top_k)
            
            results = []
            for doc, score in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            return {
                "query": query,
                "results": results,
                "total": len(results),
                "search_type": "vector_search"
            }
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return self._fallback_search(query, top_k)
    
    def _fallback_search(self, query: str, top_k: int) -> Dict[str, Any]:
        """备用搜索"""
        logger.info("使用备用搜索")
        
        # 简单的关键词匹配
        query_lower = query.lower()
        matched_results = []
        
        for category, items in self.fallback_knowledge.items():
            for item in items:
                # 计算简单的相似度
                score = self._calculate_similarity(query_lower, item.lower())
                if score > 0.1:  # 阈值
                    matched_results.append({
                        "content": item,
                        "metadata": {"category": category},
                        "score": score
                    })
        
        # 按分数排序
        matched_results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "query": query,
            "results": matched_results[:top_k],
            "total": len(matched_results),
            "search_type": "fallback_search"
        }
    
    def _calculate_similarity(self, query: str, text: str) -> float:
        """计算简单的文本相似度"""
        query_words = set(query.split())
        text_words = set(text.split())
        
        if not query_words or not text_words:
            return 0.0
        
        intersection = query_words.intersection(text_words)
        union = query_words.union(text_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_relevant_documents(self, query: str, max_docs: int = 3) -> List[Dict[str, Any]]:
        """获取相关文档"""
        search_result = self.search_knowledge(query, max_docs)
        return search_result.get("results", [])
    
    def generate_educational_advice(self, transcript: List[Dict], search_results: List[Dict]) -> Dict[str, Any]:
        """基于搜索结果生成教育建议"""
        logger.info("生成教育建议")
        
        try:
            # 准备上下文
            context = self._prepare_context(transcript, search_results)
            
            # 构建提示
            prompt = self._build_advice_prompt(context)
            
            # 调用API生成建议
            if api_client.vivo_client:
                advice = api_client.chat_with_vivo(
                    "你是一个专业的家庭教育专家，请基于以下内容为家长提供教育建议。",
                    prompt
                )
            elif api_client.deepseek_v3_client:
                response = api_client.deepseek_v3_client.chat.completions.create(
                    model="ep-20250331105849-cbfg5",
                    messages=[
                        {"role": "system", "content": "你是一个专业的家庭教育专家，请基于以下内容为家长提供教育建议。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                advice = response.choices[0].message.content
            else:
                advice = "无法生成建议：没有可用的API客户端"
            
            return {
                "advice": advice,
                "context": context,
                "search_results": search_results
            }
            
        except Exception as e:
            logger.error(f"生成教育建议失败: {e}")
            return {
                "advice": "生成建议时发生错误",
                "error": str(e)
            }
    
    def _prepare_context(self, transcript: List[Dict], search_results: List[Dict]) -> Dict[str, Any]:
        """准备上下文"""
        # 提取对话摘要
        dialogue_summary = self._extract_dialogue_summary(transcript)
        
        # 整理知识库内容
        knowledge_content = []
        for result in search_results:
            knowledge_content.append({
                "content": result.get("content", ""),
                "category": result.get("metadata", {}).get("category", "unknown"),
                "relevance": result.get("score", 0)
            })
        
        return {
            "dialogue_summary": dialogue_summary,
            "knowledge_content": knowledge_content,
            "participant_count": len(set(item.get("speaker", "") for item in transcript))
        }
    
    def _extract_dialogue_summary(self, transcript: List[Dict]) -> str:
        """提取对话摘要"""
        if not transcript:
            return "无对话内容"
        
        # 简单的摘要生成
        speakers = set()
        total_turns = len(transcript)
        
        for item in transcript:
            speakers.add(item.get("speaker", "unknown"))
        
        return f"对话包含{total_turns}轮交流，参与者：{', '.join(speakers)}"
    
    def _build_advice_prompt(self, context: Dict[str, Any]) -> str:
        """构建建议生成的提示"""
        prompt = f"""
请基于以下信息为家长提供具体的教育建议：

对话情况：
{context['dialogue_summary']}

相关教育知识：
"""
        
        for i, knowledge in enumerate(context['knowledge_content'], 1):
            prompt += f"\n{i}. {knowledge['content']} (相关性: {knowledge['relevance']:.2f})"
        
        prompt += """

请提供：
1. 针对当前情况的具体建议
2. 可以采取的实际行动
3. 需要注意的问题
4. 长期的教育策略

建议要求：
- 具体可行
- 适合家庭环境
- 考虑孩子的发展特点
- 注重亲子关系的建设
"""
        
        return prompt
    
    def multi_query_search(self, queries: List[str], top_k: int = 3) -> Dict[str, Any]:
        """多查询搜索"""
        logger.info(f"执行多查询搜索，查询数量: {len(queries)}")
        
        all_results = []
        
        # 并行执行搜索
        with ThreadPoolExecutor(max_workers=min(len(queries), 5)) as executor:
            futures = {executor.submit(self.search_knowledge, query, top_k): query for query in queries}
            
            for future in futures:
                try:
                    result = future.result()
                    all_results.extend(result.get("results", []))
                except Exception as e:
                    logger.error(f"搜索查询失败: {e}")
        
        # 去重和排序
        unique_results = self._deduplicate_results(all_results)
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return {
            "queries": queries,
            "results": unique_results[:top_k * 2],  # 返回更多结果
            "total": len(unique_results),
            "search_type": "multi_query_search"
        }
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """去重结果"""
        seen = set()
        unique_results = []
        
        for result in results:
            content = result.get("content", "")
            if content not in seen:
                seen.add(content)
                unique_results.append(result)
        
        return unique_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        stats = {
            "has_vector_store": self.vector_store is not None,
            "has_embeddings": self.embeddings is not None,
            "fallback_categories": len(self.fallback_knowledge),
            "index_path": str(self.index_folder_path),
            "langchain_available": LANGCHAIN_AVAILABLE
        }
        
        if self.vector_store is not None:
            try:
                stats["vector_count"] = self.vector_store.index.ntotal
            except:
                stats["vector_count"] = "unknown"
        
        return stats


# 全局实例
knowledge_base = EnhancedKnowledgeBase()


# 便捷函数
def search_knowledge(query: str, top_k: int = 5) -> Dict[str, Any]:
    """搜索知识库的便捷函数"""
    return knowledge_base.search_knowledge(query, top_k)


def get_educational_advice(transcript: List[Dict], query: str = None) -> Dict[str, Any]:
    """获取教育建议的便捷函数"""
    if query is None:
        # 从对话中提取查询
        query = ' '.join([item.get('content', '') for item in transcript[:3]])  # 使用前3条对话
    
    search_results = knowledge_base.get_relevant_documents(query)
    return knowledge_base.generate_educational_advice(transcript, search_results)


# 兼容性类
class Knowledge_Base:
    """兼容性类，保持与原有代码的兼容性"""
    
    def __init__(self, docs: object = None, input_data: dict = None, index_folder_path: str = None):
        self.enhanced_kb = knowledge_base
        self.docs = docs
        self.input_data = input_data
        
        if index_folder_path and index_folder_path != knowledge_base.index_folder_path:
            # 如果指定了不同的路径，创建新的实例
            self.enhanced_kb = EnhancedKnowledgeBase(index_folder_path)
    
    def search_knowledge(self, query: str) -> Dict[str, Any]:
        """搜索知识库"""
        return self.enhanced_kb.search_knowledge(query)
    
    def get_relevant_documents(self, query: str) -> List[Dict[str, Any]]:
        """获取相关文档"""
        return self.enhanced_kb.get_relevant_documents(query)
    
    def result(self) -> Dict[str, Any]:
        """兼容性方法"""
        if self.input_data:
            query = str(self.input_data)
            return self.enhanced_kb.search_knowledge(query)
        else:
            return {"error": "No input data provided"}
    
    def __del__(self):
        """清理资源"""
        pass 