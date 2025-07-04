# app/utils/task_async.py

import json
import traceback
import os
import asyncio
from flask import current_app
from ..extensions import db
from ..models import (
    AudioFile, Transcription, AnalysisResult, StatusEnum,
    ConflictScene, BehaviorScene, ConflictTypeEnum, 
    ConflictSeverityEnum, BehaviorTypeEnum, BehaviorSeverityEnum
)
from .storage import download_from_storage_async, load_documents_from_storage_async
from .script_analysis import ConflictAnalysis, BehaviorAnalysis, BehaviorAnalysisOutput, ConflictAnalysisOutput,transcribe_audio_async, analyze_audio_async, generate_intervention_strategy_async
from .request_api import process_audio_async
from sqlalchemy import text
from typing import List, Tuple
from .generate_analysis_figures import generate_analysis_figures
from .generate_html import (
    ContentModel,
    EducationReport,
    BehaviorAnalysisModel,
    StrategyContentModel,
    TutoringPortraitModel,
    generate_html_from_context,
    generate_html_from_context_async,
    generate_multiple_html_async
)
from sqlalchemy.exc import OperationalError, PendingRollbackError

# 添加重试装饰器
async def retry_async(func, *args, max_retries=1, **kwargs):
    """
    异步函数的重试装饰器
    
    参数:
        func: 要执行的异步函数
        *args: 传递给函数的位置参数
        max_retries: 最大重试次数，默认为1
        **kwargs: 传递给函数的关键字参数
        
    返回:
        与原函数相同的返回值
    """
    attempt = 0
    last_exception = None
    
    while attempt <= max_retries:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            attempt += 1
            last_exception = e
            if attempt <= max_retries:
                current_app._get_current_object().logger.warning(
                    f"函数 {func.__name__} 执行失败(尝试 {attempt}/{max_retries+1}): {str(e)}，准备重试..."
                )
                await asyncio.sleep(1)  # 等待1秒后重试
            else:
                current_app._get_current_object().logger.error(
                    f"函数 {func.__name__} 在 {max_retries+1} 次尝试后仍然失败: {str(e)}"
                )
    
    # 如果所有重试都失败，抛出最后捕获的异常
    raise last_exception

