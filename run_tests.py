#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试运行脚本
提供便捷的测试选项
"""

import os
import sys
import subprocess
import argparse

# 加载本地环境变量
if os.path.exists('local.env'):
    try:
        from dotenv import load_dotenv
        load_dotenv('local.env')
        print("✅ 已加载 local.env 配置文件")
    except ImportError:
        print("⚠️  未安装 python-dotenv，将使用系统环境变量")
        print("   如需使用 local.env，请运行: pip install python-dotenv")


def run_module_tests():
    """运行模块测试 (Python脚本)"""
    print("🔧 启动模块测试...")
    try:
        # 直接运行Python测试脚本
        subprocess.run([sys.executable, 'test_modules_simple.py'])
    except Exception as e:
        print(f"❌ 模块测试失败: {e}")


def run_workflow_tests():
    """运行工作流测试"""
    print("🚀 启动工作流测试...")
    try:
        subprocess.run([sys.executable, 'test_workflow.py'])
    except Exception as e:
        print(f"❌ 工作流测试失败: {e}")


def check_environment():
    """检查环境配置"""
    print("🔍 环境配置检查")
    print("="*50)
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查必要模块
    required_modules = [
        'flask', 'requests', 'celery', 'sqlalchemy',
        'asyncio', 'logging', 'json'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            missing_modules.append(module)
    
    # 检查API密钥
    api_keys = [
        'VIVO_BLUE_LM_APP_ID', 'VIVO_BLUE_LM_APP_KEY',  # 从local.env中的实际密钥名
        'VIVO_AUDIO_APP_ID', 'VIVO_AUDIO_APP_KEY',
        'ZHIZENGZENG_API_KEY', 'DEEPSEEK_API_KEY', 'OPENAI_API_KEY'
    ]
    
    print("\nAPI密钥配置:")
    configured = 0
    for key in api_keys:
        if os.getenv(key):
            print(f"✅ {key}")
            configured += 1
        else:
            print(f"❌ {key}")
    
    print(f"\n配置状态: {configured}/{len(api_keys)} 个API密钥已配置")
    
    if missing_modules:
        print(f"\n⚠️  缺少模块: {', '.join(missing_modules)}")
        print("请运行: pip install -r requirements.txt")
    
    if configured == 0:
        print("\n⚠️  未配置任何API密钥，测试可能失败")
        print("请在环境变量中配置相应的API密钥")


def show_help():
    """显示帮助信息"""
    help_text = """
🎯 VIVO_EDU 测试工具

可用命令:
  python run_tests.py workflow    - 运行工作流测试
  python run_tests.py check       - 检查环境配置
  python run_tests.py all         - 运行所有测试
  python run_tests.py help        - 显示此帮助信息

测试文件说明:
  🔄 test_workflow.py          - 端到端工作流测试

环境配置要求:
  🔑 API密钥配置:
    - VIVO_BLUE_LM_APP_ID, VIVO_BLUE_LM_APP_KEY
    - VIVO_AUDIO_APP_ID, VIVO_AUDIO_APP_KEY  
    - ZHIZENGZENG_API_KEY
    - DEEPSEEK_API_KEY
    - OPENAI_API_KEY

  📦 Python依赖:
    - pip install -r requirements.txt

使用示例:
  # 检查环境配置
  python run_tests.py check
  
  # 运行完整工作流测试
  python run_tests.py workflow
"""
    print(help_text)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='VIVO_EDU 测试工具')
    parser.add_argument('command', 
                       choices=['modules', 'workflow', 'check', 'all', 'help'],
                       help='要执行的测试命令')
    
    if len(sys.argv) == 1:
        show_help()
        return
    
    args = parser.parse_args()
    
    if args.command == 'help':
        show_help()
    elif args.command == 'check':
        check_environment()
    elif args.command == 'workflow':
        run_workflow_tests()
    elif args.command == 'all':
        print("🎯 运行完整测试套件")
        print("="*50)
        check_environment()
        print("\n" + "="*50)
        run_workflow_tests()
        print("\n" + "="*50)
        run_module_tests()
    else:
        show_help()


if __name__ == "__main__":
    main() 