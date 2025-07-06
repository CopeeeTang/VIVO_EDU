# -*- coding: utf-8 -*-
"""
增强的数据库模型
匹配新的算法输出结构
"""

from .extensions import db
from datetime import datetime
import enum
import json
from sqlalchemy.dialects.mysql import CHAR, JSON
from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SAEnum, Text, Float
from sqlalchemy.orm import relationship
from typing import List, Dict, Any


# 亲子画像分析结果模型
class ParentChildProfile(db.Model):
    __tablename__ = 'parent_child_profiles'
    
    profile_id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, ForeignKey('analysis_results.analysis_id', ondelete='CASCADE'), nullable=False)
    
    # 教养方式分析
    parenting_style = db.Column(db.Text, nullable=True)  # JSON字符串
    
    # 情感分析
    sentiment_analysis = db.Column(db.Text, nullable=True)  # JSON字符串
    
    # 沟通模式分析
    communication_patterns = db.Column(db.Text, nullable=True)  # JSON字符串
    
    # 主题分析
    topic_analysis = db.Column(db.Text, nullable=True)  # JSON字符串
    
    # 冲突分析（简版）
    conflict_analysis = db.Column(db.Text, nullable=True)  # JSON字符串
    
    # 优势劣势分析
    advantage_analysis = db.Column(db.Text, nullable=True)  # JSON字符串
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    analysis_result = relationship('AnalysisResult', back_populates='parent_child_profile')
    
    def set_parenting_style(self, data: Dict[str, Any]):
        """设置教养方式数据"""
        self.parenting_style = json.dumps(data, ensure_ascii=False) if data else None
    
    def get_parenting_style(self) -> Dict[str, Any]:
        """获取教养方式数据"""
        return json.loads(self.parenting_style) if self.parenting_style else {}
    
    def set_sentiment_analysis(self, data: Dict[str, Any]):
        """设置情感分析数据"""
        self.sentiment_analysis = json.dumps(data, ensure_ascii=False) if data else None
    
    def get_sentiment_analysis(self) -> Dict[str, Any]:
        """获取情感分析数据"""
        return json.loads(self.sentiment_analysis) if self.sentiment_analysis else {}
    
    def set_communication_patterns(self, data: Dict[str, Any]):
        """设置沟通模式数据"""
        self.communication_patterns = json.dumps(data, ensure_ascii=False) if data else None
    
    def get_communication_patterns(self) -> Dict[str, Any]:
        """获取沟通模式数据"""
        return json.loads(self.communication_patterns) if self.communication_patterns else {}
    
    def set_topic_analysis(self, data: Dict[str, Any]):
        """设置主题分析数据"""
        self.topic_analysis = json.dumps(data, ensure_ascii=False) if data else None
    
    def get_topic_analysis(self) -> Dict[str, Any]:
        """获取主题分析数据"""
        return json.loads(self.topic_analysis) if self.topic_analysis else {}
    
    def set_conflict_analysis(self, data: Dict[str, Any]):
        """设置冲突分析数据"""
        self.conflict_analysis = json.dumps(data, ensure_ascii=False) if data else None
    
    def get_conflict_analysis(self) -> Dict[str, Any]:
        """获取冲突分析数据"""
        return json.loads(self.conflict_analysis) if self.conflict_analysis else {}
    
    def set_advantage_analysis(self, data: Dict[str, Any]):
        """设置优势劣势分析数据"""
        self.advantage_analysis = json.dumps(data, ensure_ascii=False) if data else None
    
    def get_advantage_analysis(self) -> Dict[str, Any]:
        """获取优势劣势分析数据"""
        return json.loads(self.advantage_analysis) if self.advantage_analysis else {}