async def process_audio_task(app, file_id):
    """
    异步处理音频文件的分析任务
    """
    # 使用同步的方式推送应用上下文
    with app.app_context():
        try:
            # 获取音频文件记录
            audio = await asyncio.to_thread(AudioFile.query.get, file_id)
            # 获取用户ID
            user_id = audio.user_id
            if not audio:
                app.logger.error(f"文件记录不存在: file_id={file_id}")
                return {'status': 'failed', 'reason': '文件记录不存在'}

            # 更新进度到10%
            audio.progress = 10
            audio.status = StatusEnum.processing
            try:
                await asyncio.to_thread(db.session.commit)
            except (OperationalError, PendingRollbackError) as e:
                app.logger.warning(f"数据库提交失败 (progress 10): {e}, 开始回滚并重试...")
                await asyncio.to_thread(db.session.rollback)
                # 重新获取 audio 对象，因为它可能已从会话中分离
                audio = await asyncio.to_thread(AudioFile.query.get, file_id)
                if audio: # 确保 audio 对象仍然存在
                    audio.progress = 10
                    audio.status = StatusEnum.processing
                    await asyncio.to_thread(db.session.commit) # 重试提交
                else:
                    app.logger.error(f"重试提交失败：无法重新获取 audio 对象 file_id={file_id}")
                    raise # 如果无法恢复，则重新引发异常

            try:
                # 使用重试机制转写音频
                transcript = await retry_async(process_audio_async, audio.file_path, max_retries=1)
                app.logger.info(f"转写长度: {len(transcript) if isinstance(transcript, list) else 'not a list'}, 文档加载完成")
                
                # 标准化转写结果格式
                normalized_transcript = normalize_transcript(transcript)
                app.logger.info(f"标准化后的转写长度: {len(normalized_transcript)}")

                # 更新进度到30%
                audio.progress = 30
                try:
                    await asyncio.to_thread(db.session.commit)
                except (OperationalError, PendingRollbackError) as e:
                    app.logger.warning(f"数据库提交失败 (progress 30): {e}, 开始回滚并重试...")
                    await asyncio.to_thread(db.session.rollback)
                    audio = await asyncio.to_thread(AudioFile.query.get, file_id)
                    if audio:
                        audio.progress = 30
                        await asyncio.to_thread(db.session.commit)
                    else:
                        app.logger.error(f"重试提交失败：无法重新获取 audio 对象 file_id={file_id}")
                        raise

                # 获取日期时间，从 AudioFile 的 custom_name 字段提取
                dt = extract_date_from_custom_name(audio.custom_name)

                # 创建新的分析结果记录
                new_analysis = AnalysisResult(file_id=file_id)
                try:
                    await asyncio.to_thread(lambda: (db.session.add(new_analysis), db.session.commit()))
                except (OperationalError, PendingRollbackError) as e:
                    app.logger.warning(f"数据库提交失败 (new_analysis): {e}, 开始回滚并重试...")
                    await asyncio.to_thread(db.session.rollback)
                    # new_analysis 对象可能已失效，但因为主键是自增的，所以下次添加时会创建新的
                    # 或者，可以尝试重新创建并添加
                    new_analysis = AnalysisResult(file_id=file_id) # 重新创建实例
                    await asyncio.to_thread(lambda: (db.session.add(new_analysis), db.session.commit()))
                analysis_id = new_analysis.analysis_id

                # 同时执行步骤 4、5、6 和 步骤 7，使用规范化后的转写结果
                # 为每个任务添加重试机制
                tasks = [
                    asyncio.create_task(retry_async(save_transcript_json, app, file_id, dt, normalized_transcript)),
                    asyncio.create_task(retry_async(save_transcription_to_db, db, file_id, normalized_transcript)),
                    asyncio.create_task(retry_async(generate_intervention_strategy_async, normalized_transcript)),
                    asyncio.create_task(retry_async(analyze_transcripts, normalized_transcript, dt, file_id, analysis_id))
                ]

                # 使用gather_with_concurrency限制并发数量，避免资源过度使用
                results = await asyncio.gather(*tasks)
                transcript_path, new_transcription, intervention_strategy, (conflict_result, behavior_result) = results

                # 更新进度到70%
                audio.progress = 70
                await asyncio.to_thread(db.session.commit)

                # 更新分析结果，使用异常处理确保健壮性
                try:
                    new_analysis.family_overview = intervention_strategy.get('family_overview')
                    new_analysis.conversation_analysis = intervention_strategy.get('conversation_analysis')
                    new_analysis.emotion_analysis_result = intervention_strategy.get('emotion_analysis')
                    new_analysis.reflection_questions = intervention_strategy.get('reflection_questions')
                    new_analysis.conflict_analysis_result = intervention_strategy.get('conflict_analysis')
                    new_analysis.behavior_analysis_result = intervention_strategy.get('behavior_analysis')
                    new_analysis.strategy_generation_result = intervention_strategy.get('strategy_generation')
                    new_analysis.created_at = dt
                    await asyncio.to_thread(db.session.commit)
                    app.logger.info(f"分析结果保存完成: file_id={file_id}")
                except Exception as e:
                    app.logger.error(f"保存分析结果时出错: {str(e)}，尝试重新保存...")
                    # 重试一次
                    try:
                        # 确保获取新的会话，防止事务状态错误
                        await asyncio.to_thread(db.session.rollback)
                        # 重新获取分析结果记录
                        new_analysis = await asyncio.to_thread(AnalysisResult.query.get, analysis_id)
                        if new_analysis:
                            new_analysis.family_overview = intervention_strategy.get('family_overview')
                            new_analysis.conversation_analysis = intervention_strategy.get('conversation_analysis')
                            new_analysis.emotion_analysis_result = intervention_strategy.get('emotion_analysis')
                            new_analysis.reflection_questions = intervention_strategy.get('reflection_questions')
                            new_analysis.conflict_analysis_result = intervention_strategy.get('conflict_analysis')
                            new_analysis.behavior_analysis_result = intervention_strategy.get('behavior_analysis')
                            new_analysis.strategy_generation_result = intervention_strategy.get('strategy_generation')
                            new_analysis.created_at = dt
                            await asyncio.to_thread(db.session.commit)
                            app.logger.info(f"分析结果重试保存成功: file_id={file_id}")
                    except Exception as retry_e:
                        app.logger.error(f"重试保存分析结果仍然失败: {str(retry_e)}")
                
                # 生成并保存冲突和行为图表，添加重试
                try:
                    image_paths = await retry_async(
                        lambda: asyncio.to_thread(generate_analysis_figures, user_id=user_id), 
                        max_retries=1
                    )
                    await asyncio.to_thread(db.session.commit)
                    app.logger.info(f"分析结果和图表保存完成: file_id={file_id}")
                except Exception as e:
                    app.logger.error(f"生成分析图表失败: {str(e)}")
                
                # 保存冲突分析结果和行为分析结果到本地JSON文件，添加重试
                save_results_tasks = [
                    asyncio.create_task(retry_async(save_conflict_result_json, app, user_id, dt, conflict_result)),
                    asyncio.create_task(retry_async(save_behavior_result_json, app, user_id, dt, behavior_result))
                ]
                try:
                    await asyncio.gather(*save_results_tasks)
                    app.logger.info(f"冲突分析结果和行为分析结果已保存为JSON文件: user_id={user_id}, 日期={dt}")
                except Exception as e:
                    app.logger.error(f"保存分析结果JSON文件失败: {str(e)}")

                audio.progress = 90
                # 调用生成报告函数，添加重试
                try:
                    await retry_async(generate_reports, app, file_id, new_analysis, audio, max_retries=1)
                except Exception as e:
                    app.logger.error(f"生成报告失败: {str(e)}")
                    # 即使报告生成失败，仍然完成任务
                    audio.progress = 100
                    audio.status = StatusEnum.completed
                    await asyncio.to_thread(db.session.commit)

                return {'status': 'success'}

            except Exception as e:
                # 处理异常，更新状态为failed
                audio.status = StatusEnum.failed
                audio.progress = 0
                await asyncio.to_thread(db.session.commit)
                raise  # 重新抛出异常以便外层捕获

        except Exception as e:
            # 记录详细的错误信息和堆栈跟踪
            error_msg = f"处理文件时发生错误: file_id={file_id}, error={str(e)}"
            stack_trace = traceback.format_exc()
            app.logger.error(f"{error_msg}\n堆栈跟踪:\n{stack_trace}")
            return {'status': 'failed', 'reason': error_msg}

