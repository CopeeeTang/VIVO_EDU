'''
该py文件用于生成每个用户的前端展示文件框架

'''


import time
import json
import asyncio
from typing import List, Type, Dict, Any, Union
from pydantic import BaseModel, ValidationError
import openai
from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import OpenAI, AsyncOpenAI
import os
from functools import partial
import re


# 设置OpenAI API密钥
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

DEEPSEEK_CLIENT = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.siliconflow.cn/v1"
            )

# 创建异步客户端
ASYNC_DEEPSEEK_CLIENT = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.siliconflow.cn/v1"
            )

ZZZ_CLIENT=OpenAI(
            api_key=os.environ.get('ZHIZENGZENG_API_KEY'), 
            base_url="https://api.zhizengzeng.com/v1"
        )
    
ASYNC_ZZZ_CLIENT=AsyncOpenAI(
            api_key=os.environ.get('ZHIZENGZENG_API_KEY'), 
            base_url="https://api.zhizengzeng.com/v1"
        )

# 为各个部分定制的专业prompt
EDUCATION_REPORT_PROMPT = """
你是一位经验丰富的家庭教育顾问，需要为家长创建一份温和且易于理解的家庭教育全景报告。这份报告将用于渲染一个前端页面（part0.html）。
请根据用户提供的对话内容，分析并生成一份严格符合 EducationReport Pydantic 模型结构的 JSON 数据。

**JSON 数据生成要求 (务必严格符合模型字段):**

1.  **`file_id` (str)**: 必须包含从用户内容中提取的文件ID。
2.  **`family_panorama` (object)**:
    *   **`education_environment` (object)**:
        *   **`description` (str)**: 生成一段对当前家庭教育氛围和互动特点的**生动描述** (用于渲染 part0.html 中的 environment-description)。语言应亲切易懂，结合对话中的具体实例。
    *   **`family_portrait` (list of objects)**: 生成一个包含 **3 个对象**的列表，每个对象代表亲子画像的一个方面 (用于渲染 part0.html 中的 portrait-items)。每个对象包含：
        *   **`aspect` (str)**: 固定为 "教育态度和理念", "教育行为和方法", "孩子的表现与状态" 中的一个。
        *   **`description` (str)**: 针对该方面，结合对话实例进行**具体描述**。
3.  **`rainbow_and_shadow` (object)**:
    *   **`advantages` (list of objects)**: 生成一个包含 **5-7 个对象**的列表，每个对象代表一个家庭教育亮点 (用于渲染 part0.html 中的优势部分)。每个对象包含：
        *   **`title` (str)**: **生成一个简洁、概括性的标题** (例如："耐心倾听", "鼓励探索")，此标题将在前端卡片上显示。
        *   **`description` (str)**: 生成 **2-3句话** 的**具体行为描述**，说明优势所在。
    *   **`improvements` (list of objects)**: 生成一个包含 **3-5 个对象**的列表，每个对象代表一个待改进方面 (用于渲染 part0.html 中的待提高部分)。每个对象包含：
        *   **`title` (str)**: **生成一个简洁、概括性的标题** (例如："增加情感回应", "深化思辨引导")，此标题将在前端卡片上显示。
        *   **`description` (str)**: 生成具体、可行的**改进建议描述**，温和指出潜在影响。
        *   **`summary` (object)**: (此字段在 part0.html 未直接显示，但模型需要)
            *   **`content` (str)**: 生成总结性内容。
            *   **`recommendations` (list of str)**: 生成推荐列表。

**请特别注意:**
-   输出必须是**严格符合 EducationReport 模型**的 JSON 对象。
-   所有描述性文字都应使用**友善、支持性**的语气，面向家长，多用"您"。
-   内容应基于提供的对话，具体且有据可依。
"""

