# 导入所需的模块和函数
from functools import cache
from flask import Blueprint, request, jsonify, send_from_directory, current_app, send_file, abort, render_template
from werkzeug.utils import secure_filename, safe_join
import os
import uuid
from ..extensions import db
from ..models import AudioFile, StatusEnum, Transcription, AnalysisResult, User, ConflictScene, BehaviorScene, UserRating, ReportPartEnum
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError
from ..utils.task_async import process_audio_task
from flask import redirect, url_for
import threading
import asyncio
from ..utils.generate_html import generate_html_from_context
from ..utils.generate_html import (
    ContentModel,
    EducationReport,
    BehaviorAnalysisModel,
    StrategyContentModel,
    generate_html_from_context

)

# 创建音频蓝图
audio_bp = Blueprint('audio', __name__)

# 检查文件是否为允许的类型
def allowed_file(filename):
    # 从配置中获取允许的扩展名，并确保包含常见的iOS格式
    default_allowed = {'wav', 'mp3', 'm4a', 'webm', 'aac', 'aiff', 'caf'} # 添加了 aac, aiff, caf
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', default_allowed)
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

# 获取上传 URL 路由
@audio_bp.route('/get_upload_url', methods=['POST'])
@jwt_required()
def get_upload_url():
    """
    获取上传URL路由
    """
    try:
        data = request.get_json()
        file_name = data.get('file_name')
        custom_name = data.get('custom_name', '')  # 接收 custom_name
        created_at = data.get('created_at')  # 接收创建时间

        if not file_name:
            return jsonify({'code': 400, 'msg': '文件名不能为空'}), 400

        if not allowed_file(file_name):
            return jsonify({'code': 400, 'msg': f'不允许的文件类型: {file_name.split(".")[-1]}' }), 400

        # 获取当前用户ID
        current_user_id = get_jwt_identity()

        # 生成唯一的file_id
        file_id = str(uuid.uuid4())

        # 构造文件路径
        secure_name = secure_filename(file_name)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_name)

        # 创建AudioFile记录，并初始化task_id为None
        new_audio = AudioFile(
            file_id=file_id,
            user_id=current_user_id,
            file_name=secure_name,
            custom_name=custom_name,  # 保存 custom_name
            file_path=file_path,
            status=StatusEnum.pending,  # 设置初始状态为pending
            task_id=None  # 初始化任务ID为空
        )
        db.session.add(new_audio)
        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'upload_url': f"/api/audio/upload/{file_id}",
                'file_id': file_id
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取上传URL时出错: {str(e)}")
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

# 上传完成确认路由
@audio_bp.route('/upload-complete', methods=['POST'])
@jwt_required()
def upload_complete():
    user_id = get_jwt_identity()
    data = request.get_json()
    file_id = data.get('file_id')

    if not file_id:
        return jsonify({'code': 400, 'msg': '缺少 file_id'}), 400

    audio = AudioFile.query.filter_by(file_id=file_id, user_id=user_id).first()
    if not audio:
        return jsonify({'code': 404, 'msg': '文件记录不存在'}), 404

    # 更新文件状态
    audio.status = StatusEnum.processing
    db.session.commit()

    # 触发后台任务（如 Celery 任务）
    try:
        process_audio_task(file_id)
    except Exception as e:
        audio.status = StatusEnum.pending
        db.session.commit()
        current_app.logger.error(f"处理任务启动失败: {e}")
        return jsonify({'code': 500, 'msg': '处理任务启动失败'}), 500

    return jsonify({'code': 200, 'msg': '上传完成确认成功'}), 200