def extract_date_from_custom_name(custom_name: str) -> str:
    """
    从 custom_name 字段提取日期，支持多种格式。
    
    Args:
        custom_name: 自定义文件名，可能包含日期信息。
        
    Returns:
        str: 格式化为YYYYMMDD的日期字符串，如果无法解析则返回当前日期。
    """
    import re
    import datetime
    
    # 如果custom_name为None，使用当前日期
    if not custom_name:
        return datetime.datetime.now().strftime('%Y%m%d')
    
    # 尝试匹配常见的日期格式
    # 1. YYYY-MM-DD 或 YYYY/MM/DD
    pattern1 = r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
    match = re.search(pattern1, custom_name)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)  # 确保月份是两位数
        day = match.group(3).zfill(2)    # 确保日期是两位数
        return f"{year}{month}{day}"
    
    # 2. DD-MM-YYYY 或 DD/MM/YYYY
    pattern2 = r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})'
    match = re.search(pattern2, custom_name)
    if match:
        day = match.group(1).zfill(2)
        month = match.group(2).zfill(2)
        year = match.group(3)
        return f"{year}{month}{day}"
    
    # 3. YYYYMMDD 格式
    pattern3 = r'(\d{8})'
    match = re.search(pattern3, custom_name)
    if match and 19000101 <= int(match.group(1)) <= 21001231:  # 简单验证日期范围
        return match.group(1)
    
    # 如果都无法匹配，返回当前日期
    current_date = datetime.datetime.now().strftime('%Y%m%d')
    print(f"无法从 '{custom_name}' 中提取日期，使用当前日期: {current_date}")
    return current_date
    
async def save_transcript_json(app, user_id, date, transcript):
    """
    异步保存转写结果到JSON文件
    """
    app.logger.info(f"开始保存转写结果到JSON文件: user_id={user_id}, 日期={date}")
    results_dir = os.path.join('static', 'transcripts')
    os.makedirs(results_dir, exist_ok=True)
    transcript_filename = f"{user_id}_{date}_transcript.json"
    transcript_path = os.path.join(results_dir, transcript_filename)
    
    async def write_transcript():
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, ensure_ascii=False, indent=4)
    
    await asyncio.to_thread(write_transcript)
    app.logger.info(f"转写结果已保存到: {transcript_path}")
    return transcript_path