COMMUNICATION_ANALYSIS_PROMPT = """
你是一位亲子沟通专家，负责分析家庭对话并提供改进建议。这份报告将用于渲染一个前端页面（part1.html）。
请根据用户提供的对话内容，分析并生成一份严格符合 ContentModel Pydantic 模型结构的 JSON 数据。

**JSON 数据生成要求 (务必严格符合模型字段):**

1.  **`file_id` (str)**: 必须包含从用户内容中提取的文件ID。
2.  **`children_name` (str)**: (此字段在 part1.html 未直接显示，但模型需要，可基于对话推断或设为"孩子")。
3.  **`parent_speeches` (list of objects)**: 从原始对话中提取家长的发言。每个对象包含：
    *   **`type` (str)**: 家长发言的角色或类型 (例如："提问", "命令", "鼓励"，用于 part1.html 的标签)。
    *   **`content` (str)**: 家长的原始发言内容。
4.  **`child_speeches` (list of objects)**: 从原始对话中提取孩子的发言。每个对象包含：
    *   **`content` (str)**: 孩子的原始发言内容。 (注意：模型中 `ChildSpeech` 只有一个 `content` 字段，没有 `type`)
5.  **`improved_speeches` (list of objects)**: 提供改进后的对话建议。每个对象包含：
    *   **`parent` (str)**: 针对原始对话提出的**改进后的家长说法** (用于 part1.html "您或许可以试着这么说" 部分的家长发言)。
    *   **`child` (str)**: 孩子可能的回应 (用于 part1.html "您或许可以试着这么说" 部分的孩子回应)。
6.  **`analysis` (object)**:
    *   **`effective_communication` (list of str)**: (此字段在 part1.html 未直接显示，但模型需要，可留空或简要说明)
    *   **`ineffective_communication` (list of str)**: 提炼原始对话中**沟通不畅或效果不佳**的**关键点** (用于 part1.html "这么说或许不好" 部分，生成一个字符串列表)。
    *   **`reasons` (list of str)**: 针对 `improved_speeches`，**简单解释**为什么改进后的说法更好 (用于 part1.html "为什么要这么说？" 部分，生成一个字符串列表，语言通俗易懂)。

**请特别注意:**
-   输出必须是**严格符合 ContentModel 模型**的 JSON 对象。
-   语气应友善、支持，如同与朋友交谈。
-   改进建议应具体、可行。
-   避免使用专业术语，尤其是解释理由时。
"""

BEHAVIOR_ANALYSIS_PROMPT = """
你是一位经验丰富的家庭教育顾问，需要分析亲子互动中的行为和情绪模式。这份报告将用于渲染一个前端页面（part2.html）。
请根据用户提供的对话内容，分析并生成一份严格符合 BehaviorAnalysisModel Pydantic 模型结构的 JSON 数据。

**JSON 数据生成要求 (务必严格符合模型字段):**

1.  **`file_id` (str)**: 必须包含从用户内容中提取的文件ID。
2.  **`behavior_analysis` (list of Scene objects)**: 提取 **2-3个** 关键互动场景进行分析 (用于渲染 part2.html 的"冲突舞台"部分)。每个 `Scene` 对象包含：
    *   **`title` (str)**: 为场景起一个简洁的标题 (例如："写字拖拉引发的催促")。
    *   **`event` (str)**: 简述该场景的核心事件。
    *   **`changes` (str)**: 描述事件发展及亲子行为、情绪变化的过程。
    *   **`dialogues` (list of Dialogue objects)**: **包含该场景中能够充分展示事件、变化和冲突的、具有代表性的连续对话节选（建议包含至少3-5轮对话交互，如果原始对话足够长）。** 每个 `Dialogue` 对象包含：
        *   `parent_speech` (list of ParentSpeech objects): 每个对象含 `type` (发言类型) 和 `content`。
        *   `child_speech` (list of ChildSpeech objects): 每个对象含 `type` (发言类型) 和 `content`。
    *   **`conflict` (str)**: 分析该场景中存在的主要冲突点。
3.  **`emotion_analysis` (object)**:
    *   **`emotional_journey` (list of EmotionStage objects)**: 追踪互动中的情感变化 (用于渲染 part2.html 的情绪温度计表格)。每个 `EmotionStage` 对象包含：
        *   **`stage` (str)**: 阶段名称 (例如："初始阶段", "发展阶段", "高潮阶段", "结尾阶段")。
        *   **`emotional_state` (str)**: 对该阶段观察到的**具体情绪状态**进行描述 (例如："耐心平和", "略显急躁")。
    *   **`emotional_evaluation` (str)**: 对家长的整体情绪管理能力进行**温和、客观的评估** (用于渲染 part2.html 的情绪评估部分)。
4.  **`reflection` (object)**:
    *   **`questions` (list of str)**: 提供 **3-5个** 温和的、引导性的**反思问题** (用于渲染 part2.html 的心灵反思镜部分)。问题应具有启发性而非指责性。

**请特别注意:**
-   输出必须是**严格符合 BehaviorAnalysisModel 模型**的 JSON 对象。
-   语言应友善、非评判性。
-   聚焦具体行为和可观察的情绪表现。
-   反思问题应引导思考，而非质问。
"""

