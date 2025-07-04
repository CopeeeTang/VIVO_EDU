import json
import pickle
import time
from pathlib import Path
from typing import List, Dict, Any
import json
import time
from typing import List, Dict, Any
from operator import itemgetter
from tqdm.auto import tqdm
from IPython.display import display, Markdown
from openai import OpenAI
from .prompt import Scenery_user_prompt, Scenery_system_prompt
from operator import itemgetter
from tqdm import tqdm
from IPython.display import display, Markdown,JSON
from .prompt import Scenery_user_prompt,Scenery_system_prompt
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from json import loads, dumps
import time
from operator import itemgetter
from tqdm import tqdm
from langchain_community.vectorstores import FAISS
import concurrent.futures
import functools
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import queue
from langchain_openai import OpenAIEmbeddings,AzureOpenAIEmbeddings,AzureChatOpenAI
import os


DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

# 新的DeepSeek API客户端 - v3
client_deepseek_v3 = OpenAI(
    api_key="a306bf91-ca05-442f-b09d-8ebaca556f0a",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    timeout=60
)
# 新的DeepSeek API客户端 - v3
client_deepseek_r1 = OpenAI(
    api_key="a306bf91-ca05-442f-b09d-8ebaca556f0a",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    timeout=60
)

# 同步请求 DeepSeek v3
def deepseek_v3_prompt(prompt, input_data, max_retries=3, delay=5):
    attempt = 0
    input_str = 'Transcripts of conversations: \n' + str(input_data)
    while attempt < max_retries:
        try:
            start_time = time.time()
            response = client_deepseek_v3.chat.completions.create(
                model="ep-20250217231058-gx2x5",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_str}
                ],
                temperature=0
            )
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"DeepSeek v3 running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred v3: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            time.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None
# 同步请求 DeepSeek r1
def deepseek_r1_prompt(prompt, input_data, max_retries=3, delay=5):
    attempt = 0
    # 将system prompt和user prompt合并
    user_prompt = f"{prompt}\n \n{str(input_data)}"
    while attempt < max_retries:
        try:
            start_time = time.time()
            response = client_deepseek_r1.chat.completions.create(
                model="ep-20250213154525-wkfdb",
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6
            )
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"DeepSeek r1 running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred r1: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            time.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None