async def save_transcription_to_db(db, file_id, transcript):
    """
    异步保存转写结果到数据库
    """
    app = current_app._get_current_object()
    app.logger.info(f"开始保存转写结果到数据库: file_id={file_id}")
    
    new_transcription = Transcription(
        transcript=json.dumps(transcript, ensure_ascii=False),
        file_id=file_id,
        content=str(transcript)
    )
    
    await asyncio.to_thread(lambda: (db.session.add(new_transcription), db.session.commit()))
    app.logger.info(f"转写结果保存完成: file_id={file_id}")
    return new_transcription

from typing import Tuple

async def analyze_transcripts(transcripts: List[dict], date: str, file_id: str, analysis_id: int) -> Tuple[ConflictAnalysisOutput, BehaviorAnalysisOutput]:
    """
    封装冲突分析和行为分析的函数。

    参数:
        transcripts (List[dict]): 转录文本的字典列表。
        date (str): 日期，格式为"YYYYMMDD"。
        file_id (str): 音频文件ID。
        analysis_id (int): 分析结果ID。

    返回:
        Tuple[ConflictAnalysisOutput, BehaviorAnalysisOutput]: 冲突分析和行为分析的输出结果。
    """
    app = current_app._get_current_object()
    
    # 冲突分析
    conflict_analyzer = ConflictAnalysis()
    conflict_result = None
    try:
        conflict_result = await asyncio.to_thread(
            conflict_analyzer.analyze_conflict, transcripts, date)
    except Exception as e:
        app.logger.error(f"冲突分析失败: {str(e)}，尝试重试...")
        try:
            # 重试一次
            conflict_result = await asyncio.to_thread(
                conflict_analyzer.analyze_conflict, transcripts, date)
        except Exception as retry_e:
            app.logger.error(f"冲突分析重试失败: {str(retry_e)}")
            # 创建一个空的分析结果
            conflict_result = ConflictAnalysisOutput(scenes=[])

    # 行为分析
    behavior_analyzer = BehaviorAnalysis()
    behavior_result = None
    try:
        behavior_result = await asyncio.to_thread(
            behavior_analyzer.analyze_behavior, transcripts, date)
    except Exception as e:
        app.logger.error(f"行为分析失败: {str(e)}，尝试重试...")
        try:
            # 重试一次
            behavior_result = await asyncio.to_thread(
                behavior_analyzer.analyze_behavior, transcripts, date)
        except Exception as retry_e:
            app.logger.error(f"行为分析重试失败: {str(retry_e)}")
            # 创建一个空的分析结果
            behavior_result = BehaviorAnalysisOutput(scenes=[])

    # 创建冲突场景和行为场景模型实例
    conflict_scenes = []
    if conflict_result and hasattr(conflict_result, 'scenes'):
        for scene in conflict_result.scenes:
            try:
                conflict_scene = ConflictScene(
                    trigger_event=scene.trigger,
                    process=scene.process,
                    conflict_type=scene.conflict_type.value,
                    severity=scene.severity.value,
                    dt=scene.dt,
                    analysis_id=analysis_id
                )
                conflict_scenes.append(conflict_scene)
            except Exception as e:
                app.logger.error(f"创建冲突场景失败: {str(e)}")

    # 创建行为场景模型实例列表
    behavior_scenes = []
    if behavior_result and hasattr(behavior_result, 'scenes'):
        for scene in behavior_result.scenes:
            try:
                behavior_scene = BehaviorScene(
                    description=scene.description,
                    code=scene.code.value,
                    type=scene.type.value,
                    dt=scene.dt,
                    analysis_id=analysis_id
                )
                behavior_scenes.append(behavior_scene)
            except Exception as e:
                app.logger.error(f"创建行为场景失败: {str(e)}")

    # 分批保存到数据库，避免单个事务过大
    try:
        # 保存冲突场景
        if conflict_scenes:
            await asyncio.to_thread(lambda: (
                db.session.add_all(conflict_scenes),
                db.session.commit()
            ))
            app.logger.info(f"保存 {len(conflict_scenes)} 个冲突场景成功")
            
        # 保存行为场景
        if behavior_scenes:
            await asyncio.to_thread(lambda: (
                db.session.add_all(behavior_scenes),
                db.session.commit()
            ))
            app.logger.info(f"保存 {len(behavior_scenes)} 个行为场景成功")
            
    except Exception as e:
        app.logger.error(f"保存场景到数据库失败: {str(e)}，尝试重试...")
        try:
            # 回滚后重试
            await asyncio.to_thread(db.session.rollback)
            
            # 批量保存冲突场景
            if conflict_scenes:
                for batch in batch_items(conflict_scenes, 10):  # 每10个一批
                    await asyncio.to_thread(lambda: (
                        db.session.add_all(batch),
                        db.session.commit()
                    ))
                
            # 批量保存行为场景
            if behavior_scenes:
                for batch in batch_items(behavior_scenes, 10):  # 每10个一批
                    await asyncio.to_thread(lambda: (
                        db.session.add_all(batch),
                        db.session.commit()
                    ))
                    
            app.logger.info("批量保存场景成功")
            
        except Exception as retry_e:
            app.logger.error(f"批量保存场景重试失败: {str(retry_e)}")
            # 回滚事务
            await asyncio.to_thread(db.session.rollback)
    
    return conflict_result, behavior_result