STRATEGY_CONTENT_PROMPT = """
你是一位亲子关系专家，需要为家长提供实用的亲子沟通策略。这份报告将用于渲染一个前端页面（part3.html）。
请根据用户提供的对话内容，分析并生成一份严格符合 StrategyContentModel Pydantic 模型结构的 JSON 数据。

**JSON 数据生成要求 (务必严格符合模型字段):**

1.  **`file_id` (str)**: 必须包含从用户内容中提取的文件ID。
2.  **`emotional_yoga` (object)**: (用于渲染 part3.html 的"情绪瑜伽"部分)
    *   **`analysis` (str)**: 对家长的情绪反应和可能的触发点进行**分析**。
    *   **`support_tips` (list of str)**: 提供 **5-7个** 具体、实用的**情绪管理技巧或寻求支持的建议** (作为列表项渲染)。
3.  **`tutorial_guide` (object)**: (用于渲染 part3.html 的"解锁宝典"部分)
    *   **`problem_description` (str)**: 描述需要解决的**具体问题或挑战**。
    *   **`strategies` (list of str)**: 提供 **3-5个** 针对该问题的**具体策略** (作为列表项渲染)。
    *   **`implementation_steps` (str)**: 提供实施这些策略的**具体步骤或方法**。
4.  **`parent_examples` (list of ParentExample objects)**: 提供 **1-2个** 相关的案例 (用于渲染 part3.html 的"别人家的家长"部分)。每个 `ParentExample` 对象包含：
    *   **`title` (str)**: 案例的标题。
    *   **`scenario` (str)**: 案例发生的**场景描述**。
    *   **`solution` (str)**: 案例中家长的**解决方案或做法**。
    *   **`outcome` (str)**: 该做法带来的**效果或结果**。

**请特别注意:**
-   输出必须是**严格符合 StrategyContentModel 模型**的 JSON 对象。
-   避免专业术语，使用家长熟悉的日常语言。
-   策略和步骤应具体、可操作。
-   示例应与家长的实际情况相关。
-   语气应支持性和鼓励性。
"""

TUTORING_PORTRAIT_PROMPT = """
你是一位家庭教育分析师，专注于亲子互动尤其是在**作业辅导场景**中的行为模式。
请根据用户提供的家庭概览内容，分析并生成一份严格符合 TutoringPortraitModel Pydantic 模型结构的 JSON 数据，用于在历史回顾页面(history2.html)展示简洁的亲子画像。

**JSON 数据生成要求 (务必严格符合模型字段):**

1.  **`tutoring_portrait` (object)**:
    *   **`parent_tendencies` (list of str)**: 提取或总结 **3-4条** 家长在**辅导作业时**最可能展现的**简洁行为特点或倾向** (例如："倾向于直接指导", "有时缺乏耐心", "注重鼓励", "习惯于监督")。
    *   **`child_tendencies` (list of str)**: 提取或总结 **3-4条** 孩子在**学习或做作业时**最可能展现的**简洁行为特点或倾向** (例如："容易分心", "遇到难题易放弃", "需要陪伴", "能独立完成简单任务")。
2.  **`file_id` (str)**: 必须包含从用户内容中提取的文件ID。

**请特别注意:**
-   输出必须是**严格符合 TutoringPortraitModel 模型**的 JSON 对象。
-   特点描述必须非常**简洁**，每个特点最好是**短语或短句**。
-   聚焦于**作业辅导**这个特定场景。
-   如果信息不足，可以基于普遍情况进行合理推断，但需保持中性客观。
"""