class Scenery_rebuild:
    def __init__(self,input_data:str,system_prompt:str,user_prompt:str) -> None:
        self.input = input_data
        self.client = OpenAI(
           api_key=os.environ.get('ZHIZENGZENG_API_KEY'),
            base_url="https://api.zhizengzeng.com/v1",
            )

        self.tools = self._define_tools()
        self.system_prompt=system_prompt
        self.user_prompt=user_prompt
        print("Initialized Scenery_rebuild")

    #工具定义
    def _define_tools(self) -> List[Dict[str, Any]]:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "Scenery_rebuild",
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
                                        "事件": {
                                            "type": "string",
                                            "description": " 详细描述场景中的主要教育事件，包括主题（如作业辅导、行为管教）、参与者、核心互动过程和结果。"
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
                                            "description": "提取能体现场景特点的关键对话片段。包括情感强烈、体现教育方法或反映问题核心的对话。每个片段应标注说话者和情感色彩，有助于后续分析和案例匹配。"
                                        }
                                    }
                                },
                                "description": "每个识别出场景的详细摘要，结构化呈现以便于后续的知识库检索和相似案例匹配。摘要应包含足够的上下文信息和关键要素，以确保准确的场景重建和案例对比。"
                            }
                        },
                        "required": ["场景数量", "场景摘要"]
                    }
                }
            }
        ]
        return tools
    
    def Scenery_rebuild(self, arguments: List[Dict[str, Any]]) -> str:
        try:
            # 如果arguments已经是完整的结构
            if isinstance(arguments, dict) and "场景数量" in arguments and "场景摘要" in arguments:
                return json.dumps(arguments)
            
            # 如果arguments是列表
            environment_info = {
                "场景数量": len(arguments) if isinstance(arguments, list) else 1,
                "场景摘要": []
            }
            
            # 处理不同的输入类型
            if isinstance(arguments, list):
                for scene in arguments:
                    if isinstance(scene, dict):
                        info = {
                            "事件": scene.get("事件", ""),
                            "变化": scene.get("变化", ""),
                            "关键细节": scene.get("关键细节", [])
                        }
                        environment_info["场景摘要"].append(info)
            elif isinstance(arguments, dict):
                # 单个场景的情况
                info = {
                    "事件": arguments.get("事件", ""),
                    "变化": arguments.get("变化", ""),
                    "关键细节": arguments.get("关键细节", [])
                }
                environment_info["场景摘要"].append(info)
            
            return json.dumps(environment_info)
        except Exception as e:
            print(f"处理场景时发生错误: {e}")
            # 返回一个简单的默认结构防止崩溃
            default_info = {
                "场景数量": 1,
                "场景摘要": [{
                    "事件": "数据处理异常",
                    "变化": "处理失败",
                    "关键细节": ["处理输入时发生错误"]
                }]
            }
            return json.dumps(default_info)

    #工具调用
    def call_tool(self, tool_call_id: str, name: str, arguments: str, message_history: List[Dict[str, Any]]):
        try:
            # 确保arguments是字符串
            if not isinstance(arguments, str):
                arguments = json.dumps(arguments)
            
            # 简单解析JSON，不做复杂的修复
            try:
                arguments_obj = json.loads(arguments)
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                arguments_obj = {"事件": "JSON解析失败", "变化": "无法分析", "关键细节": ["JSON无法解析"]}
            
            # 根据函数名选择不同的处理方法
            if name == "Scenery_rebuild":
                function_response = self.Scenery_rebuild(arguments_obj)
            else:
                function_response = json.dumps({"错误": f"未知的函数名: {name}"})
            
            message_history.append({
                "role": "function",
                "name": name,
                "content": function_response,
                "tool_call_id": tool_call_id,
            })
        except Exception as e:
            print(f"调用工具时发生错误: {e}")
            # 添加错误信息到消息历史
            message_history.append({
                "role": "function",
                "name": name,
                "content": json.dumps({"错误": f"工具调用失败: {str(e)}"}),
                "tool_call_id": tool_call_id,
            })

    def call_deepseekv3(self, message_history: List[Dict[str, Any]]) -> str:
        setting = {
            "model": "gpt-4.1",  # 更新为新的模型
            "tools": self.tools,  # 按照新的方式传递tools
            "tool_choice": "auto",
            "temperature": 0.6,
        }
        try:
            response = self.client.chat.completions.create(messages=message_history, **setting)
        except Exception as e:
            print(f"Error during API call: {e}")
            return None

        function_output = {"name": "", "arguments": ""}
        for part in response.choices:
            new_delta = part.message
            tool_calls = new_delta.tool_calls
            if tool_calls:
                for tool_call in tool_calls:
                    function = tool_call.function
                    if function and function.name and function.arguments:
                        function_output["name"] += function.name
                        function_output["arguments"] += function.arguments

        if function_output["name"]:
            self.call_tool(
                tool_call_id=None,
                name=function_output["name"],
                arguments=function_output["arguments"],
                message_history=message_history,
            )

        return function_output["arguments"]

    #后处理
    def final_handle(self):
        message_history = [
            {
                "role": "system",
                "content": (
                    self.system_prompt
                ),
            },
            {
                "role": "user",
                "content": (
                    self.user_prompt
                ),
            }
        ]
        message_history.append({"role": "user", "content": self.input})
        cur_iter=0
        while cur_iter < 1:
            start_time=time.time()
            scenery=self.call_deepseekv3(message_history)
            end_time=time.time()
            print(f"场景重建耗时{end_time-start_time}s")
            print(scenery)
            cur_iter+=1
        
        # 简化的JSON处理
        try:
            # 如果scenery是字符串，尝试解析为JSON对象
            if isinstance(scenery, str):
                scenery_obj = json.loads(scenery)
            else:
                scenery_obj = scenery
                
            # 简单验证结果格式
            if not isinstance(scenery_obj, dict) or "场景摘要" not in scenery_obj:
                return {
                    "场景数量": 1,
                    "场景摘要": [{
                        "事件": "格式错误",
                        "变化": "返回格式不符合预期",
                        "关键细节": ["格式验证失败"]
                    }]
                }
                
            # 确保场景数量与场景摘要数组长度一致
            scenery_obj["场景数量"] = len(scenery_obj.get("场景摘要", []))
            
            return scenery_obj
        except Exception as e:
            print(f"JSON解析错误: {e}")
            return {
                "场景数量": 1,
                "场景摘要": [{
                    "事件": "数据处理异常",
                    "变化": "处理失败",
                    "关键细节": ["发生内部错误"]
                }]
            }
    
    #格式化输出
    def format_output(self):
        scenery = self.final_handle()
        queries = []
        
        # 遍历所有场景
        for i, scene in enumerate(scenery.get('场景摘要', [])):
            事件 = scene.get("事件", "未知事件")
            变化 = scene.get("变化", "未知变化")
            combined = f"{事件} {变化}"
            queries.append(f"第{i+1}个场景{combined}")
        
        # 如果没有场景，添加默认查询
        if not queries:
            queries.append("无场景信息")
            
        return queries

