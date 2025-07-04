# 导入所需的模块
from .extensions import db
from datetime import datetime
import enum
# 音频文件模型
import uuid
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from typing import List


# 用户模型
class User(db.Model):
    __tablename__ = 'users'  # 改为小写
    user_id = db.Column(db.Integer, primary_key=True)  # 用户ID，主键
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)  # 用户名，唯一且不可为空
    password = db.Column(db.String(255), nullable=False)  # 密码，不可为空
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    last_login = db.Column(db.DateTime, onupdate=datetime.utcnow)  # 最后登录时间

# 音频文件状态枚举
class StatusEnum(enum.Enum):
    pending = "pending"  # 待处理
    processing = "processing"  # 处理中
    completed = "completed"  # 已完成
    failed = "failed"  # 失败

# 报告部分枚举
class ReportPartEnum(enum.Enum):
    part0 = "家庭教育全景图"
    part1 = "沟通魔法"
    part2 = "家庭情绪密码"
    part3 = "亲子秘籍"

class AudioFile(db.Model):
    __tablename__ = 'audio_files'
    file_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # 使用UUID字符串作为file_id
    user_id = db.Column(db.Integer, ForeignKey('users.user_id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    custom_name = db.Column(db.String(255), nullable=True)  # 新增自定义名称字段
    file_path = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 使用正确的调用方式
    status = db.Column(SAEnum(StatusEnum), default=StatusEnum.pending)
    task_id = db.Column(db.String(50), nullable=True)  # 新增任务ID字段
    progress = db.Column(db.Integer, default=0, nullable=False)
    
    # 定义与 AnalysisResult 的关系
    analysis_results = relationship('AnalysisResult', back_populates='audio_file', cascade='all, delete-orphan')

# 转录模型
class Transcription(db.Model):
    __tablename__ = 'transcriptions'  # 改为小写
    transcription_id = db.Column(db.Integer, primary_key=True)  # 转录ID，主键
    transcript = db.Column(db.Text, nullable=False)  # 转录内容
    file_id = db.Column(db.String(36), ForeignKey('audio_files.file_id'), nullable=False)  # 修正为String(36)
    content = db.Column(db.Text, nullable=False)  # 转录文本内容

# 冲突类型枚举
class ConflictTypeEnum(str, enum.Enum):
    EC = "期望和目标冲突"
    CC = "沟通和互动方式冲突"
    LMC = "学习过程与方法冲突"
    RC = "规则与控制冲突"
    TMC = "时间与精力管理冲突"
    KC = "知识水平与理解差异冲突"
    FC = "注意力和专注度冲突"

# 冲突强度枚举
class ConflictSeverityEnum(str, enum.Enum):
    高 = "高"
    中 = "中"
    低 = "低"

# 行为类型枚举
class BehaviorTypeEnum(str, enum.Enum):
    ENC = "鼓励"
    SP = "有标注表扬"
    GP = "无标注表扬"
    GI = "启发式指导"
    SR = "设定规则"
    SRS = "敏感性回应"
    DI = "非启发式指导"
    IT = "信息教授"
    EC = "纠正错误"
    MON = "监督检查"
    DC = "直接命令"
    IC = "间接命令"
    CB = "批评责备"
    FT = "强迫威胁"
    NI = "忽视冷漠"
    BD = "贬低质疑"
    FD = "沮丧失望"
    II = "急躁不耐"

# 行为强度等级枚举
class BehaviorSeverityEnum(str, enum.Enum):
    积极 = "积极"
    中性 = "中性"
    消极 = "消极"

# 分析结果模型
class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    analysis_id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.String(36), ForeignKey('audio_files.file_id', ondelete='CASCADE'), nullable=False)
    family_overview = db.Column(db.Text)
    conversation_analysis = db.Column(db.Text)
    emotion_analysis_result = db.Column(db.Text)
    reflection_questions = db.Column(db.Text)
    conflict_analysis_result = db.Column(db.Text)
    behavior_analysis_result = db.Column(db.Text)
    strategy_generation_result = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 定义与场景的关系
    conflict_scenes = relationship('ConflictScene', back_populates='analysis_result', cascade='all, delete-orphan')
    behavior_scenes = relationship('BehaviorScene', back_populates='analysis_result', cascade='all, delete-orphan')
    
    # 反向关系
    audio_file = relationship('AudioFile', back_populates='analysis_results')

# 冲突场景模型
class ConflictScene(db.Model):
    __tablename__ = 'conflict_scenes'
    scene_id = db.Column(db.Integer, primary_key=True)
    trigger_event = db.Column(db.String(255), nullable=False)
    process = db.Column(db.String(1024), nullable=False)
    conflict_type = db.Column(SAEnum(ConflictTypeEnum), nullable=False)
    severity = db.Column(SAEnum(ConflictSeverityEnum), nullable=False)
    dt = db.Column(db.Integer, nullable=False)
    
    # 添加外键和关系
    analysis_id = db.Column(db.Integer, ForeignKey('analysis_results.analysis_id', ondelete='CASCADE'), nullable=False)
    analysis_result = relationship('AnalysisResult', back_populates='conflict_scenes')

# 行为场景模型
class BehaviorScene(db.Model):
    __tablename__ = 'behavior_scenes'
    behaviour_id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(1024), nullable=False)
    code = db.Column(SAEnum(BehaviorTypeEnum), nullable=False)
    type = db.Column(SAEnum(BehaviorSeverityEnum), nullable=False)
    dt = db.Column(db.String(8), nullable=False)
    
    # 添加外键和关系
    analysis_id = db.Column(db.Integer, ForeignKey('analysis_results.analysis_id', ondelete='CASCADE'), nullable=False)
    analysis_result = relationship('AnalysisResult', back_populates='behavior_scenes')

# 用户评分模型 - 新增
class UserRating(db.Model):
    __tablename__ = 'user_ratings'
    rating_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.user_id'), nullable=False)  # 添加用户ID外键
    part = db.Column(SAEnum(ReportPartEnum), nullable=False)
    comprehensibility = db.Column(db.Integer, nullable=False)  # 内容理解性 (1-5)
    authenticity = db.Column(db.Integer, nullable=False)  # 内容真实性 (1-5)
    usefulness = db.Column(db.Integer, nullable=False)  # 模块实用性 (1-5)
    comment = db.Column(db.String(500), nullable=True)  # 可选的评论
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 反向关系
    user = relationship('User', backref=db.backref('ratings', lazy=True))