def zip_lists(a, b):
    """自定义zip函数"""
    return zip(a, b)

#=======================对话分析==========================#
# 定义所有Pydantic模型
class ParentSpeech(BaseModel):
    type: str
    content: str

class ChildSpeech(BaseModel):
    content: str

class ImprovedSpeech(BaseModel):
    parent: str
    child: str

class Analysis(BaseModel):
    effective_communication: List[str]
    ineffective_communication: List[str]
    reasons: List[str]

class ContentModel(BaseModel):
    children_name: str
    parent_speeches: List[ParentSpeech]
    child_speeches: List[ChildSpeech]
    improved_speeches: List[ImprovedSpeech]
    analysis: Analysis
    file_id: str

#======================策略分析==========================#

class EmotionalAnalysis(BaseModel):
    analysis: str
    support_tips: List[str]

class TutorialStrategy(BaseModel):
    problem_description: str
    strategies: List[str]  # 每个策略包含标题和具体内容
    implementation_steps: str

class ParentExample(BaseModel):
    title: str
    scenario: str
    solution: str
    outcome: str

class StrategyContentModel(BaseModel):
    emotional_yoga: EmotionalAnalysis
    tutorial_guide: TutorialStrategy
    parent_examples: List[ParentExample]
    file_id: str

#======================家庭教育全景图==========================#

class EducationEnvironment(BaseModel):
    """家庭教育环境描述"""
    description: str

class PortraitItem(BaseModel):
    """家庭画像的每个方面"""
    aspect: str  # 方面
    description: str  # 描述

class FamilyPanorama(BaseModel):
    """家庭教育全景图"""
    education_environment: EducationEnvironment
    family_portrait: List[PortraitItem]

class AdvantageItem(BaseModel):
    """优势项"""
    title: str
    description: str

class ImprovementItem(BaseModel):
    """待改进项"""
    title: str
    description: str

class Summary(BaseModel):
    """总结与建议"""
    content: str
    recommendations: List[str]

class RainbowAndShadow(BaseModel):
    """彩虹与阴霾部分"""
    advantages: List[AdvantageItem]
    improvements: List[ImprovementItem]
    summary: Summary

class EducationReport(BaseModel):
    """教育报告完整结构"""
    family_panorama: FamilyPanorama
    rainbow_and_shadow: RainbowAndShadow
    file_id: str

#======================行为分析==========================#

class ParentSpeech(BaseModel):
    type: str
    content: str

class ChildSpeech(BaseModel):
    type: str
    content: str

class Dialogue(BaseModel):
    parent_speech: list[ParentSpeech]
    child_speech: list[ChildSpeech]

class Scene(BaseModel):
    title: str  # 场景标题
    event: str  # 事件描述
    changes: str  # 变化过程
    dialogues: List[Dialogue]  # 对话内容列表
    conflict: str  # 存在的冲突

class EmotionStage(BaseModel):
    stage: str  # 阶段，如'初始阶段'
    emotional_state: str  # 情感状态

class EmotionAnalysis(BaseModel):
    emotional_journey: List[EmotionStage]  # 情感历程
    emotional_evaluation: str  # 情绪评估

class Reflection(BaseModel):
    questions: List[str]  # 反思问题列表

class BehaviorAnalysisModel(BaseModel):
    behavior_analysis: List[Scene]  # 行为分析
    emotion_analysis: EmotionAnalysis  # 情绪分析
    reflection: Reflection  # 反思问题
    file_id: str