# 添加到Knowledge_Base类之前
class EnhancedDummyRetriever:
    """改进的备用检索器，直接提供一些通用知识"""
    
    def __init__(self):
        # 预设一些通用教育知识
        self.general_knowledge = [
            {"page_content": "教育中的积极引导：赞美和鼓励比批评更有效。通过积极引导，可以帮助孩子建立自信心和正面行为模式。当孩子做出正确行为时，及时表扬和肯定，能够强化这些行为。"},
            {"page_content": "冲突处理：家庭教育中的冲突是正常现象，重要的是如何处理。保持冷静，倾听孩子的想法，寻找共同解决方案是有效处理冲突的关键步骤。"},
            {"page_content": "情绪管理：教导孩子识别和表达情绪的能力是重要的。家长应该成为榜样，展示健康的情绪管理方式，同时接纳孩子的情绪表达。"},
            {"page_content": "设定界限：明确一致的规则和期望有助于孩子理解行为边界。规则应该清晰、合理、可执行，并适合孩子的年龄和发展阶段。"},
            {"page_content": "关注力训练：现代社会中，孩子的注意力容易分散。通过有趣的互动游戏和活动，可以帮助孩子提高专注力。减少电子设备使用时间也是关键。"}
        ]
    
    def get_relevant_documents(self, query):
        """根据查询返回最相关的通用知识"""
        print(f"使用备用检索器处理查询: {query}")
        # 向用户返回一些通用知识，并说明这些是备用信息
        return self.general_knowledge + [
            {"page_content": "注意：由于知识库检索暂时不可用，以上信息来自系统预设的通用教育知识。请在系统恢复后重新查询以获取更准确的信息。"}
        ]


# 创建查询缓存
query_cache = {}
cache_lock = threading.Lock()

# 创建文档缓存
document_cache = {}
doc_cache_lock = threading.Lock()

