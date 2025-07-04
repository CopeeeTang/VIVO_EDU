# -*- coding: utf-8 -*-
import logging
import asyncio
import os
import pickle
import hashlib
import functools
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings # 使用 api.py 中配置好的实例
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.document import Document
# from langchain.prompts import ChatPromptTemplate # 可能需要，如果使用 LangChain Prompt
# from langchain.schema.output_parser import StrOutputParser # 可能需要

# API 和 Prompt 导入
from .api import call_llm_async, azure_embedding_client # 导入嵌入客户端
try:
    # 假设 prompt.py 中定义了 RAG 相关 Prompt
    from ..prompt import (
        RAG_STRATEGY_TEMPLATE, RAG_EXAMPLE_TEMPLATE, 
        RAG_CONVERSATION_TEMPLATE, RAG_ANALYSIS_TEMPLATE,
        QUERY_GENERATION_TEMPLATE # 用于生成多查询的 Prompt
    )
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("无法从 prompt.py 导入 RAG Prompts。将使用占位符。")
    # 提供占位符
    RAG_STRATEGY_TEMPLATE = "Context: {context}\nQuestion: {question}\nAnswer:"
    RAG_EXAMPLE_TEMPLATE = "Context: {context}\nQuestion: {question}\nAnswer:"
    RAG_CONVERSATION_TEMPLATE = "Context: {context}\nQuestion: {question}\nAnswer:"
    RAG_ANALYSIS_TEMPLATE = "Context: {context}\nQuestion: {question}\nAnswer:"
    QUERY_GENERATION_TEMPLATE = "Generate related queries for: {question}"

logger = logging.getLogger(__name__)

# --- 缓存相关代码已移除 ---