#======================新增：辅导场景亲子画像==========================#

class TutoringPortrait(BaseModel):
    """用于 history2.html 的简洁亲子画像模型"""
    parent_tendencies: List[str]  # 家长在辅导场景下的特点列表 (3-4条)
    child_tendencies: List[str]   # 孩子在学习/作业场景下的特点列表 (3-4条)

class TutoringPortraitModel(BaseModel):
    """包含画像和 file_id 的完整模型"""
    tutoring_portrait: TutoringPortrait
    file_id: str

def parse_content(content: str, model_class: Type[BaseModel]) -> BaseModel:
    """
    使用 OpenAI API 解析内容并转换为指定的 Pydantic 模型实例。

    参数:
    - content (str): 输入的上下文内容。
    - model_class (Type[BaseModel]): 目标 Pydantic 模型类。

    返回:
    - BaseModel: 解析后的模型实例。
    """
    start_time = time.time()
    
    # 根据模型类型选择合适的prompt
    system_prompt = "你是一个结构化数据生成器。请将用户输入的家庭教育相关内容转换为预定义的JSON格式，以中文输出，且符合指定的Pydantic模型。"
    
    if model_class == EducationReport:
        system_prompt = EDUCATION_REPORT_PROMPT
    elif model_class == ContentModel:
        system_prompt = COMMUNICATION_ANALYSIS_PROMPT
    elif model_class == BehaviorAnalysisModel:
        system_prompt = BEHAVIOR_ANALYSIS_PROMPT
    elif model_class == StrategyContentModel:
        system_prompt = STRATEGY_CONTENT_PROMPT
    elif model_class == TutoringPortraitModel:
        system_prompt = TUTORING_PORTRAIT_PROMPT
        
    response = ASYNC_ZZZ_CLIENT.beta.chat.completions.parse(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        temperature=0.1,
        response_format=model_class
    )
    data = response.choices[0].message.parsed
    try:
        result = model_class.parse_obj(data)
        end_time = time.time()
        print(f"解析耗时: {end_time - start_time:.2f}秒")
        return result
    except Exception as e:
        print("JSON解析错误:", e)
        print("返回的内容:", data)
        raise ValueError(f"JSON解析错误: {e}")