# 缓存装饰器
def cache_result(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 创建缓存键
        key = hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()
        with cache_lock:
            if key in query_cache:
                print(f"缓存命中: {func.__name__}")
                return query_cache[key]
        
        result = func(*args, **kwargs)
        with cache_lock:
            query_cache[key] = result
        return result
    return wrapper

class Knowledge_Base:
    def __init__(self, docs: object, input_data: dict, index_folder_path: str = None):
        """
        docs: 预加载的文档对象（传统方式）
        input_data: 包含场景摘要的字典
        index_folder_path: 预处理的FAISS索引路径（新方式）
        """
        self.input = input_data
        self.docs = docs
        self.index_folder_path = index_folder_path
        self.embedding_model = OpenAIEmbeddings(model='text-embedding-3-large',openai_api_base='https://api.zhizengzeng.com/v1',openai_api_key=os.environ.get('ZHIZENGZENG_API_KEY'))
        #self.embedding_model = AzureOpenAIEmbeddings(
            #azure_endpoint='https://pcg-east-us3.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15',
            #api_key=os.environ.get('AZURE_OPENAI_API_KEY'),
            #model="text-embedding-3-large",
        #)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
        self.doc_retriever = None  # 文档检索器
        self.executor = ThreadPoolExecutor(max_workers=5, 
                                          thread_name_prefix="KB_Worker")
        
        # 设置所有线程为守护线程
        for thread in self.executor._threads:
            thread.daemon = True
            
        # 如果提供了预处理索引路径，优先使用
        if index_folder_path:
            self.load_faiss_index()
        
    def load_faiss_index(self):
        """从预处理的FAISS索引加载向量存储"""
        if not self.index_folder_path:
            print("未提供索引文件夹路径")
            return False
            
        try:
            # 检查路径是否存在
            if not os.path.exists(self.index_folder_path):
                print(f"索引文件夹不存在: {self.index_folder_path}")
                return False
                
            # 检查index.faiss和index.pkl文件是否存在
            if not (os.path.exists(os.path.join(self.index_folder_path, "index.faiss")) and 
                    os.path.exists(os.path.join(self.index_folder_path, "index.pkl"))):
                print(f"索引文件不完整: 缺少index.faiss或index.pkl文件")
                return False
            
            # 检查权限
            if not (os.access(os.path.join(self.index_folder_path, "index.faiss"), os.R_OK) and
                    os.access(os.path.join(self.index_folder_path, "index.pkl"), os.R_OK)):
                print(f"权限不足: 无法读取索引文件")
                return False
                
            # 加载FAISS索引
            print(f"正在从 {self.index_folder_path} 加载FAISS索引...")
            start_time = time.time()
            
            vector_store = FAISS.load_local(
                folder_path=self.index_folder_path,
                embeddings=self.embedding_model,
                allow_dangerous_deserialization=True
            )
            
            end_time = time.time()
            print(f"成功加载预存FAISS索引，耗时: {end_time - start_time:.2f}秒")
            
            # 尝试多种方式初始化检索器
            try:
                # 方式1: 标准方式
                retriever = vector_store.as_retriever(search_kwargs={'k': 3})
                # 简单测试
                _ = retriever.get_relevant_documents("家庭教育")
                print("检索器初始化成功 (标准方式)")
                self.doc_retriever = retriever
                return True
            except Exception as e1:
                print(f"标准检索器初始化失败: {e1}")
                
                try:
                    # 方式2: 不带参数
                    retriever = vector_store.as_retriever()
                    _ = retriever.get_relevant_documents("家庭教育")
                    print("检索器初始化成功 (不带参数方式)")
                    self.doc_retriever = retriever
                    return True
                except Exception as e2:
                    print(f"无参数检索器初始化失败: {e2}")
                    
                    try:
                        # 方式3: 使用自定义包装器
                        self.vector_store = vector_store
                        
                        # 自定义检索函数，与现有的_retrieve_docs兼容
                        def custom_retriever(query):
                            try:
                                return vector_store.similarity_search(query, k=3)
                            except Exception as e:
                                print(f"自定义检索器搜索错误: {e}")
                                return []
                                
                        self.doc_retriever = custom_retriever
                        # 测试检索
                        test_results = custom_retriever("家庭教育")
                        if test_results:
                            print(f"自定义检索器初始化成功，返回 {len(test_results)} 条结果")
                            return True
                        else:
                            print("自定义检索器未返回结果")
                            raise ValueError("检索测试返回空结果")
                    except Exception as e3:
                        print(f"自定义检索器初始化失败: {e3}")
                        # 最后尝试创建备用检索器
                        print("使用备用检索器...")
                        self.doc_retriever = EnhancedDummyRetriever()
                        return False
                        
        except Exception as e:
            print(f"FAISS索引加载失败: {e}")
            # 创建备用检索器
            self.doc_retriever = EnhancedDummyRetriever()
            return False
        
    def process_file(self):
        """优化的文档检索系统初始化"""
        # 如果已经成功加载了检索器，则无需处理
        if self.doc_retriever:
            return
            
        try:
            if not self.docs:
                raise ValueError("无效的文档源")
            
            # 优先尝试使用预处理索引
            if self.index_folder_path:
                success = self.load_faiss_index()
                if success:
                    return
            
            # 使用传统方式
            if hasattr(self.docs, 'get_relevant_documents'):
                self.doc_retriever = self.docs
                print("使用已初始化的检索器")
            else:
                # 如果没有检索器，尝试从文档构建
                try:
                    texts = []
                    if isinstance(self.docs, list):
                        for doc in self.docs:
                            if hasattr(doc, 'page_content'):
                                texts.append(doc.page_content)
                            else:
                                texts.append(str(doc))
                    else:
                        text_content = str(self.docs)
                        texts = self.text_splitter.split_text(text_content)
                    
                    print(f"从 {len(texts)} 个文本片段创建FAISS索引...")
                    
                    # 使用更高效的参数创建检索器
                    vector_store = FAISS.from_texts(
                        texts=texts,
                        embedding=self.embedding_model
                    )
                    
                    self.doc_retriever = vector_store.as_retriever(search_kwargs={'k': 2})
                    print("检索器创建成功")
                    
                except Exception as e:
                    print(f"创建检索器失败: {e}")
                    # 创建一个备用检索器
                    self.doc_retriever = EnhancedDummyRetriever()
            
            print("知识库初始化完成")
            
        except Exception as e:
            print(f"文档处理失败: {e}")
            # 创建一个备用检索器
            self.doc_retriever = EnhancedDummyRetriever()

    def _generate_queries(self, question: str, query_type: str) -> list:
        """查询改写核心方法 (无缓存)"""
        templates = {
            'Multi_query': """生成3个不同角度的查询问题...原始问题:{question}""",  # 减少到3个查询
            'RAG_Fusion': """生成3个优化后的知识库查询语句...原始查询:{question}"""    # 减少到3个查询
        }
        
        prompt = templates[query_type].format(question=question)
        response = deepseek_v3_prompt(prompt, question)
        return response.split("\n") if response else [question]

    def _retrieve_docs(self, queries: list) -> list:
        """优化的并发多路检索与结果融合 (无缓存版本)"""
        # 设置重试机制
        timeout = 30  # 超时时间
        max_retries = 2
        
        # 如果检索器还未初始化，确保初始化
        if not self.doc_retriever:
            self.process_file()
            if not self.doc_retriever:
                return []
        
        def process_query(query, attempt=0):
            try:
                # 检查检索器类型并适当处理
                if callable(self.doc_retriever) and not hasattr(self.doc_retriever, 'get_relevant_documents'):
                    # 自定义检索函数
                    docs = self.doc_retriever(query)
                else:
                    # 标准检索器
                    docs = self.doc_retriever.get_relevant_documents(query)
                    
                # 标准化结果格式
                return [{
                    "page_content": getattr(doc, 'page_content', str(doc)),
                    "metadata": getattr(doc, 'metadata', {})
                } for doc in docs]
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(0.5)  # 短暂延迟后重试
                    return process_query(query, attempt + 1)
                print(f"查询失败: {e}")
                return []
        
        # 并发查询处理
        futures = []
        for query in queries:
            futures.append(self.executor.submit(process_query, query))
        
        # 收集可用结果
        result_docs = []
        for future in as_completed(futures, timeout=timeout):
            try:
                docs = future.result()
                result_docs.extend(docs)
            except Exception:
                continue  # 忽略单个查询失败
        
        # 去重并返回
        seen_contents = set()
        unique_docs = []
        for doc in result_docs:
            content = doc.get("page_content", "")
            if content and content not in seen_contents:
                seen_contents.add(content)
                unique_docs.append(doc)
        
        return unique_docs

    def _build_processor(self, template: str, query_type: str, use_reasoning: bool = False):
        """改进的处理器工厂方法，每次重新生成结果"""
        def processor(question: str) -> str:
            try:
                # 设置超时标志
                retrieval_failed = False
                
                # 生成优化查询 (无缓存)
                queries = self._generate_queries(question, query_type)
                
                try:
                    # 尝试检索文档，有超时控制
                    docs = self._retrieve_docs(queries)
                    if not docs:
                        retrieval_failed = True
                except Exception:
                    # 检索失败时触发回退
                    retrieval_failed = True
                    docs = []
                
                if retrieval_failed:
                    # 检索失败时直接使用大模型生成回应
                    if use_reasoning:
                        fallback_prompt = f"""
                        无法访问知识库，但请尽力根据您的知识回答以下问题。
                        需要解答的问题：{question}
                        
                        请提供最相关的回答，明确标注这是基于您已有的知识。
                        """
                        return deepseek_r1_prompt(fallback_prompt, "") or "无法获取结果"
                    else:
                        fallback_prompt = f"""
                        无法连接知识库，请根据您已有的知识回答：
                        {question}
                        
                        请标注这是基于通用知识的回答。
                        """
                        return deepseek_v3_prompt(fallback_prompt, "") or "无法获取结果"
                
                # 正常流程：检索成功
                context_parts = [doc.get("page_content", "") for doc in docs if doc.get("page_content")]
                
                # 限制上下文长度
                context = "\n".join(context_parts)
                if len(context) > 15000:  # 降低到8000以减少超时风险
                    context = context[:15000] + "...(已截断)"
                
                # 构造完整prompt
                full_prompt = template.format(context=context, question=question)
                
                # 调用对应API
                if use_reasoning:
                    return deepseek_r1_prompt(full_prompt, "") or "未获取到分析结果"
                else:
                    return deepseek_v3_prompt(full_prompt, "") or "未获取到响应"
                    
            except Exception as e:
                # 最终异常处理
                print(f"处理过程中出错: {e}")
                # 直接返回简单回复而不是错误信息
                return f"很抱歉，由于技术原因无法提供详细答案。请稍后再试。"

        return processor

    # 各功能链定义
    def strategy_chain(self):
        """教育策略生成链"""
        template = """基于以下教育策略知识：\n{context}\n\n针对问题"{question}"，请提供2-3条具体、可操作的**分步骤**教育策略建议，并为每条策略起一个简洁的标题。"""
        return self._build_processor(template, 'Multi_query')

    def example_chain(self):
        """教育案例生成链"""
        template = """根据以下案例库：\n{context}\n\n请生成与"{question}"情境最相关的**一个**详细教育案例（不少于200字）。案例需包含以下结构化信息：\n1. **案例标题**: [简洁概括案例]\n2. **情景描述**: [详细说明当时的情况和挑战]\n3. **家长的做法**: [具体描述家长的应对措施或沟通方式]\n4. **最终效果**: [说明该做法带来的结果或影响]"""
        return self._build_processor(template, 'Multi_query')

    def conversation_chain(self):
        """对话改善分析链（使用r1的推理过程）"""
        template = """原始对话片段或情境：{question}\n\n相关理论或知识库信息：{context}\n\n请分析并提供：\n1. **改善后的对话建议**: [针对原始对话，提出具体、温和、有效的替代说法]\n2. **这么说的理由 (请用通俗易懂的语言解释)**: [简单解释为何改善后的说法更有效，例如它如何安抚情绪、促进理解、鼓励合作等，避免直接引用复杂理论名称]"""
        return self._build_processor(template, 'RAG_Fusion', use_reasoning=True)

    def analysis_chain(self):
        """教育问题分析链，旨在生成反思问题"""
        template = """分析以下现象或问题：“{question}”\\n\\n相关教育理论或文献：{context}\\n\\n请基于理论分析该现象可能的**深层原因或模式**，并据此为正在经历此现象的家长**构思2-3个开放式的、引人深思的自我反思问题**，帮助他们进行自我探索。问题应避免指责，例如：“当...时，您内心真正的担忧是什么？”或“您觉得这种模式是如何形成的？”"""
        return self._build_processor(template, 'Multi_query')

    def result(self):
        """优化的最终报告生成函数"""
        self.process_file()
        
        # 使用更可靠的初始化方式
        try:
            strategy_gen = self.strategy_chain()
            example_gen = self.example_chain()
            dialog_improve = self.conversation_chain()
            problem_analysis = self.analysis_chain()
        except Exception as e:
            print(f"初始化处理链失败: {e}")
            return ("初始化失败，请稍后重试", "", "", "", "")
        
        # 检查输入数据格式
        if not isinstance(self.input, dict) or '场景摘要' not in self.input:
            print("输入数据格式不正确")
            return ("无法处理输入数据", "", "", "", "")
        
        # 防止处理过多场景导致超时
        max_scenes = min(3, len(self.input['场景摘要']))
        scenes_to_process = self.input['场景摘要'][:max_scenes]
        
        # 优化：顺序处理而非并发，减少超时风险
        scene_results = []
        for i, scene in enumerate(scenes_to_process):
            try:
                # 提取对话内容
                original_dialog = scene.get('关键细节', ["无详细对话"])
                
                # 生成查询
                strategy_query = f"{scene.get('事件', '')} {scene.get('变化', '')}"
                
                # 设置超时处理
                max_time = 45  # 每个场景最多处理45秒
                start_time = time.time()
                
                # 顺序执行各项分析，有超时保护
                results = {}
                
                # 使用简单的超时控制
                try:
                    if time.time() - start_time < max_time:
                        results['strategy'] = strategy_gen(strategy_query) or "生成策略超时"
                    else:
                        results['strategy'] = "处理时间超出限制，无法生成"
                        
                    if time.time() - start_time < max_time:
                        results['example'] = example_gen(strategy_query) or "生成案例超时"
                    else:
                        results['example'] = "处理时间超出限制，无法生成"
                        
                    if time.time() - start_time < max_time:
                        results['analysis'] = dialog_improve(str(original_dialog)) or "改进分析超时"
                    else:
                        results['analysis'] = "处理时间超出限制，无法生成"
                    
                    if time.time() - start_time < max_time:
                        results['problem'] = problem_analysis(strategy_query) or "问题分析超时"
                    else:
                        results['problem'] = "处理时间超出限制，无法生成"
                except Exception as e:
                    # 处理任何单个分析的失败
                    print(f"场景 {i} 处理部分失败: {e}")
                    if 'strategy' not in results: results['strategy'] = "生成策略失败"
                    if 'example' not in results: results['example'] = "生成案例失败"
                    if 'analysis' not in results: results['analysis'] = "对话分析失败"
                    if 'problem' not in results: results['problem'] = "问题分析失败"
                
                scene_results.append({
                    'idx': i,
                    'original_dialog': original_dialog,
                    'strategy': results.get('strategy', "无法生成策略"),
                    'example': results.get('example', "无法生成案例"),
                    'analysis': results.get('analysis', "无法分析对话"),
                    'problem': results.get('problem', "无法分析问题")
                })
                
            except Exception as e:
                print(f"处理场景 {i} 时出错: {e}")
                scene_results.append({
                    'idx': i,
                    'original_dialog': ["处理出错"],
                    'strategy': "生成策略失败",
                    'example': "获取案例失败",
                    'analysis': "分析失败",
                    'problem': "问题分析失败"
                })
        
        # 格式化最终结果
        report = {
            'strategies': [],
            'examples': [],
            'original_dialogs': [],
            'improved_dialogs': [],
            'problem_analysis': []
        }
        
        # 整理结果
        scene_results.sort(key=lambda x: x['idx'])
        for result in scene_results:
            report['original_dialogs'].append(result['original_dialog'])
            report['strategies'].append(result['strategy'])
            report['examples'].append(result['example'])
            report['improved_dialogs'].append(result['analysis'])
            report['problem_analysis'].append(result['problem'])
        
        # 返回格式化后的报告内容
        return (
            "\n\n".join(report['strategies']),
            "\n\n".join(report['examples']),
            "\n".join([f"场景{i+1}：{d}" for i, d in enumerate(report['original_dialogs'])]),
            "\n\n".join([f"改进方案{i+1}：\n{d}" for i, d in enumerate(report['improved_dialogs'])]),
            "\n\n".join(report['problem_analysis'])
        )
        
    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'executor') and self.executor:
                print("安全关闭线程池...")
                self.executor.shutdown(wait=True, cancel_futures=False)
        except Exception as e:
            print(f"关闭线程池时出错: {e}")