# 场景重建结果模型
class SceneryRebuild(db.Model):
    __tablename__ = 'scenery_rebuilds'
    
    scenery_id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, ForeignKey('analysis_results.analysis_id', ondelete='CASCADE'), nullable=False)
    
    # 场景数量
    scene_count = db.Column(db.Integer, nullable=False, default=0)
    
    # 场景摘要（JSON格式存储所有场景）
    scene_summaries = db.Column(db.Text, nullable=True)  # JSON字符串
    
    # 处理状态
    processing_status = db.Column(db.String(50), default='completed')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    analysis_result = relationship('AnalysisResult', back_populates='scenery_rebuild')
    scene_details = relationship('SceneDetail', back_populates='scenery_rebuild', cascade='all, delete-orphan')
    
    def set_scene_summaries(self, data: Dict[str, Any]):
        """设置场景摘要数据"""
        self.scene_summaries = json.dumps(data, ensure_ascii=False) if data else None
        if data and '场景数量' in data:
            self.scene_count = data['场景数量']
    
    def get_scene_summaries(self) -> Dict[str, Any]:
        """获取场景摘要数据"""
        return json.loads(self.scene_summaries) if self.scene_summaries else {}


# 场景详情模型
class SceneDetail(db.Model):
    __tablename__ = 'scene_details'
    
    detail_id = db.Column(db.Integer, primary_key=True)
    scenery_id = db.Column(db.Integer, ForeignKey('scenery_rebuilds.scenery_id', ondelete='CASCADE'), nullable=False)
    
    # 场景ID（在单次分析中的ID）
    scene_id = db.Column(db.Integer, nullable=False)
    
    # 事件描述
    event_description = db.Column(db.Text, nullable=True)
    
    # 变化过程
    change_process = db.Column(db.Text, nullable=True)
    
    # 关键细节（JSON数组）
    key_details = db.Column(db.Text, nullable=True)  # JSON字符串
    
    # 时间范围
    time_range = db.Column(db.String(100), nullable=True)
    
    # 参与者（JSON数组）
    participants = db.Column(db.Text, nullable=True)  # JSON字符串
    
    # 情感基调
    emotional_tone = db.Column(db.String(50), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    scenery_rebuild = relationship('SceneryRebuild', back_populates='scene_details')
    
    def set_key_details(self, details: List[str]):
        """设置关键细节"""
        self.key_details = json.dumps(details, ensure_ascii=False) if details else None
    
    def get_key_details(self) -> List[str]:
        """获取关键细节"""
        return json.loads(self.key_details) if self.key_details else []
    
    def set_participants(self, participants: List[str]):
        """设置参与者"""
        self.participants = json.dumps(participants, ensure_ascii=False) if participants else None
    
    def get_participants(self) -> List[str]:
        """获取参与者"""
        return json.loads(self.participants) if self.participants else []


# 知识库检索结果模型
class KnowledgeBaseResult(db.Model):
    __tablename__ = 'knowledge_base_results'
    
    kb_result_id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, ForeignKey('analysis_results.analysis_id', ondelete='CASCADE'), nullable=False)
    
    # 查询文本
    query_text = db.Column(db.Text, nullable=True)
    
    # 搜索类型
    search_type = db.Column(db.String(50), nullable=True)  # vector_search, fallback_search, multi_query_search
    
    # 搜索结果总数
    total_results = db.Column(db.Integer, default=0)
    
    # 搜索结果（JSON格式）
    search_results = db.Column(db.Text, nullable=True)  # JSON字符串
    
    # 生成的教育建议
    educational_advice = db.Column(db.Text, nullable=True)
    
    # 建议生成状态
    advice_status = db.Column(db.String(50), default='pending')  # pending, generated, failed
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    analysis_result = relationship('AnalysisResult', back_populates='knowledge_base_result')
    
    def set_search_results(self, data: Dict[str, Any]):
        """设置搜索结果数据"""
        self.search_results = json.dumps(data, ensure_ascii=False) if data else None
        if data:
            self.total_results = data.get('total', 0)
            self.search_type = data.get('search_type', 'unknown')
    
    def get_search_results(self) -> Dict[str, Any]:
        """获取搜索结果数据"""
        return json.loads(self.search_results) if self.search_results else {}