# 修改异步解析函数，修复 JSON 解析错误
async def parse_content_async(content: str, model_class: Type[BaseModel]) -> BaseModel:
    """
    异步使用 OpenAI API 解析内容并转换为指定的 Pydantic 模型实例。
    """
    start_time = time.time()
    try:
        system_prompt = "你是一个结构化数据生成器。请将用户输入的内容转换为预定义的JSON格式，输出请保持中文输出，且符合指定的Pydantic模型。请确保返回的是一个有效的JSON对象。"
        
        if model_class == EducationReport:
            system_prompt = EDUCATION_REPORT_PROMPT
        elif model_class == ContentModel:
            system_prompt = COMMUNICATION_ANALYSIS_PROMPT
        elif model_class == BehaviorAnalysisModel:
            system_prompt = BEHAVIOR_ANALYSIS_PROMPT
        elif model_class == StrategyContentModel:
            system_prompt = STRATEGY_CONTENT_PROMPT
        elif model_class == TutoringPortraitModel:
            system_prompt = TUTORING_PORTRAIT_PROMPT

        response = await ASYNC_ZZZ_CLIENT.beta.chat.completions.parse(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            temperature=0.1,
            response_format=model_class,
            timeout=300
        )
        
        data = response.choices[0].message.parsed
        try:
            result = model_class.parse_obj(data)
            end_time = time.time()
            print(f"异步解析耗时: {end_time - start_time:.2f}秒")
            return result
        except ValidationError as e:
            print(f"模型验证错误: {e}")
            # 为新模型添加回退逻辑
            if model_class == TutoringPortraitModel:
                return TutoringPortraitModel(
                    tutoring_portrait=TutoringPortrait(
                        parent_tendencies=["数据处理过程中出现错误"],
                        child_tendencies=["数据处理过程中出现错误"]
                    ),
                    file_id=content.split("file_id=")[-1] if "file_id=" in content else ""
                )
            elif model_class == EducationReport:
                return EducationReport(
                    family_panorama=FamilyPanorama(
                        education_environment=EducationEnvironment(description="数据处理过程中出现错误"),
                        family_portrait=[]
                    ),
                    rainbow_and_shadow=RainbowAndShadow(
                        advantages=[], 
                        improvements=[],
                        summary=Summary(content="解析过程中出现错误，请稍后重试", recommendations=[])
                    ),
                    file_id=content.split("file_id=")[-1] if "file_id=" in content else ""
                )
            elif model_class == ContentModel:
                return ContentModel(
                    children_name="未知",
                    parent_speeches=[],
                    child_speeches=[],
                    improved_speeches=[],
                    analysis=Analysis(
                        effective_communication=[],
                        ineffective_communication=[],
                        reasons=[]
                    ),
                    file_id=content.split("file_id=")[-1] if "file_id=" in content else ""
                )
            elif model_class == StrategyContentModel:
                return StrategyContentModel(
                    emotional_yoga=EmotionalAnalysis(
                        analysis="数据处理过程中出现错误",
                        support_tips=[]
                    ),
                    tutorial_guide=TutorialStrategy(
                        problem_description="",
                        strategies=[],
                        implementation_steps=""
                    ),
                    parent_examples=[],
                    file_id=content.split("file_id=")[-1] if "file_id=" in content else ""
                )
            elif model_class == BehaviorAnalysisModel:
                return BehaviorAnalysisModel(
                    behavior_analysis=[],
                    emotion_analysis=EmotionAnalysis(
                        emotional_journey=[],
                        emotional_evaluation="数据处理过程中出现错误"
                    ),
                    file_id=content.split("file_id=")[-1] if "file_id=" in content else ""
                )
            else:
                raise ValueError(f"不支持的模型类型: {model_class.__name__}")
    except Exception as e:
        print(f"异步解析过程中发生错误: {e}")
        file_id = ""
        try:
            if "file_id=" in content:
                file_id = content.split("file_id=")[-1].strip()
        except:
            pass
        
        # 为新模型添加回退逻辑
        if model_class == TutoringPortraitModel:
            return TutoringPortraitModel(
                tutoring_portrait=TutoringPortrait(
                    parent_tendencies=["数据处理过程中出现错误"],
                    child_tendencies=["数据处理过程中出现错误"]
                ),
                file_id=file_id
            )
        elif model_class == EducationReport:
            return EducationReport(
                family_panorama=FamilyPanorama(
                    education_environment=EducationEnvironment(description="数据处理过程中出现错误"),
                    family_portrait=[]
                ),
                rainbow_and_shadow=RainbowAndShadow(
                    advantages=[], 
                    improvements=[],
                    summary=Summary(content="解析过程中出现错误，请稍后重试", recommendations=[])
                ),
                file_id=file_id
            )
        elif model_class == ContentModel:
            return ContentModel(
                children_name="未知",
                parent_speeches=[],
                child_speeches=[],
                improved_speeches=[],
                analysis=Analysis(
                    effective_communication=[],
                    ineffective_communication=[],
                    reasons=[]
                ),
                file_id=file_id
            )
        elif model_class == StrategyContentModel:
            return StrategyContentModel(
                emotional_yoga=EmotionalAnalysis(
                    analysis="数据处理过程中出现错误",
                    support_tips=[]
                ),
                tutorial_guide=TutorialStrategy(
                    problem_description="",
                    strategies=[],
                    implementation_steps=""
                ),
                parent_examples=[],
                file_id=file_id
            )
        elif model_class == BehaviorAnalysisModel:
            return BehaviorAnalysisModel(
                behavior_analysis=[],
                emotion_analysis=EmotionAnalysis(
                    emotional_journey=[],
                    emotional_evaluation="数据处理过程中出现错误"
                ),
                file_id=file_id
            )
        else:
            raise ValueError(f"无法创建回退对象: {model_class.__name__}")

