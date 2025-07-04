# app/routes/main_routes.py
from flask import Blueprint, render_template, abort, redirect, url_for, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import AnalysisResult, AudioFile
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def home():
    """
    重定向根路径到登录页面
    """
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET'])
def login():
    """
    登录页面
    """
    return render_template('index.html')

@main_bp.route('/register', methods=['GET'])
def register():
    """
    注册页面
    """
    return render_template('register.html')

@main_bp.route('/upload', methods=['GET'])
def upload():
    """
    录音上传与管理页面
    """
    return render_template('upload.html')

@main_bp.route('/home_page', methods=['GET'])
def home_page():
    """
    主页
    """
    return render_template('home.html')

@main_bp.route('/history', methods=['GET'])
def history():
    """
    历史页面
    """
    return render_template('history1.html')

@main_bp.route('/recording', methods=['GET'])
def recording():
    """
    录音页面
    """
    return render_template('recording.html')

@main_bp.route('/analyse', methods=['GET'])
def analyse():
    """
    分析页面
    """
    return render_template('analyse.html')

@main_bp.route('/audio', methods=['GET'])
def audio():
    """
    音频页面
    """
    return render_template('audio1.html')


@main_bp.route('/detail/<int:id>', methods=['GET'])
def detail(id):
    """
    详情页面
    """
    return render_template(f'detail{id}.html')



@main_bp.route('/report/<file_id>', methods=['GET'])
def report(file_id):
    """
    分析报告页面
    """
    analysis = AnalysisResult.query.filter_by(file_id=file_id).first()
    if not analysis:
        abort(404, description="分析结果不存在")
    # 将分析结果转换为字典
    analysis_dict = {
        "family_overview": analysis.family_overview,
        "conversation_analysis": analysis.conversation_analysis,
        "emotion_analysis_result": analysis.emotion_analysis_result,
        "reflection_questions": analysis.reflection_questions,
        "conflict_analysis_result": analysis.conflict_analysis_result,
        "behavior_analysis_result": analysis.behavior_analysis_result,
        "strategy_generation_result": analysis.strategy_generation_result
    }
    print(f"Analysis Data for file_id {file_id}: {analysis_dict}")  # 添加日志
    return render_template('report.html', analysis=analysis_dict)