# 干预策略结果模型
class InterventionStrategy(db.Model):
    __tablename__ = 'intervention_strategies'
    
    strategy_id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, ForeignKey('analysis_results.analysis_id', ondelete='CASCADE'), nullable=False)
    
    # 策略内容
    strategy_content = db.Column(db.Text, nullable=True)
    
    # 策略类型
    strategy_type = db.Column(db.String(100), nullable=True)  # 沟通策略、行为指导、学习支持等
    
    # 优先级
    priority = db.Column(db.String(20), nullable=True)  # high, medium, low
    
    # 适用场景
    applicable_scenarios = db.Column(db.Text, nullable=True)  # JSON字符串
    
    # 预期效果
    expected_outcomes = db.Column(db.Text, nullable=True)
    
    # 实施建议
    implementation_suggestions = db.Column(db.Text, nullable=True)
    
    # 注意事项
    precautions = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    analysis_result = relationship('AnalysisResult', back_populates='intervention_strategy')
    
    def set_applicable_scenarios(self, scenarios: List[str]):
        """设置适用场景"""
        self.applicable_scenarios = json.dumps(scenarios, ensure_ascii=False) if scenarios else None
    
    def get_applicable_scenarios(self) -> List[str]:
        """获取适用场景"""
        return json.loads(self.applicable_scenarios) if self.applicable_scenarios else []


# 扩展现有的AnalysisResult模型（需要在现有模型中添加这些关系）
"""
需要在app/models.py的AnalysisResult类中添加以下关系：

# 新增关系
parent_child_profile = relationship('ParentChildProfile', back_populates='analysis_result', uselist=False, cascade='all, delete-orphan')
scenery_rebuild = relationship('SceneryRebuild', back_populates='analysis_result', uselist=False, cascade='all, delete-orphan')
knowledge_base_result = relationship('KnowledgeBaseResult', back_populates='analysis_result', uselist=False, cascade='all, delete-orphan')
intervention_strategy = relationship('InterventionStrategy', back_populates='analysis_result', uselist=False, cascade='all, delete-orphan')
"""

# 分析任务状态模型
class AnalysisTask(db.Model):
    __tablename__ = 'analysis_tasks'
    
    task_id = db.Column(db.String(50), primary_key=True)
    file_id = db.Column(db.String(36), ForeignKey('audio_files.file_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, ForeignKey('users.user_id'), nullable=False)
    
    # 任务状态
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed
    
    # 当前步骤
    current_step = db.Column(db.String(100), nullable=True)
    
    # 总步骤数
    total_steps = db.Column(db.Integer, default=6)
    
    # 已完成步骤数
    completed_steps = db.Column(db.Integer, default=0)
    
    # 进度百分比
    progress_percentage = db.Column(db.Integer, default=0)
    
    # 错误信息
    error_message = db.Column(db.Text, nullable=True)
    
    # 开始时间
    started_at = db.Column(db.DateTime, nullable=True)
    
    # 完成时间
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # 处理时长（秒）
    processing_duration = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def update_progress(self, step_name: str, completed_steps: int):
        """更新任务进度"""
        self.current_step = step_name
        self.completed_steps = completed_steps
        self.progress_percentage = int((completed_steps / self.total_steps) * 100)
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self):
        """标记任务完成"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100
        if self.started_at:
            self.processing_duration = (self.completed_at - self.started_at).total_seconds()
    
    def mark_failed(self, error_message: str):
        """标记任务失败"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.processing_duration = (self.completed_at - self.started_at).total_seconds()


# 系统配置模型
class SystemConfig(db.Model):
    __tablename__ = 'system_configs'
    
    config_id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)
    config_value = db.Column(db.Text, nullable=True)
    config_type = db.Column(db.String(20), nullable=False, default='string')  # string, json, int, float, bool
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_value(self):
        """根据类型返回配置值"""
        if self.config_type == 'json':
            return json.loads(self.config_value) if self.config_value else {}
        elif self.config_type == 'int':
            return int(self.config_value) if self.config_value else 0
        elif self.config_type == 'float':
            return float(self.config_value) if self.config_value else 0.0
        elif self.config_type == 'bool':
            return self.config_value.lower() in ('true', '1', 'yes') if self.config_value else False
        else:
            return self.config_value
    
    def set_value(self, value):
        """设置配置值"""
        if self.config_type == 'json':
            self.config_value = json.dumps(value, ensure_ascii=False)
        else:
            self.config_value = str(value) 