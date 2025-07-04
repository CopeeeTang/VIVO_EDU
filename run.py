import os
from dotenv import load_dotenv

# 必须在导入app之前加载环境变量
# 因为config.py在导入时就会读取环境变量
if os.path.exists('local.env'):
    load_dotenv('local.env')
    print("已加载本地环境配置文件: local.env")
elif os.path.exists('.env'):
    load_dotenv('.env')
    print("已加载环境配置文件: .env")
else:
    print("警告: 未找到环境配置文件，将使用默认配置")

# 在加载环境变量后再导入app
from app import create_app

app = create_app()

if __name__ == "__main__":
    # 本地开发时的运行配置
    app.run(
        debug=True,
        host='0.0.0.0',  # 允许外部访问
        port=5000,
        ssl_context='adhoc'  # 保持SSL支持
    )