# 家庭教育AI助手 - 模块规范与功能分布

## 项目概述

本项目是一个家庭教育AI辅助系统，用于分析家长辅导孩子学习的音频对话，提取亲子互动特征，并根据分析结果生成个性化教育策略指导。

系统采用模块化设计，将复杂的音频分析流程分解为以下几个主要环节：

1. **音频预处理**: 转录与文本标准化
2. **亲子画像**: 冲突和行为分析
3. **场景重建**: 生成详细场景描述
4. **知识检索**: 基于场景检索相关教育知识
5. **策略生成**: 整合信息生成干预策略

## 模块详细设计

### 1. API模块 (api.py)

**职责**:
- 统一管理所有大模型API和语音API的调用
- 提供错误处理和重试机制
- 支持异步调用

**主要接口**:
```python
async def call_llm_async(client_type, model, messages, **kwargs) -> str:
    """异步调用LLM API，统一处理错误和重试"""
    pass

async def transcribe_audio_async(audio_path, **kwargs) -> dict:
    """异步调用语音转写API"""
    pass

def call_llm(client_type, model, messages, **kwargs) -> str:
    """同步调用LLM API"""
    pass

def transcribe_audio(audio_path, **kwargs) -> dict:
    """同步调用语音转写API"""
    pass
```

**支持的API类型**:
- Azure OpenAI API
- 智增增 API (gpt-4o)
- 火山引擎 API (deepseek-chat)
- 讯飞转写 API

### 2. 预处理模块 (preprocess.py)

**职责**:
- 音频文件的转写和标准化
- 提取日期信息
- 分段对齐和清洗

**主要接口**:
```python
async def process_audio(audio_path) -> List[Dict]:
    """异步处理音频文件，返回标准化的转写结果"""
    pass

def extract_date_from_filename(filename) -> str:
    """从文件名中提取日期，格式化为YYYYMMDD"""
    pass

def normalize_transcript(raw_transcript) -> List[Dict]:
    """标准化转写格式，统一为[{id, speaker, text}]结构"""
    pass
```

### 3. 亲子画像模块 (role_model.py)

**职责**:
- 分析冲突场景
- 分析行为特征
- 保存分析结果到数据库

**主要接口**:
```python
async def analyze_transcripts_for_profile(transcripts, date, file_id, analysis_id) -> Tuple[ConflictAnalysisOutput, BehaviorAnalysisOutput]:
    """分析转写内容，提取冲突和行为特征"""
    pass

async def save_analysis_results_to_db(conflict_result, behavior_result, file_id, analysis_id):
    """将分析结果保存至数据库"""
    pass
```

**数据模型**:
- `ConflictSceneData`: 冲突场景数据模型
- `BehaviorSceneData`: 行为场景数据模型
- `ConflictAnalysisOutput`: 冲突分析结果
- `BehaviorAnalysisOutput`: 行为分析结果

### 4. 场景重建模块 (Scenery.py)

**职责**:
- 基于转写和亲子画像，重建详细的教育场景
- 提供场景总结和分析
- 改进对话内容

**主要接口**:
```python
async def rebuild_scenery(transcript, conflict_result, behavior_result) -> Dict:
    """重建教育场景，生成详细描述和分析"""
    pass
```

**输出结构**:
```
{
  "scenes": [
    {
      "scene_id": 1,
      "summary": "场景概述",
      "original_dialogue": "原始对话片段",
      "improved_dialogue": "改进后的对话",
      "analysis": "场景分析",
    }
  ]
}
```

### 5. 知识检索模块 (RAG.py)

**职责**:
- 维护教育知识库
- 基于场景检索相关知识
- 提供解决方案和案例

**主要接口**:
```python
async def retrieve_knowledge(scenery_result) -> Dict:
    """基于场景检索相关教育知识"""
    pass
```

**输出结构**:
```
{
  "guidance": ["针对场景的指导建议1", "指导建议2", ...],
  "examples": ["相关案例1", "相关案例2", ...],
  "original_dialogue": "原始对话片段",
  "improved_dialogue": "改进后的对话示例",
  "reflection_questions": ["反思问题1", "反思问题2", ...]
}
```

### 6. 策略生成模块 (Strategy.py)

**职责**:
- 整合所有分析结果
- 生成个性化教育干预策略
- 提供多维度教育建议

**主要接口**:
```python
async def generate_strategy(transcript, conflict_result, behavior_result, scenery_result, knowledge_result) -> Dict:
    """生成完整的教育干预策略"""
    pass
```

**输出结构**:
```
{
  "family_overview": "家庭教育概览",
  "conversation_analysis": "对话分析",
  "emotion_analysis": "情绪分析",
  "reflection_questions": ["反思问题1", "反思问题2", ...],
  "conflict_analysis": "冲突分析",
  "behavior_analysis": "行为分析",
  "strategy_generation": "详细策略建议"
}
```

### 7. 任务流程模块 (task_async.py)

**职责**:
- 协调各模块工作流程
- 处理异步任务
- 管理任务状态和结果

**主要接口**:
```python
async def process_audio_analysis_task(audio_path, task_id) -> Dict:
    """处理完整的音频分析任务"""
    pass
```

## 工作流程

1. **任务接收**:
   - 系统接收音频文件和任务参数
   - 创建任务记录

2. **音频预处理**:
   - 调用转写API获取对话文本
   - 提取日期信息
   - 标准化转写格式

3. **亲子画像分析**:
   - 并行执行冲突分析和行为分析
   - 保存分析结果到数据库

4. **场景重建**:
   - 基于转写和亲子画像重建详细场景
   - 生成场景总结和改进对话

5. **知识检索**:
   - 根据场景检索相关教育知识和案例
   - 提供反思问题

6. **策略生成**:
   - 整合所有分析结果
   - 生成完整的干预策略报告

7. **结果返回**:
   - 返回分析结果
   - 更新任务状态

## 模块间依赖关系

- **音频预处理** 依赖 **API模块**
- **亲子画像分析** 依赖 **API模块**、**预处理模块**
- **场景重建** 依赖 **API模块**、**亲子画像分析**
- **知识检索** 依赖 **API模块**、**场景重建**
- **策略生成** 依赖 **API模块**、**亲子画像分析**、**场景重建**、**知识检索**
- **任务流程** 依赖 所有其他模块

## 扩展和维护计划

### 短期改进

1. 完善错误处理机制
2. 添加更多单元测试
3. 优化模型提示词

### 中期规划

1. 支持更多音频格式和转写API
2. 扩展知识库内容
3. 实现用户反馈和策略调优机制

### 长期目标

1. 开发实时分析功能
2. 添加多模态分析支持(音频+视频)
3. 构建个性化推荐系统

## 测试计划

使用 `test_flow.py` 测试整个流程的正确性和稳定性，该测试脚本:

1. 模拟完整分析流程
2. 提供详细日志输出
3. 保存中间结果用于检查
4. 支持模块独立测试 