# 添加批量处理辅助函数
def batch_items(items, batch_size):
    """
    将列表分成固定大小的批次
    
    参数:
        items: 要分批的列表
        batch_size: 每批的大小
        
    返回:
        批次生成器
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

# 为报告生成函数添加健壮性
async def generate_reports(app, file_id, new_analysis, audio):
    """
    异步生成并保存报告文件，提供健壮的错误处理
    """
    app.logger.info(f"开始为文件 {file_id} 生成报告文件")

    reports_dir = os.path.join('static', 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    # 定义输出文件路径
    output_paths = {
        'part0': os.path.join(reports_dir, f'output0_{file_id}.html'),
        'part1': os.path.join(reports_dir, f'output1_{file_id}.html'),
        'part2': os.path.join(reports_dir, f'output2_{file_id}.html'),
        'part3': os.path.join(reports_dir, f'output3_{file_id}.html'),
        'history2': os.path.join(reports_dir, f'history2_{file_id}.html')
    }

    # 准备所有报告的生成信息
    contents_info = [
        # 家庭概览 (part0.html)
        {
            'content': new_analysis.family_overview + f" file_id={file_id}",
            'model_class': EducationReport,
            'template_name': 'part0.html',
            'output_path': output_paths['part0']
        },
        # 对话分析 (part1.html)
        {
            'content': new_analysis.conversation_analysis + f" file_id={file_id}",
            'model_class': ContentModel,
            'template_name': 'part1.html',
            'output_path': output_paths['part1']
        },
        # 行为分析 (part2.html)
        {
            'content': new_analysis.behavior_analysis_result + new_analysis.emotion_analysis_result + new_analysis.reflection_questions + f" file_id={file_id}",
            'model_class': BehaviorAnalysisModel,
            'template_name': 'part2.html',
            'output_path': output_paths['part2']
        },
        # 策略生成 (part3.html)
        {
            'content': new_analysis.strategy_generation_result + f" file_id={file_id}",
            'model_class': StrategyContentModel,
            'template_name': 'part3.html',
            'output_path': output_paths['part3']
        },
        # 历史回顾 - 亲子画像 (history2.html) - 使用新模型
        {
            'content': new_analysis.family_overview + f" file_id={file_id}", # 仍然使用 family_overview 作为输入源
            'model_class': TutoringPortraitModel, # 指定新模型
            'template_name': 'history2.html',
            'output_path': output_paths['history2']
        }
    ]

    # 更新进度到75%，表示开始生成报告
    audio.progress = 75
    await asyncio.to_thread(db.session.commit)
    
    app.logger.info(f"开始并行生成所有报告...")
    success_count = 0
    failed_reports = []
    
    try:
        # 并行生成所有报告
        await generate_multiple_html_async(contents_info)
        app.logger.info(f"所有报告并行生成成功")
        success_count = len(contents_info)
    except Exception as e:
        app.logger.error(f"并行生成报告失败: {e}")
        app.logger.info(f"回退到逐个生成报告...")
        
        # 回退到逐个同步生成
        for info in contents_info:
            try:
                app.logger.info(f"正在生成 {info['template_name']} 报告")
                generate_html_from_context(
                    content=info['content'],
                    model_class=info['model_class'],
                    template_name=info['template_name'],
                    output_path=info['output_path']
                )
                app.logger.info(f"{info['template_name']} 报告生成完成")
                success_count += 1
            except Exception as single_e:
                app.logger.error(f"生成 {info['template_name']} 报告失败: {single_e}")
                failed_reports.append(info['template_name'])
                # 再尝试一次
                try:
                    app.logger.info(f"重试生成 {info['template_name']} 报告")
                    generate_html_from_context(
                        content=info['content'],
                        model_class=info['model_class'],
                        template_name=info['template_name'],
                        output_path=info['output_path']
                    )
                    app.logger.info(f"{info['template_name']} 报告重试生成完成")
                    # 如果重试成功，从失败列表中移除
                    if info['template_name'] in failed_reports:
                         failed_reports.remove(info['template_name'])
                    # success_count 已经在第一次尝试失败时未增加，重试成功也不需要再加
                except Exception as retry_e:
                    app.logger.error(f"重试生成 {info['template_name']} 报告也失败: {retry_e}")
                    # 确保失败的报告仍在列表中
                    if info['template_name'] not in failed_reports:
                        failed_reports.append(info['template_name'])
    
    # 更新进度到100%并设置状态为完成
    audio.progress = 100
    audio.status = StatusEnum.completed
    await asyncio.to_thread(db.session.commit)
    
    if failed_reports:
        app.logger.warning(f"部分报告生成失败: {', '.join(failed_reports)}, 但任务仍标记为完成")
    else:
        app.logger.info(f"分析任务完成: file_id={file_id}，成功生成报告数量: {len(contents_info)}/{len(contents_info)}") # 修正成功计数逻辑

async def save_conflict_result_json(app, user_id, date, conflict_result):
    """
    异步保存冲突分析结果到JSON文件
    """
    app.logger.info(f"开始保存冲突分析结果到JSON文件: user_id={user_id}, 日期={date}")
    results_dir = os.path.join('static', 'transcripts')
    os.makedirs(results_dir, exist_ok=True)
    conflict_filename = f"{user_id}_{date}_conflict.json"
    conflict_path = os.path.join(results_dir, conflict_filename)
    
    async def write_conflict():
        with open(conflict_path, 'w', encoding='utf-8') as f:
            json.dump(conflict_result, f, ensure_ascii=False, indent=4)
    
    await asyncio.to_thread(write_conflict)
    app.logger.info(f"冲突分析结果已保存到: {conflict_path}")
    return conflict_path

async def save_behavior_result_json(app, user_id, date, behavior_result):
    """
    异步保存行为分析结果到JSON文件
    """
    app.logger.info(f"开始保存行为分析结果到JSON文件: user_id={user_id}, 日期={date}")
    results_dir = os.path.join('static', 'transcripts')
    os.makedirs(results_dir, exist_ok=True)
    behavior_filename = f"{user_id}_{date}_behavior.json"
    behavior_path = os.path.join(results_dir, behavior_filename)
    
    async def write_behavior():
        with open(behavior_path, 'w', encoding='utf-8') as f:
            json.dump(behavior_result, f, ensure_ascii=False, indent=4)
    
    await asyncio.to_thread(write_behavior)
    app.logger.info(f"行为分析结果已保存到: {behavior_path}")
    return behavior_path

def normalize_transcript(transcript):
    """
    标准化转写结果格式，确保返回一个字典列表，
    每个字典包含 'id', 'speaker', 'content' 字段
    
    参数:
        transcript: 转写结果，可能是任何格式
        
    返回:
        List[dict]: 标准化后的转写结果
    """
    # 如果输入为None，返回空列表
    if transcript is None:
        return []
        
    # 如果不是列表，尝试转换为列表
    if not isinstance(transcript, list):
        if isinstance(transcript, dict):
            transcript = [transcript]
        else:
            try:
                # 尝试解析JSON字符串
                if isinstance(transcript, str):
                    transcript = json.loads(transcript)
                    if not isinstance(transcript, list):
                        transcript = [transcript]
                else:
                    # 其他类型，转换为单元素列表
                    transcript = [{"content": str(transcript)}]
            except:
                # 解析失败，创建包含原始内容的单元素列表
                transcript = [{"content": str(transcript)}]
    
    # 标准化每个元素
    normalized = []
    for i, item in enumerate(transcript):
        if isinstance(item, dict):
            # 确保包含所需字段
            normalized_item = {
                "id": item.get("id", i),
                "speaker": item.get("speaker", "unknown"),
                "content": item.get("content", "")
            }
            normalized.append(normalized_item)
        else:
            # 非字典元素，创建包含原始内容的字典
            normalized.append({
                "id": i,
                "speaker": "unknown",
                "content": str(item)
            })
    
    return normalized