def generate_html(context: BaseModel, template_name: str, output_path: str):
    """
    使用 Jinja2 模板生成 HTML 文件。
    """
    template_path = os.environ.get('TEMPLATE_PATH', 'templates')
    env = Environment(
        loader=FileSystemLoader(searchpath=template_path),
        autoescape=select_autoescape(['html', 'xml'])
    )
    env.filters['zip'] = zip_lists
    try:
        template = env.get_template(template_name)
        rendered_html = ""
        
        # 根据不同的模型类型准备渲染上下文
        if isinstance(context, ContentModel):
            max_length = max(len(context.parent_speeches), len(context.child_speeches))
            render_context = context.dict()
            render_context['max_length'] = max_length
        elif isinstance(context, StrategyContentModel):
            render_context = context.dict()
        elif isinstance(context, EducationReport):
            # EducationReport 只用于 part0.html
            if template_name == 'part0.html':
                render_context = context.dict()
            else:
                 raise TypeError(f"EducationReport 不适用于模板 {template_name}")
        elif isinstance(context, BehaviorAnalysisModel):
            render_context = context.dict()
        elif isinstance(context, TutoringPortraitModel): # 新增处理
            # TutoringPortraitModel 只用于 history2.html
            if template_name == 'history2.html':
                # context 已经是 TutoringPortraitModel 类型，直接使用
                render_context = context.dict() 
                # 确保 tutoring_portrait 在上下文中
                if 'tutoring_portrait' not in render_context:
                    # 如果 TutoringPortraitModel 结构变化，需要调整
                    # 假设 context.tutoring_portrait 存在
                    render_context['tutoring_portrait'] = context.tutoring_portrait.dict()
            else:
                raise TypeError(f"TutoringPortraitModel 不适用于模板 {template_name}")
        else:
            raise TypeError(f"不支持的模型类型: {type(context)}")

        rendered_html = template.render(**render_context)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)
        print(f"HTML文件已生成：{output_path}")
        return rendered_html
    except Exception as e:
        print(f"模板生成失败 ({template_name}): {e}")
        raise RuntimeError(f"模板生成失败 ({template_name}): {e}")

async def generate_html_async(context: BaseModel, template_name: str, output_path: str):
    """
    异步使用 Jinja2 模板生成 HTML 文件。
    """
    loop = asyncio.get_running_loop()
    try:
        # 注意：这里仍然调用同步的 generate_html，但将其放在线程池中执行
        # 如果 generate_html 本身非常 CPU 密集，这可能不是最优的异步方式
        # 但对于 IO 密集或混合型任务是常见的做法
        rendered_html = await loop.run_in_executor(
            None, 
            partial(generate_html, context, template_name, output_path)
        )
        return rendered_html
    except Exception as e:
        print(f"异步模板生成失败: {e}")
        raise RuntimeError(f"异步模板生成失败: {e}")

def generate_html_from_context(content: str, model_class: Type[BaseModel], template_name: str, output_path: str) -> str:
    """
    整合内容解析和HTML生成的函数。

    参数:
    - content (str): 输入的上下文内容。
    - model_class (Type[BaseModel]): 预定义的Pydantic模型类。
    - template_name (str): 使用的HTML模板名称。
    - output_path (str): 输出HTML文件的路径。

    返回:
    - str: 生成的HTML内容。
    """
    # 解析内容
    context = parse_content(content, model_class)
    
    # 生成HTML
    generate_html(context, template_name, output_path)
    
    # 读取并返回生成的HTML内容
    with open(output_path, 'r', encoding='utf-8') as f:
        return f.read()

