#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIVO_EDU项目工作流测试
测试整体的音频处理和分析流程
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
sys.path.append(os.path.abspath('.'))

# 加载本地环境变量
if os.path.exists('local.env'):
    try:
        from dotenv import load_dotenv
        load_dotenv('local.env')
        print("✅ 已加载 local.env 配置文件")
    except ImportError:
        print("⚠️  未安装 python-dotenv，将使用系统环境变量")
        print("   如需使用 local.env，请运行: pip install python-dotenv")

# 导入项目模块 - 直接导入我们需要测试的模块文件
try:
    from app.utils.api_clients import api_client, chat_with_fallback, chat_with_fallback_async
    from app.utils.parent_child_profiling import analyze_audio  
    from app.utils.conflict_behavior_analysis import analyze_conflict_and_behavior
    print("✅ 核心模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("尝试直接导入模块文件...")
    # 如果通过app包导入失败，尝试直接导入
    sys.path.insert(0, 'app/utils')
    try:
        import api_clients
        import parent_child_profiling 
        import conflict_behavior_analysis
        
        # 重新赋值函数引用
        api_client = api_clients.api_client
        chat_with_fallback = api_clients.chat_with_fallback
        chat_with_fallback_async = api_clients.chat_with_fallback_async
        analyze_audio = parent_child_profiling.analyze_audio
        analyze_conflict_and_behavior = conflict_behavior_analysis.analyze_conflict_and_behavior
        
        print("✅ 直接导入模块文件成功")
    except Exception as direct_import_error:
        print(f"❌ 直接导入也失败: {direct_import_error}")
        print("请检查模块文件是否存在和语法正确")

# 音频转录功能单独处理
try:
    from app.utils.request_api import transcribe_audio
    print("✅ 音频转录模块导入成功")
except ImportError:
    print("⚠️  音频转录模块导入失败，将跳过相关测试")
    transcribe_audio = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WorkflowTester:
    """工作流测试器"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        
    def log_result(self, step: str, success: bool, details: str = ""):
        """记录测试结果"""
        self.results[step] = {
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"{step}: {status} - {details}")
        
        if not success:
            self.errors.append(f"{step}: {details}")
    
    def test_environment(self):
        """测试环境配置"""
        print("\n" + "="*60)
        print("🔧 环境配置测试")
        print("="*60)
        
        # 检查API密钥配置
        api_keys = [
            'VIVO_BLUE_LM_APP_ID', 'VIVO_BLUE_LM_APP_KEY',  # local.env中的实际密钥名
            'VIVO_AUDIO_APP_ID', 'VIVO_AUDIO_APP_KEY',
            'ZHIZENGZENG_API_KEY', 'DEEPSEEK_API_KEY', 'OPENAI_API_KEY'
        ]
        
        configured_keys = []
        for key in api_keys:
            if os.getenv(key):
                configured_keys.append(key)
                
        self.log_result(
            "环境配置检查",
            len(configured_keys) > 0,
            f"已配置 {len(configured_keys)}/{len(api_keys)} 个API密钥: {configured_keys}"
        )
        
        # 检查API客户端可用性
        try:
            best_client = api_client.get_best_available_client()
            self.log_result(
                "API客户端初始化",
                best_client is not None,
                f"最佳可用客户端: {best_client}"
            )
        except Exception as e:
            self.log_result("API客户端初始化", False, str(e))
    
    def test_api_connectivity(self):
        """测试API连接性"""
        print("\n" + "="*60)
        print("🌐 API连接性测试")
        print("="*60)
        
        try:
            response = chat_with_fallback(
                "你是一个AI助手",
                "请回答'连接测试成功'，不要有其他内容"
            )
            
            self.log_result(
                "API基本连接测试",
                "连接测试成功" in response or "成功" in response,
                f"响应: {response[:100]}"
            )
        except Exception as e:
            self.log_result("API基本连接测试", False, str(e))
    
    def test_transcription_workflow(self):
        """测试转录工作流（需要真实音频文件）"""
        print("\n" + "="*60)
        print("🎵 音频转录工作流测试")
        print("="*60)
        
        # 查找测试音频文件
        test_audio_paths = [
            "uploads/17.m4a",  # 用户提供的测试音频
            "uploads/test.wav",
            "uploads/test.mp3",
            "static/test.wav"
        ]
        
        test_audio = None
        for path in test_audio_paths:
            if os.path.exists(path):
                test_audio = path
                break
        
        if not test_audio:
            self.log_result(
                "音频文件检查",
                False,
                "未找到测试音频文件，请确保 uploads/test_30s.m4a 存在"
            )
            return
        
        try:
            # 测试音频转录
            transcript_result = transcribe_audio(test_audio)
            
            self.log_result(
                "音频转录测试",
                transcript_result is not None,
                f"转录结果类型: {type(transcript_result)}"
            )
            
            return transcript_result
            
        except Exception as e:
            self.log_result("音频转录测试", False, str(e))
            return None
    
    def test_analysis_workflow(self, transcript_data=None):
        """测试分析工作流"""
        print("\n" + "="*60)
        print("🔍 分析工作流测试")
        print("="*60)
        
        # 测试用例：如果没有提供转录数据，使用示例数据
        if transcript_data is None:
            transcript_data = {
                "transcript": "妈妈：你今天作业做完了吗？\n孩子：还没有，我想先玩一会儿游戏。\n妈妈：不行，必须先做作业才能玩游戏。\n孩子：为什么总是要先做作业？\n妈妈：因为学习很重要，你要有责任心。",
                "speakers": ["妈妈", "孩子"]
            }
        
        # 创建输出记录字典
        analysis_outputs = {
            "转录结果": transcript_data,
            "亲子画像分析": None,
            "冲突行为分析": None,
            "场景重建": None,
            "知识库检索": None
        }
        
        # 测试亲子画像分析
        try:
            if 'analyze_audio' in globals():
                profile_result = analyze_audio(transcript_data)
                analysis_outputs["亲子画像分析"] = profile_result
                self.log_result(
                    "亲子画像分析",
                    profile_result is not None,
                    f"分析结果: {type(profile_result)}"
                )
            else:
                self.log_result("亲子画像分析", False, "模块未加载")
        except Exception as e:
            self.log_result("亲子画像分析", False, str(e))
        
        # 测试冲突行为分析
        try:
            if 'analyze_conflict_and_behavior' in globals():
                # 添加默认日期参数，转换为字符串格式
                import datetime
                today = datetime.date.today().strftime('%Y%m%d')  # 转换为字符串
                conflict_result = analyze_conflict_and_behavior(transcript_data, today)
                analysis_outputs["冲突行为分析"] = conflict_result
                self.log_result(
                    "冲突行为分析",
                    conflict_result is not None,
                    f"分析结果: {type(conflict_result)}"
                )
            else:
                self.log_result("冲突行为分析", False, "模块未加载")
        except Exception as e:
            self.log_result("冲突行为分析", False, str(e))
        
        # 测试场景重建
        try:
            from app.utils.enhanced_scenery_rebuild import rebuild_scene
            
            # 转换数据格式为List[Dict]
            if isinstance(transcript_data, dict) and 'transcript' in transcript_data:
                # 如果有结构化的转录数据，使用它
                if isinstance(transcript_data, dict) and len(transcript_data) > 0:
                    # 假设transcript_data是最终的JSON结果，包含id, speaker, content等字段
                    if 'transcript' in transcript_data:
                        # 如果是原始格式
                        scenery_input = [{"speaker": "Speaker 1", "content": transcript_data['transcript']}]
                    else:
                        # 如果已经是处理过的格式
                        scenery_input = [transcript_data] if not isinstance(transcript_data, list) else transcript_data
                else:
                    scenery_input = [{"speaker": "Speaker 1", "content": str(transcript_data)}]
            else:
                # 简单格式转换
                scenery_input = [{"speaker": "Speaker 1", "content": str(transcript_data)}]
            
            scenery_result = rebuild_scene(scenery_input)
            analysis_outputs["场景重建"] = scenery_result
            self.log_result(
                "场景重建",
                scenery_result is not None and "error" not in scenery_result,
                f"场景重建结果: {type(scenery_result)}"
            )
        except Exception as e:
            self.log_result("场景重建", False, str(e))
        
        # 测试知识库检索
        try:
            from app.utils.enhanced_knowledge_base import get_educational_advice
            
            # 转换数据格式为List[Dict]，get_educational_advice期望这种格式
            if isinstance(transcript_data, list):
                # 如果已经是列表格式
                kb_input = transcript_data
            elif isinstance(transcript_data, dict):
                if 'transcript' in transcript_data:
                    # 原始格式，转换为list
                    kb_input = [{"speaker": "Speaker 1", "content": transcript_data['transcript']}]
                else:
                    # 如果是单个字典，转换为列表
                    kb_input = [transcript_data]
            else:
                # 字符串或其他格式
                kb_input = [{"speaker": "Speaker 1", "content": str(transcript_data)}]
            
            # 确保列表中的每个元素都有必要的字段
            formatted_kb_input = []
            for item in kb_input:
                if isinstance(item, dict):
                    formatted_item = {
                        "speaker": item.get("speaker", "Speaker 1"),
                        "content": item.get("content", str(item))
                    }
                else:
                    formatted_item = {
                        "speaker": "Speaker 1", 
                        "content": str(item)
                    }
                formatted_kb_input.append(formatted_item)
            
            kb_result = get_educational_advice(formatted_kb_input)
            analysis_outputs["知识库检索"] = kb_result
            self.log_result(
                "知识库检索",
                kb_result is not None and "error" not in kb_result,
                f"知识库检索结果: {type(kb_result)}"
            )
        except Exception as e:
            self.log_result("知识库检索", False, str(e))
        

        
        # 保存详细输出结果
        self.save_detailed_outputs(analysis_outputs)
        
        return analysis_outputs
    
    def save_detailed_outputs(self, analysis_outputs: Dict[str, Any]):
        """保存详细输出结果到文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 创建输出目录
            output_dir = "workflow_outputs"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 保存JSON格式的完整结果
            json_file = os.path.join(output_dir, f"workflow_output_{timestamp}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_outputs, f, ensure_ascii=False, indent=2, default=str)
            
            # 保存Markdown格式的易读结果
            md_file = os.path.join(output_dir, f"workflow_output_{timestamp}.md")
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f"# 工作流测试输出报告\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 添加模块输出数据结构说明
                f.write("## 📋 各模块输出数据结构说明\n\n")
                f.write("### 🎵 转录结果\n")
                f.write("```\n格式: List[Dict]\n")
                f.write("字段: id, speaker, start_time, end_time, content\n")
                f.write("示例: [{'id': 0, 'speaker': '妈妈', 'content': '你今天作业做完了吗？'}]\n```\n\n")
                
                f.write("### 👥 亲子画像分析\n")
                f.write("```\n格式: Dict\n")
                f.write("字段: 家长画像, 孩子画像, 亲子关系评估\n")
                f.write("包含情感状态、沟通方式、教育风格等分析\n```\n\n")
                
                f.write("### ⚡ 冲突行为分析\n")
                f.write("```\n格式: Dict\n")
                f.write("字段: 冲突识别, 行为模式, 建议措施\n")
                f.write("分析对话中的冲突点和行为特征\n```\n\n")
                
                f.write("### 🎬 场景重建\n")
                f.write("```\n格式: Dict\n")
                f.write("字段: 场景数量, 场景摘要[{场景ID, 事件, 变化, 关键细节, 时间范围, 参与者, 情感基调}]\n")
                f.write("重建家庭教育场景的结构化描述\n```\n\n")
                
                f.write("### 📚 知识库检索\n")
                f.write("```\n格式: Dict\n")
                f.write("字段: advice, context, search_results\n")
                f.write("基于知识库提供的教育建议和相关理论\n```\n\n")
                
                f.write("## 📊 详细输出结果\n\n")
                
                for module_name, result in analysis_outputs.items():
                    f.write(f"### {module_name}\n\n")
                    
                    if result is None:
                        f.write("*无输出结果*\n\n")
                    elif isinstance(result, dict):
                        f.write("```json\n")
                        f.write(json.dumps(result, ensure_ascii=False, indent=2, default=str))
                        f.write("\n```\n\n")
                    elif isinstance(result, str):
                        f.write(f"```\n{result}\n```\n\n")
                    else:
                        f.write(f"```\n{str(result)}\n```\n\n")
                
                f.write(f"## 🧪 测试结果摘要\n\n")
                f.write("| 模块 | 状态 | 详情 |\n")
                f.write("|------|------|------|\n")
                
                for step, info in self.results.items():
                    status = "✅ 成功" if info['success'] else "❌ 失败"
                    f.write(f"| {step} | {status} | {info['details']} |\n")
            
            print(f"✅ 详细输出已保存到:")
            print(f"   - JSON格式: {json_file}")
            print(f"   - Markdown格式: {md_file}")
            
        except Exception as e:
            print(f"❌ 保存详细输出失败: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行工作流测试...")
        
        # 1. 环境配置测试
        self.test_environment()
        
        # 2. API连接性测试
        self.test_api_connectivity()
        
        # 3. 转录工作流测试
        transcript_result = self.test_transcription_workflow()
        
        # 4. 分析工作流测试
        analysis_result = self.test_analysis_workflow(transcript_result)
        
        # 5. 输出总结
        self.print_summary()
        
        return self.results
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📊 测试总结")
        print("="*60)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results.values() if r['success'])
        failed_tests = total_tests - successful_tests
        
        print(f"总测试数: {total_tests}")
        print(f"成功: {successful_tests}")
        print(f"失败: {failed_tests}")
        
        if self.errors:
            print(f"\n❌ 错误详情:")
            for error in self.errors:
                print(f"  - {error}")
        
        if successful_tests == total_tests:
            print("\n🎉 所有测试都成功完成!")
        else:
            print(f"\n⚠️  {failed_tests} 个测试失败，请检查错误详情")


def main():
    """主函数"""
    tester = WorkflowTester()
    results = tester.run_all_tests()
    
    # 保存测试结果
    report_file = "workflow_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📋 测试报告已保存到: {report_file}")
    
    return results


if __name__ == "__main__":
    main()