# 上传文件路由
@audio_bp.route('/upload/<file_id>', methods=['POST'])
@jwt_required()
def upload_file(file_id):
    """
    上传文件路由
    """
    try:
        if 'file' not in request.files:
            return jsonify({'code': 400, 'msg': '没有文件部分'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'code': 400, 'msg': '没有选择文件'}), 400

        if file and allowed_file(file.filename):
            secure_name = secure_filename(file.filename)
            audio = AudioFile.query.get(file_id)
            if not audio:
                return jsonify({'code': 404, 'msg': '文件记录不存在'}), 404

            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_name)
            file.save(file_path)

            # 更新文件路径和状态
            audio.file_path = file_path
            audio.status = StatusEnum.pending
            db.session.commit()

            return jsonify({'code': 200, 'msg': '文件上传成功'}), 200
        else:
            return jsonify({'code': 400, 'msg': f'不允许的文件类型: {file.filename.split(".")[-1]}' }), 400
    except Exception as e:
        current_app.logger.error(f"上传文件时出错: {str(e)}")
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

def run_async_task(app, file_id):
    """
    在新线程中运行异步任务的同步包装器
    """
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # 运行异步任务
        result = loop.run_until_complete(process_audio_task(app, file_id))
        return result
    finally:
        # 确保关闭事件循环
        loop.close()

# 启动分析任务路由
@audio_bp.route('/analyze/<file_id>', methods=['POST'])
@jwt_required()
def analyze_file(file_id):
    """
    启动分析任务路由
    """
    try:
        user_id = get_jwt_identity()
        audio = AudioFile.query.filter_by(file_id=file_id, user_id=user_id).first()
        if not audio:
            return jsonify({'code': 404, 'msg': '文件记录不存在'}), 404

        if audio.status == StatusEnum.processing:
            return jsonify({'code': 400, 'msg': '分析任务正在进行中'}), 400
        if audio.status == StatusEnum.completed:
            return jsonify({'code': 400, 'msg': '文件已完成分析'}), 400

        # 更新状态为处理中
        audio.status = StatusEnum.processing
        audio.progress = 0  # 初始化进度
        db.session.commit()

        # 获取当前的应用实例
        app = current_app._get_current_object()

        # 启动后台线程执行任务，传递应用实例和 file_id
        task_thread = threading.Thread(
            target=run_async_task,
            args=(app, file_id),
            daemon=True  # 设置为守护线程，确保程序退出时线程结束
        )
        task_thread.start()

        return jsonify({'code': 200, 'msg': '分析任务已启动'}), 200
    except Exception as e:
        current_app.logger.error(f"启动分析任务时出错: {str(e)}")
        if 'audio' in locals() and audio:
            audio.status = StatusEnum.failed  # 如果出错，将状态重置为待处理
            db.session.commit()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500