# --- RAG 核心类 ---
class KnowledgeRAG:
    """
    实现 RAG 检索和生成流程。
    """
    def __init__(self, embedding_model: AzureOpenAIEmbeddings, index_folder_path: str):
        """
        初始化 RAG 系统。

        Args:
            embedding_model: 用于文本嵌入的 Langchain 模型实例。
            index_folder_path: FAISS 索引文件所在的目录路径。
        """
        self.embedding_model = embedding_model
        self.index_folder_path = Path(index_folder_path)
        self.vector_store = self._load_faiss_index()
        if not self.vector_store:
             raise RuntimeError("无法加载 FAISS 索引，RAG 系统无法初始化。")
             
        # retriever 可以根据需要配置 search_type 和 search_kwargs
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3}) # 默认检索 top 3
        logger.info(f"KnowledgeRAG initialized. Index loaded from: {self.index_folder_path}")

    def _load_faiss_index(self) -> Optional[FAISS]:
        """
        加载本地 FAISS 索引。
        假设索引文件名固定为 'faiss_index'。
        """
        index_file = self.index_folder_path / "faiss_index"
        if not index_file.exists():
            logger.error(f"FAISS 索引文件不存在于: {index_file}")
            # 尝试查找 .faiss 文件
            faiss_files = list(self.index_folder_path.glob("*.faiss"))
            if faiss_files:
                 index_file_base = faiss_files[0].stem # 获取不带扩展名的文件名
                 logger.info(f"找到 .faiss 文件，尝试加载索引: {index_file_base}")
                 try:
                      # FAISS.load_local 需要文件夹路径和基础索引名
                      return FAISS.load_local(str(self.index_folder_path), self.embedding_model, index_name=index_file_base, allow_dangerous_deserialization=True)
                 except Exception as e:
                      logger.error(f"加载 FAISS 索引 '{index_file_base}' 失败: {e}", exc_info=True)
                      return None
            else:
                 logger.error(f"在 {self.index_folder_path} 中未找到 'faiss_index' 或任何 .faiss 文件")
                 return None
        else:
             # 如果是旧格式（单独的 faiss_index 文件）
             logger.warning("检测到旧的 'faiss_index' 文件格式，建议使用文件夹格式保存索引 (index_name='your_index_name')")
             try:
                  # 旧的加载方式，可能不适用于新版 LangChain
                  with open(index_file, "rb") as f:
                      vector_store = pickle.load(f)
                  if isinstance(vector_store, FAISS):
                       # 需要确保加载的 embedding function 与当前一致
                       vector_store.embedding_function = self.embedding_model
                       logger.info("成功加载旧格式 FAISS 索引文件。")
                       return vector_store
                  else:
                       logger.error("旧格式索引文件内容不是 FAISS 实例。")
                       return None
             except Exception as e:
                  logger.error(f"加载旧格式 FAISS 索引失败: {e}", exc_info=True)
                  return None

    # 缓存已移除
    async def _generate_queries_with_llm(self, question: str, num_queries: int = 3) -> List[str]:
        """
        使用 LLM 根据原始问题生成多个相关查询以增强检索效果。
        """
        logger.debug(f"使用 LLM 生成查询: {question}")
        prompt = QUERY_GENERATION_TEMPLATE.format(question=question, num_queries=num_queries)
        messages = [{"role": "user", "content": prompt}]
        
        # 使用一个较快的模型进行查询生成
        response = await call_llm_async(
            client_type='zhizengzeng', 
            model='kimi-micro', # 或其他轻量级模型
            messages=messages,
            temperature=0.3
        )
        
        if not response:
            logger.warning("LLM 生成查询失败，将仅使用原始查询。")
            return [question]
            
        # 解析 LLM 返回的查询列表 (假设每行一个查询)
        queries = [q.strip() for q in response.strip().split('\n') if q.strip()]
        # 保证包含原始查询
        if question not in queries:
             queries.insert(0, question)
             
        logger.debug(f"生成的查询: {queries[:num_queries]}")
        return queries[:num_queries] # 返回指定数量的查询

    async def _retrieve_docs(self, queries: List[str]) -> List[Document]:
        """
        根据多个查询检索文档，并去重。
        """
        logger.debug(f"开始检索文档，查询数量: {len(queries)}")
        all_docs = []
        retrieval_tasks = [self.retriever.aget_relevant_documents(q) for q in queries]
        
        results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)
        
        unique_docs_dict = {}
        for i, result in enumerate(results):
             if isinstance(result, Exception):
                 logger.error(f"检索查询 '{queries[i]}' 时失败: {result}")
             elif isinstance(result, list):
                 for doc in result:
                     if isinstance(doc, Document) and doc.page_content not in unique_docs_dict:
                          unique_docs_dict[doc.page_content] = doc
             else:
                  logger.warning(f"检索查询 '{queries[i]}' 返回了非列表类型: {type(result)}")
                  
        all_docs = list(unique_docs_dict.values())
        logger.info(f"检索完成，共找到 {len(all_docs)} 篇独立文档。")
        return all_docs

    def _format_docs(self, docs: List[Document]) -> str:
        """
        将检索到的文档格式化为 LLM 的上下文。
        """
        if not docs:
             return "No relevant context found."
        # 简单的拼接，可以根据需要添加更多格式化逻辑
        return "\n\n".join([f"Document {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])

    # 缓存已移除
    async def invoke_rag_chain_async(
        self, 
        question: str, 
        template: str, # 使用哪个 Prompt 模板
        generate_sub_queries: bool = True, # 是否生成子查询
        client_type: str = 'zhizengzeng', 
        model: str = 'deepseek-chat' # 用于最终答案生成的模型
    ) -> str:
        """
        异步执行完整的 RAG 流程：查询生成 -> 检索 -> 格式化 -> LLM 生成答案。

        Args:
            question: 用户的原始问题。
            template: 用于最终答案生成的 Prompt 模板 (包含 {context} 和 {question})。
            generate_sub_queries: 是否使用 LLM 生成子查询以增强检索。
            client_type: 用于答案生成的 LLM 客户端。
            model: 用于答案生成的 LLM 模型。

        Returns:
            LLM 生成的最终答案字符串。
        """
        logger.info(f"开始 RAG 调用: 问题=\"{question}\", 模板={template[:50]}..." ) # 记录部分模板
        
        # 1. (可选) 生成查询
        if generate_sub_queries:
            queries = await self._generate_queries_with_llm(question)
        else:
            queries = [question]
            
        # 2. 检索文档
        retrieved_docs = await self._retrieve_docs(queries)
        
        # 3. 格式化上下文
        context = self._format_docs(retrieved_docs)
        
        # 4. 使用 LLM 生成答案
        prompt_filled = template.format(context=context, question=question)
        messages = [{"role": "user", "content": prompt_filled}]
        
        logger.debug(f"最终发送给 LLM ({client_type}/{model}) 的内容长度: {len(prompt_filled)}")
        
        final_answer = await call_llm_async(
            client_type=client_type,
            model=model,
            messages=messages,
            temperature=0.2 # RAG 通常需要较低的温度以基于上下文回答
        )
        
        if not final_answer:
             logger.error("RAG 最终答案生成失败。")
             return "Failed to generate answer based on retrieved context."

        logger.info("RAG 调用成功完成。")
        return final_answer

    async def process_scene_based_queries(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
        """
        针对场景重建的结果，异步执行多个 RAG 查询 (a1 到 a5)。

        Args:
            scenarios: 从 SceneryRebuilder 获取的场景列表。

        Returns:
            一个包含 a1 到 a5 结果的字典。
        """
        logger.info(f"开始基于 {len(scenarios)} 个场景进行 RAG 查询 (a1-a5)...")
        if not scenarios:
             logger.warning("场景列表为空，无法执行基于场景的 RAG 查询。")
             return {'a1': None, 'a2': None, 'a3': None, 'a4': None, 'a5': None}

        # 将场景信息格式化为字符串，以便作为 RAG 的输入问题
        # 这里是一个简单的示例，可能需要根据 Prompt 模板的要求调整格式
        scenarios_str = json.dumps(scenarios, ensure_ascii=False, indent=2)
        base_question = f"基于以下重建的家庭教育场景:\n{scenarios_str}\n\n请提供:"

        # 定义 a1 到 a5 的具体问题和使用的模板
        rag_tasks_info = [
            {'key': 'a1', 'question': base_question + " 1. 对每个场景家长引导的建议。", 'template': RAG_STRATEGY_TEMPLATE},
            {'key': 'a2', 'question': base_question + " 2. 为每个场景检索两个启发性案例。", 'template': RAG_EXAMPLE_TEMPLATE},
            {'key': 'a3', 'question': base_question + " 3. 每个场景对应的原始对话 (用于对比)。", 'template': RAG_CONVERSATION_TEMPLATE}, # 可能不需要 RAG?
            {'key': 'a4', 'question': base_question + " 4. 每个场景改进后的对话示例。", 'template': RAG_CONVERSATION_TEMPLATE},
            {'key': 'a5', 'question': base_question + " 5. 引发家长反思的问题：为什么会出现这种情况？", 'template': RAG_ANALYSIS_TEMPLATE}
        ]

        tasks = []
        for info in rag_tasks_info:
             # a3 可能直接从 scenarios 获取，而不是 RAG？
             if info['key'] == 'a3':
                 # 提取原始对话片段 (假设 scenarios 中包含)
                 original_dialogues = []
                 for i, scene in enumerate(scenarios):
                     details = scene.get('关键细节', [])
                     original_dialogues.append(f"场景 {i+1} 原始对话:\n" + "\n".join(details))
                 tasks.append(asyncio.sleep(0, result="\n\n".join(original_dialogues))) # 用 sleep 模拟异步返回
             else:
                 tasks.append(self.invoke_rag_chain_async(
                     question=info['question'], 
                     template=info['template'],
                     generate_sub_queries=True # 对复杂场景问题启用子查询
                 ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_rag_results = {}
        for i, result in enumerate(results):
            key = rag_tasks_info[i]['key']
            if isinstance(result, Exception):
                logger.error(f"执行 RAG 查询 '{key}' 时失败: {result}")
                final_rag_results[key] = None
            else:
                final_rag_results[key] = result
        
        logger.info("基于场景的 RAG 查询 (a1-a5) 完成。")
        return final_rag_results

# --- 示例用法 (可选) ---
# async def main():
#     # 确保设置了 Azure 嵌入环境变量或在 api.py 中配置
#     # 假设 FAISS 索引在 'checkpoints/faiss_index' 目录
#     index_path = "./checkpoints"
#     if not os.path.exists(index_path):
#          print(f"Error: Index path does not exist: {index_path}")
#          return
#     if not any(f.endswith('.faiss') or f == 'faiss_index' for f in os.listdir(index_path)):
#          print(f"Error: No FAISS index file found in {index_path}")
#          return
#          
#     try:
#         rag_system = KnowledgeRAG(
#             embedding_model=azure_embedding_client, 
#             index_folder_path=index_path
#         )
#     except RuntimeError as e:
#          print(e)
#          return
#     
#     # 示例场景数据 (来自 SceneryRebuilder)
#     sample_scenarios = [
#         {
#             "事件": "辅导数学作业",
#             "变化": "从耐心指导转变为不耐烦",
#             "关键细节": [
#                 "家长: 这道题怎么又错了？",
#                 "孩子: 我就是不会嘛...",
#                 "家长: 跟你讲了多少遍了！真是笨！"
#             ]
#         }
#     ]
#     
#     # 执行基于场景的查询
#     a_results = await rag_system.process_scene_based_queries(sample_scenarios)
#     
#     print("\nRAG Results (a1-a5):")
#     for key, value in a_results.items():
#         print(f"\n--- {key} ---")
#         print(value if value else "[生成失败或无结果]")
# 
# if __name__ == "__main__":
#     asyncio.run(main()) 