# 添加异步版本的整合函数
async def generate_html_from_context_async(content: str, model_class: Type[BaseModel], template_name: str, output_path: str) -> str:
    """
    异步整合内容解析和HTML生成的函数。

    参数:
    - content (str): 输入的上下文内容。
    - model_class (Type[BaseModel]): 预定义的Pydantic模型类。
    - template_name (str): 使用的HTML模板名称。
    - output_path (str): 输出HTML文件的路径。

    返回:
    - str: 生成的HTML内容。
    """
    try:
        # 异步解析内容
        context = await parse_content_async(content, model_class)
        
        # 异步生成HTML
        await generate_html_async(context, template_name, output_path)
        
        # 读取并返回生成的HTML内容
        async def read_file():
            loop = asyncio.get_running_loop()
            try:
                return await loop.run_in_executor(
                    None,
                    lambda: open(output_path, 'r', encoding='utf-8').read()
                )
            except Exception as e:
                print(f"读取生成的HTML文件失败: {e}")
                return ""
                
        return await read_file()
    except Exception as e:
        print(f"异步生成HTML出错: {e}")
        raise e

# 优化异步多报告生成函数
async def generate_multiple_html_async(contents_info: List[Dict[str, Any]]) -> List[str]:
    """并行生成多个HTML文件，并提供健壮的错误处理"""
    results = []
    
    # 创建单独的任务列表，添加超时处理
    tasks = []
    for info in contents_info:
        # 为每个任务添加超时
        task = asyncio.create_task(
            asyncio.wait_for(
                generate_html_from_context_async(
                    content=info['content'],
                    model_class=info['model_class'],
                    template_name=info['template_name'],
                    output_path=info['output_path']
                ),
                timeout=240  # 3分钟超时
            )
        )
        tasks.append((task, info))
    
    # 逐个处理任务
    for task, info in tasks:
        try:
            # 等待任务完成
            result = await task
            results.append(result)
            print(f"异步生成报告成功: {info['output_path']}")
        except asyncio.TimeoutError:
            print(f"报告生成超时: {info['output_path']}")
            # 超时时尝试同步方法
            try:
                print(f"使用同步方法重试: {info['output_path']}")
                sync_result = generate_html_from_context(
                    content=info['content'],
                    model_class=info['model_class'],
                    template_name=info['template_name'],
                    output_path=info['output_path']
                )
                results.append(sync_result)
                print(f"同步重试成功: {info['output_path']}")
            except Exception as sync_e:
                # 同步方法也失败时，生成错误页面
                print(f"同步重试失败: {sync_e}")
                results.append(_generate_error_page(info['output_path']))
        except Exception as e:
            print(f"异步生成报告失败: {info['output_path']}, 错误: {e}")
            # 异步失败时尝试同步方法
            try:
                print(f"使用同步方法重试: {info['output_path']}")
                sync_result = generate_html_from_context(
                    content=info['content'],
                    model_class=info['model_class'],
                    template_name=info['template_name'],
                    output_path=info['output_path']
                )
                results.append(sync_result)
                print(f"同步重试成功: {info['output_path']}")
            except Exception as sync_e:
                # 同步方法也失败时，生成错误页面
                print(f"同步重试失败: {sync_e}")
                results.append(_generate_error_page(info['output_path']))
    
    return results

# 辅助函数：生成错误页面
def _generate_error_page(output_path: str) -> str:
    """生成简单的错误页面，确保页面渲染不会完全失败"""
    error_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>报告生成失败</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
            .error-container {{ 
                max-width: 800px;
                margin: 50px auto;
                padding: 30px;
                border-radius: 10px;
                background-color: #fff;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                text-align: center;
            }}
            h1 {{ color: #e74c3c; margin-bottom: 20px; }}
            p {{ line-height: 1.6; margin-bottom: 15px; }}
            .action-button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="error-container">
            <h1>报告生成处理中</h1>
            <p>系统正在处理您的数据，请稍后刷新页面查看完整报告。</p>
            <p>如果问题持续存在，请联系系统管理员获取帮助。</p>
            <a href="javascript:location.reload()" class="action-button">刷新页面</a>
        </div>
    </body>
    </html>
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(error_html)
        print(f"已生成错误页面: {output_path}")
    except Exception as write_e:
        print(f"写入错误页面失败: {write_e}")
    
    return error_html