# 新增：获取分析结果并生成 HTML 模板的路由
@audio_bp.route('/get_analysis/<file_id>', methods=['GET'])
@jwt_required()
def get_analysis(file_id):
    """
    获取分析结果并生成相应的 HTML 模板
    """
    try:
        user_id = get_jwt_identity()
        audio = AudioFile.query.filter_by(file_id=file_id, user_id=user_id).first()
        if not audio or audio.status != StatusEnum.completed:
            return jsonify({'code': 400, 'msg': '分析结果尚未完成'}), 400

        # 获取分析结果
        analysis_result = AnalysisResult.query.filter_by(file_id=file_id).first()
        if not analysis_result:
            current_app.logger.error(f"Analysis result not found for File ID: {file_id}")
            return jsonify({'code': 404, 'msg': '找不到分析结果'}), 404

        # 修改报告输出目录到static文件夹下
        reports_dir = os.path.join('static', 'reports')
        os.makedirs(reports_dir, exist_ok=True)

        # 检查所有报告文件是否已存在
        report_files = [
            os.path.join(reports_dir, f'output{i}_{file_id}.html') 
            for i in range(4)
        ] + [os.path.join(reports_dir, f'history2_{file_id}.html')]
        
        # 如果所有文件都存在,直接返回
        if all(os.path.exists(f) for f in report_files):
            current_app.logger.info(f"文件 {file_id} 的报告已存在,直接返回")
            return jsonify({
                'code': 200,
                'msg': 'HTML 文件已存在',
                'templates': {
                    'part0': f'/static/reports/output0_{file_id}.html',
                    'part1': f'/static/reports/output1_{file_id}.html', 
                    'part2': f'/static/reports/output2_{file_id}.html',
                    'part3': f'/static/reports/output3_{file_id}.html',
                    'history2': f'/static/reports/history2_{file_id}.html'
                }
            }), 200

        # 生成所有报告文件
        current_app.logger.info(f"开始为文件 {file_id} 生成报告文件")

        # 生成 part0.html - 家庭概览
        current_app.logger.info(f"生成家庭概览报告 part0.html")
        generate_html_from_context(
            content=analysis_result.family_overview+f"file_id={file_id}",
            model_class=EducationReport,  # 添加模型类
            template_name='part0.html', 
            output_path=os.path.join(reports_dir, f'output0_{file_id}.html')
        )
        current_app.logger.info(f"家庭概览报告生成完成")

        # 生成 part1.html - 对话分析
        current_app.logger.info(f"生成对话分析报告 part1.html")
        generate_html_from_context(
            content=analysis_result.conversation_analysis+f"file_id={file_id}",
            model_class=ContentModel,  # 对话分析模型
            template_name='part1.html',
            output_path=os.path.join(reports_dir, f'output1_{file_id}.html')
        )
        current_app.logger.info(f"对话分析报告生成完成")

        # 生成 part2.html - 行为分析等
        current_app.logger.info(f"生成行为分析报告 part2.html")
        generate_html_from_context(
            content=f"file_id={file_id}"+analysis_result.behavior_analysis_result + analysis_result.emotion_analysis_result + analysis_result.reflection_questions,
            model_class=BehaviorAnalysisModel,  # 行为分析模型
            template_name='part2.html',
            output_path=os.path.join(reports_dir, f'output2_{file_id}.html')
        )
        current_app.logger.info(f"行为分析报告生成完成")
        print(analysis_result.strategy_generation_result)
        # 生成 part3.html - 策略生成
        current_app.logger.info(f"生成策略生成报告 part3.html")
        generate_html_from_context(
            content=analysis_result.strategy_generation_result+f"file_id={file_id}",
            model_class=StrategyContentModel,  # 策略生成模型
            template_name='part3.html',
            output_path=os.path.join(reports_dir, f'output3_{file_id}.html')
        )
        current_app.logger.info(f"策略生成报告生成完成")

        # 生成 history2_{file_id}.html - 历史记录
        current_app.logger.info(f"生成历史记录报告 history2_{file_id}.html")
        generate_html_from_context(
            content=analysis_result.family_overview + f"file_id={file_id}",  # 使用与 part0 相同的内容
            model_class=EducationReport,  # 使用 EducationReport 模型类
            template_name='history2.html',
            output_path=os.path.join(reports_dir, f'history2_{file_id}.html')
        )
        current_app.logger.info(f"历史记录报告生成完成")

        current_app.logger.info(f"文件 {file_id} 的所有报告生成完毕")

        return jsonify({
            'code': 200,
            'msg': 'HTML 文件已生成',
            'templates': {
                'part0': f'/static/reports/output0_{file_id}.html',
                'part1': f'/static/reports/output1_{file_id}.html',
                'part2': f'/static/reports/output2_{file_id}.html',
                'part3': f'/static/reports/output3_{file_id}.html',
                'history2': f'/static/reports/history2_{file_id}.html'
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"生成 HTML 模板时出错: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500





# 获取任务进度路由
@audio_bp.route('/progress/<file_id>', methods=['GET'])
@jwt_required()
def get_progress(file_id):
    """
    获取任务进度路由
    """
    try:
        user_id = get_jwt_identity()
        audio = AudioFile.query.filter_by(file_id=file_id, user_id=user_id).first()
        if not audio:
            return jsonify({'code': 404, 'msg': '文件记录不存在'}), 404

        return jsonify({
            'code': 200,
            'data': {
                'current': audio.progress,
                'total': 100,
                'status': translate_status(audio.status)
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"获取任务进度时出错: {str(e)}")
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500
    
def translate_status(status):
    status_map = {
        StatusEnum.pending: '待处理',
        StatusEnum.processing: '处理中',
        StatusEnum.completed: '已完成',
        StatusEnum.failed: '失败'
    }
    return status_map.get(status, status)

# 获取文件列表路由
@audio_bp.route('/list_files', methods=['GET'])
@jwt_required()
def list_files():
    """
    获取用户的音频文件列表
    """
    try:
        current_user_id = get_jwt_identity()
        files = AudioFile.query.filter_by(user_id=current_user_id).all()
        files_list = [{
            'file_id': file.file_id,
            'file_name': file.file_name,
            'custom_name': file.custom_name,  # 添加 custom_name
            'status': file.status.value  # 将枚举值转换为字符串
        } for file in files]

        return jsonify({'code': 200, 'data': {'files': files_list}}), 200
    except Exception as e:
        current_app.logger.error(f"获取文件列表时出错: {str(e)}")
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

# 删除文件路由
@audio_bp.route('/delete/<file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """
    删除用户的音频文件
    """
    try:
        audio_file = AudioFile.query.filter_by(file_id=file_id, user_id=get_jwt_identity()).first()

        if not audio_file:
            return jsonify({'code': 404, 'msg': '文件未找到'}), 404

        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], audio_file.file_name)  # 更新为实际上传文件夹路径
        if os.path.exists(file_path):
            os.remove(file_path)

        # 如果有关联的任务，尝试撤销
        if audio_file.task_id:
            from celery import Celery
            celery = Celery(broker=current_app.config['CELERY_BROKER_URL'])
            celery.control.revoke(audio_file.task_id, terminate=True)

        db.session.delete(audio_file)
        db.session.commit()

        return jsonify({'code': 200, 'msg': '文件已删除'}), 200
    except Exception as e:
        current_app.logger.error(f"删除文件时出错: {str(e)}")
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

# 下载文件路由
@audio_bp.route('/download/<file_id>', methods=['GET'])
@jwt_required()
def download_file(file_id):
    try:
        user_id = get_jwt_identity()
        current_app.logger.debug(f"Download request received for file_id: {file_id}, user_id: {user_id}")
        
        audio = AudioFile.query.filter_by(file_id=file_id, user_id=user_id).first()
        if not audio:
            current_app.logger.warning(f"File not found in database for file_id: {file_id}, user_id: {user_id}")
            return jsonify({'code': 404, 'msg': '文件记录不存在'}), 404

        # 检查文件路径是存在
        if not os.path.exists(audio.file_path):
            current_app.logger.error(f"File path does not exist: {audio.file_path}")
            return jsonify({'code': 404, 'msg': '文件不存在'}), 404

        # 使用 safe_join 来确保文件路径的安全
        file_path = safe_join(current_app.config['UPLOAD_FOLDER'], os.path.basename(audio.file_path))
        if not file_path:
            current_app.logger.error(f"Invalid file path: {audio.file_path}")
            return jsonify({'code': 400, 'msg': '无效的文件路径'}), 400

        current_app.logger.info(f"Attempting to send file: {file_path}")
        
        if os.path.isfile(file_path):
            return send_file(file_path, as_attachment=True, download_name=audio.file_name)
        else:
            current_app.logger.error(f"File not found at path: {file_path}")
            return jsonify({'code': 404, 'msg': '文件不存在'}), 404

    except Exception as e:
        current_app.logger.error(f"Unexpected error in download_file: {str(e)}")
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

# 分析示例路由
@audio_bp.route('/analyze/<filename>', methods=['GET'])
@jwt_required()
def analyze_example(filename):
    user_id = get_jwt_identity()
    # 获取文件记录
    audio = AudioFile.query.filter_by(file_name=filename, user_id=user_id).first()
    if not audio:
        return jsonify({'error': '文件不存在'}), 404

    # 获取分析状态
    if audio.status == StatusEnum.completed:
        # 获取分析结果
        analysis = AnalysisResult.query.filter_by(file_id=audio.file_id).first()
        if not analysis:
            return jsonify({'error': '分析结果不存在'}), 404
        transcript = Transcription.query.filter_by(file_id=audio.file_id).first()
        return jsonify({
            'transcript': transcript.transcript if transcript else '',
            'analysis': {
                'family_overview': analysis.family_overview,
                'conversation_analysis': analysis.conversation_analysis,
                'emotion_analysis': analysis.emotion_analysis_result,
                'reflection_questions': analysis.reflection_questions,
                'conflict_analysis': analysis.conflict_analysis_result,
                'behavior_analysis': analysis.behavior_analysis_result,
                'strategy_generation': analysis.strategy_generation_result
            }
        }), 200
    elif audio.status == StatusEnum.processing:
        return jsonify({'status': 'processing'}), 200
    else:
        return jsonify({'status': 'pending'}), 200

# 处理授权错误
@audio_bp.errorhandler(NoAuthorizationError)
def handle_auth_error(e):
    return jsonify({'code': 401, 'msg': '未授权访问'}), 401

# 全局异常处理器
@audio_bp.errorhandler(Exception)
def handle_unexpected_error(error):
    current_app.logger.error('Unexpected error: %s', str(error))
    return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500



@audio_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    返回当前用户的冲突场景和行为场景统计数据。
    """
    try:
        user_id = get_jwt_identity()
        
    
            
        # 查询当前用户的所有 audio_files
        audio_files = AudioFile.query.filter_by(user_id=user_id).all()
        audio_file_ids = [audio.file_id for audio in audio_files]

        if not audio_file_ids:
            response_data = {
                "conflict_count": 0,
                "conflict_change": "N/A",
                "behavior_count": 0,
                "behavior_change": "N/A"
            }
        else:
            # 获取有分析结果的记录并按创建时间降序排序
            analyses = AnalysisResult.query \
                .filter(AnalysisResult.file_id.in_(audio_file_ids)) \
                .filter(
                    db.or_(
                        AnalysisResult.conflict_analysis_result.isnot(None),
                        AnalysisResult.behavior_analysis_result.isnot(None)
                    )
                ) \
                .order_by(AnalysisResult.created_at.desc(), AnalysisResult.analysis_id.desc()).all()
                
            if not analyses:
                response_data = {
                    "conflict_count": 0,
                    "conflict_change": "N/A",
                    "behavior_count": 0,
                    "behavior_change": "N/A"
                }
            else:
                # 最近的分析结果
                current_analysis = analyses[0]
                current_analysis_id = current_analysis.analysis_id
                
                # 统计当前分析结果的冲突场景和行为场景数量
                current_conflict_count = ConflictScene.query.filter_by(analysis_id=current_analysis_id).count()
                current_behavior_count = BehaviorScene.query.filter_by(analysis_id=current_analysis_id).count()
                
                # 如果有前一个分析结果
                if len(analyses) > 1:
                    previous_analysis = analyses[1]
                    previous_conflict_count = ConflictScene.query.filter_by(analysis_id=previous_analysis.analysis_id).count()
                    previous_behavior_count = BehaviorScene.query.filter_by(analysis_id=previous_analysis.analysis_id).count()
                else:
                    previous_conflict_count = 0
                    previous_behavior_count = 0
                
                # 计算变化百分比
                def calculate_change(current, previous):
                    if previous == 0:
                        return "N/A"
                    change = ((current - previous) / previous) * 100
                    return f"{change:.1f}%" if abs(change) < 1000 else "过大变化"
                
                response_data = {
                    "conflict_count": current_conflict_count,
                    "conflict_change": calculate_change(current_conflict_count, previous_conflict_count),
                    "behavior_count": current_behavior_count,
                    "behavior_change": calculate_change(current_behavior_count, previous_behavior_count)
                }
        
        
        return jsonify({"code": 200, "data": response_data}), 200
    except Exception as e:
        current_app.logger.error(f"获取历史统计数据时出错: {str(e)}")
        return jsonify({'code': 500, 'msg': '无法获取历史统计数据。'}), 500
    
@audio_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    """
    获取历史记录和图片数据，包括冲突和行为分析
    """
    user_id = get_jwt_identity()
    try:
        # 通过AudioFile关联查询
        analyses = db.session.query(AnalysisResult)\
            .join(AudioFile, AnalysisResult.file_id == AudioFile.file_id)\
            .filter(AudioFile.user_id == user_id)\
            .order_by(AnalysisResult.created_at.desc())\
            .all()

        history_data = []
        for analysis in analyses:
            # 检查冲突图表文件是否存在,不存在则使用默认图片
            conflict_dist_path = f'static/images/conflict_distribution_{user_id}.png'
            if not os.path.exists(conflict_dist_path):
                conflict_dist_path = 'static/images/conflict_dist.png'

            conflict_trend_path = f'static/images/conflict_trend_{user_id}.png'
            if not os.path.exists(conflict_trend_path):
                conflict_trend_path = 'static/images/trend.png'
                
            # 添加冲突类型趋势图
            conflict_type_trend_path = f'static/images/conflict_type_trend_{user_id}.png'
            if not os.path.exists(conflict_type_trend_path):
                conflict_type_trend_path = 'static/images/conflict_type_trend.png'

            severity_dist_path = f'static/images/severity_distribution_{user_id}.png'
            if not os.path.exists(severity_dist_path):
                severity_dist_path = 'static/images/severity.png'
                
            # 检查行为图表文件是否存在,不存在则使用默认图片
            behavior_dist_path = f'static/images/behavior_distribution_{user_id}.png'
            if not os.path.exists(behavior_dist_path):
                behavior_dist_path = 'static/images/behavior_dist.png'
                
            behavior_trend_path = f'static/images/behavior_trend_{user_id}.png'
            if not os.path.exists(behavior_trend_path):
                behavior_trend_path = 'static/images/behavior_trend.png'
                
            behavior_type_path = f'static/images/behavior_type_distribution_{user_id}.png'
            if not os.path.exists(behavior_type_path):
                behavior_type_path = 'static/images/behavior_type.png'
                
            # 添加行为百分比趋势图
            behavior_percentage_trend_path = f'static/images/behavior_percentage_trend_{user_id}.png'
            if not os.path.exists(behavior_percentage_trend_path):
                behavior_percentage_trend_path = 'static/images/behavior_percentage_trend.png'

            history_data.append({
                'user_id': user_id,
                'file_id': analysis.file_id,
                'timestamp': int(analysis.created_at.timestamp()),
                'conflict_distribution': conflict_dist_path,
                'conflict_trend': conflict_trend_path,
                'conflict_type_trend': conflict_type_trend_path, 
                'severity_distribution': severity_dist_path,
                'behavior_distribution': behavior_dist_path,
                'behavior_trend': behavior_trend_path,
                'behavior_type_distribution': behavior_type_path,
                'behavior_percentage_trend': behavior_percentage_trend_path
            })

        return jsonify({'code': 200, 'data': history_data}), 200
    except Exception as e:
        current_app.logger.error(f"获取历史记录时出错: {str(e)}")
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

# 修改 history2_page 路由
@audio_bp.route('/history2/<file_id>', methods=['GET'])
@jwt_required()
def history2_page(file_id):
    """
    智能返回可用报告页面,如果请求的报告不存在则重定向到其他可用报告
    """
    try:
        user_id = get_jwt_identity()
        current_app.logger.warning(f"用户 {user_id} 请求访问报告 {file_id}")

        # 如果file_id为undefined，直接获取用户所有已完成的分析记录
        if file_id == 'undefined':
            current_app.logger.warning(f"file_id为undefined，直接获取用户所有已完成的分析记录")
            completed_files = AudioFile.query.filter(
                AudioFile.user_id == user_id,
                AudioFile.status == StatusEnum.completed,
                AudioFile.file_id.isnot(None),
                AudioFile.file_id != ''
            ).all()
            # 遍历查找其他可用的报告
            for audio_file in completed_files:
                report_path = f'reports/history2_{audio_file.file_id}.html'
                full_path = os.path.join(current_app.static_folder, report_path)
                current_app.logger.warning(f"尝试定位其他报告路径: {full_path}")
                
                if os.path.exists(full_path):
                    current_app.logger.warning(f"找到可用报告: {full_path}")
                    return redirect(url_for('static', filename=report_path))

        # 先检查用户是否有权限访问该报告
        target_file = AudioFile.query.filter_by(file_id=file_id).first()
        if not target_file or target_file.user_id != user_id:
            current_app.logger.warning(f"用户 {user_id} 无权访问报告 {file_id}")
            return jsonify({'code': 401, 'msg': '无权访问该报告'}), 401

        # 检查目标报告文件是否存在
        target_path = os.path.join(current_app.static_folder, f'reports/history2_{file_id}.html')
        current_app.logger.warning(f"尝试定位目标报告路径: {target_path}")
        
        if os.path.exists(target_path):
            # 如果目标报告存在,直接返回
            current_app.logger.warning(f"找到目标报告: {target_path}")
            return redirect(url_for('static', filename=f'reports/history2_{file_id}.html'))
            
        # 如果目标报告不存在,查找其他可用报告
        # 获取用户所有已完成的分析记录
        completed_files = AudioFile.query.filter(
            AudioFile.user_id == user_id,
            AudioFile.status == StatusEnum.completed,
            AudioFile.file_id.isnot(None),  # 新增空值过滤
            AudioFile.file_id != ''         # 过滤空字符串
        ).all()
        
        # 遍历查找其他可用的报告
        for audio_file in completed_files:
            report_path = f'reports/history2_{audio_file.file_id}.html'
            full_path = os.path.join(current_app.static_folder, report_path)
            current_app.logger.warning(f"尝试定位其他报告路径: {full_path}")
            
            if os.path.exists(full_path):
                current_app.logger.warning(f"找到可用报告: {full_path}")
                return redirect(url_for('static', filename=report_path))
        
        current_app.logger.warning("未找到任何可用报告")
        return jsonify({'code': 404, 'msg': '没有找到可用的报告'}), 404
        
    except Exception as e:
        current_app.logger.error(f"访问报告页失败: {str(e)}")
        return jsonify({'code': 500, 'msg': '报告加载失败'}), 500

@audio_bp.route('/submit_rating', methods=['POST'])
@jwt_required(optional=True)  # 修改为可选JWT认证
def submit_rating():
    try:
        # 获取当前用户ID
        current_user_id = get_jwt_identity()
        
        # 如果用户未登录，使用临时ID
        if current_user_id is None:
            current_app.logger.info("用户未登录，使用临时用户ID")
            # 使用系统中第一个用户作为默认用户（或创建一个专门的游客账户）
            default_user = User.query.first()
            if default_user:
                current_user_id = default_user.user_id
            else:
                current_app.logger.error("系统中没有用户，无法提交评分")
                return jsonify({'success': False, 'message': '系统错误：没有默认用户'}), 500
        
        # 从表单中获取数据并打印日志
        form_data = request.form.to_dict()
        current_app.logger.info(f"收到评分提交: {form_data}")
        
        part_str = form_data.get('part')
        
        # 直接从表单中获取评分值，可能来自输入框而非隐藏字段
        try:
            comprehensibility = int(form_data.get('comprehensibility', 0))
            authenticity = int(form_data.get('authenticity', 0))
            usefulness = int(form_data.get('usefulness', 0))
        except (ValueError, TypeError) as e:
            # 如果转换失败，尝试从输入框直接获取
            current_app.logger.warning(f"无法将评分转换为整数: {e}")
            comprehensibility = int(form_data.get('comprehensibility-input', 0))
            authenticity = int(form_data.get('authenticity-input', 0))
            usefulness = int(form_data.get('usefulness-input', 0))
            
        comment = form_data.get('comment', '')
        
        # 详细日志
        current_app.logger.info(f"解析后的评分数据: part={part_str}, " 
                               f"comprehensibility={comprehensibility}, authenticity={authenticity}, "
                               f"usefulness={usefulness}")
        
        # 验证数据
        if not part_str:
            current_app.logger.warning(f"缺少必要参数: part={part_str}")
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
            
        if not all(1 <= rating <= 5 for rating in [comprehensibility, authenticity, usefulness]):
            current_app.logger.warning(f"评分不在有效范围内: {comprehensibility}, {authenticity}, {usefulness}")
            return jsonify({'success': False, 'message': '评分必须在1-5之间'}), 400
        
        # 将part字符串转换为枚举值
        part_mapping = {
            'part0': ReportPartEnum.part0,
            'part1': ReportPartEnum.part1,
            'part2': ReportPartEnum.part2,
            'part3': ReportPartEnum.part3
        }
        part = part_mapping.get(part_str)
        if not part:
            current_app.logger.warning(f"无效的报告部分: {part_str}")
            return jsonify({'success': False, 'message': '无效的报告部分'}), 400
        
        # 创建新的评分记录
        new_rating = UserRating(
            user_id=current_user_id,
            part=part,
            comprehensibility=comprehensibility,
            authenticity=authenticity,
            usefulness=usefulness,
            comment=comment
        )
        db.session.add(new_rating)
        current_app.logger.info("创建新的评分记录")
        
        db.session.commit()
        return jsonify({'success': True, 'message': '评分已成功提交'})
    
    except Exception as e:
        current_app.logger.error(f"评分提交错误: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

# 添加删除报告的路由
@audio_bp.route('/delete_report/<file_id>', methods=['DELETE'])
@jwt_required()
def delete_report(file_id):
    """
    删除用户的报告及相关文件
    """
    try:
        user_id = get_jwt_identity()
        
        # 检查文件是否存在且属于当前用户
        audio = AudioFile.query.filter_by(file_id=file_id, user_id=user_id).first()
        if not audio:
            return jsonify({'code': 404, 'msg': '报告不存在或无权限删除'}), 404

        # 删除相关的报告文件
        reports_dir = os.path.join('static', 'reports')
        report_files = [
            f'output0_{file_id}.html',
            f'output1_{file_id}.html',
            f'output2_{file_id}.html',
            f'output3_{file_id}.html',
            f'history2_{file_id}.html'
        ]

        for report_file in report_files:
            file_path = os.path.join(reports_dir, report_file)
            if os.path.exists(file_path):
                os.remove(file_path)

        # 删除数据库中的相关记录
        analysis = AnalysisResult.query.filter_by(file_id=file_id).first()
        if analysis:
            db.session.delete(analysis)

        transcription = Transcription.query.filter_by(file_id=file_id).first()
        if transcription:
            db.session.delete(transcription)

        # 删除音频文件记录
        db.session.delete(audio)
        db.session.commit()

        return jsonify({'code': 200, 'msg': '报告删除成功'}), 200

    except Exception as e:
        current_app.logger.error(f"删除报告时出错: {str(e)}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '删除报告失败'}), 500

