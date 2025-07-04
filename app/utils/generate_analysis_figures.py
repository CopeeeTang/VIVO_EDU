'''
该py文件根据后端数据生成前端特定的图片，包括冲突分析和行为分析
'''

import pandas as pd
import warnings
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import seaborn as sns
from matplotlib import font_manager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import ConflictScene, BehaviorScene, AudioFile, AnalysisResult
from config import Config
import os

def setup_plot_environment():
    """
    设置绘图环境，返回字体和图片路径。
    """
    warnings.filterwarnings('ignore')
    font_prop = font_manager.FontProperties(fname=os.path.join(Config.PATH_FONT))
    path_img = os.path.join(Config.PATH_IMG)
    
    # 确保图片输出目录存在
    os.makedirs(path_img, exist_ok=True)
    
    return font_prop, path_img

def save_figure(plt, path_img, filename, user_id):
    """
    保存图片为PNG格式，返回文件路径。
    """
    pdf_path = os.path.join(path_img, f'{filename}_{user_id}.pdf')
    png_path = os.path.join(path_img, f'{filename}_{user_id}.png')
    
    # 仅保存PNG格式，如果需要PDF格式，取消下面的注释
    # plt.savefig(pdf_path, bbox_inches='tight')
    plt.savefig(png_path, bbox_inches='tight')
    plt.close()
    
    return pdf_path, png_path

def plot_conflict_distribution(df_filtered, path_img, font_prop, user_id):
    """
    绘制冲突类型分布图
    """
    if df_filtered.empty:
        return None, None
        
    plt.figure(figsize=(6, 4))
    sns.countplot(x='conflict_type', data=df_filtered, palette='viridis')
    plt.xlabel('冲突类型', fontsize=12, fontproperties=font_prop)
    plt.ylabel('数量', fontsize=12, fontproperties=font_prop)
    plt.xticks(rotation=90, fontproperties=font_prop)
    # 确保Y轴只显示整数值
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    max_y = df_filtered['conflict_type'].value_counts().max() if not df_filtered.empty else 0
    plt.ylim(0, max_y + 1)
    plt.tight_layout()
    
    return save_figure(plt, path_img, 'conflict_distribution', user_id)

def plot_conflict_trend(df_grouped, path_img, font_prop, user_id):
    """
    绘制冲突趋势图
    """
    if df_grouped.empty:
        return None, None
    
    # 确保日期格式正确
    try:
        if 'dt' in df_grouped.columns and not pd.api.types.is_datetime64_any_dtype(df_grouped['dt']):
            # 添加错误处理，排除非标准日期格式
            mask = df_grouped['dt'].str.match(r'^\d{8}$')
            if not all(mask):
                # 对于非标准格式的日期，使用当前日期替代
                import datetime
                current_date = datetime.datetime.now().strftime('%Y%m%d')
                df_grouped.loc[~mask, 'dt'] = current_date
            
            # 转换日期格式
            df_grouped['dt'] = pd.to_datetime(df_grouped['dt'], format='%Y%m%d', errors='coerce')
            # 处理转换失败的日期
            df_grouped = df_grouped.dropna(subset=['dt'])
            
        # 设置更友好的日期格式显示
        if 'dt' in df_grouped.columns and pd.api.types.is_datetime64_any_dtype(df_grouped['dt']):
            df_grouped['display_dt'] = df_grouped['dt'].dt.strftime('%m月%d日')
        else:
            df_grouped['display_dt'] = df_grouped['dt']
            
        # 确保有星期几信息
        if 'weekday' not in df_grouped.columns and not df_grouped.empty:
            df_grouped['weekday'] = df_grouped['dt'].dt.strftime('%A')
            weekday_map = {
                'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三', 
                'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六', 
                'Sunday': '周日'
            }
            df_grouped['weekday'] = df_grouped['weekday'].map(weekday_map)
    except Exception as e:
        print(f"处理日期格式时出错: {str(e)}")
        return None, None
        
    # 如果处理后数据为空，则返回
    if df_grouped.empty:
        return None, None
    
    plt.figure(figsize=(6, 4))
    
    # 使用柱状图显示每天的冲突数
    sns.barplot(x='weekday' if 'weekday' in df_grouped.columns else 'display_dt', 
                y='total_conflicts', data=df_grouped, color='#b5cd81')
    
    # 添加折线图，只显示每天一个点(总和)
    plt.plot(df_grouped.index, df_grouped['total_conflicts'], 
             color='black', marker='o', linestyle='-', linewidth=2, markersize=8)
    
    plt.xlabel('星期', fontsize=12, fontproperties=font_prop)
    plt.ylabel('总冲突数', fontsize=12, fontproperties=font_prop)
    plt.xticks(rotation=0, fontproperties=font_prop)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    max_y = df_grouped['total_conflicts'].max() if not df_grouped.empty else 0
    plt.ylim(0, max_y + 2)
    plt.tight_layout()
    
    return save_figure(plt, path_img, 'conflict_trend', user_id)

def plot_behavior_trend(df_grouped, path_img, font_prop, user_id):
    """
    绘制行为趋势图
    """
    if df_grouped.empty:
        return None, None
        
    # 确保日期格式正确
    try:
        if 'dt' in df_grouped.columns and not pd.api.types.is_datetime64_any_dtype(df_grouped['dt']):
            # 添加错误处理，排除非标准日期格式
            mask = df_grouped['dt'].str.match(r'^\d{8}$')
            if not all(mask):
                # 对于非标准格式的日期，使用当前日期替代
                import datetime
                current_date = datetime.datetime.now().strftime('%Y%m%d')
                df_grouped.loc[~mask, 'dt'] = current_date
            
            # 转换日期格式
            df_grouped['dt'] = pd.to_datetime(df_grouped['dt'], format='%Y%m%d', errors='coerce')
            # 处理转换失败的日期
            df_grouped = df_grouped.dropna(subset=['dt'])
        
        # 设置更友好的日期格式显示
        if 'dt' in df_grouped.columns and pd.api.types.is_datetime64_any_dtype(df_grouped['dt']):
            df_grouped['display_dt'] = df_grouped['dt'].dt.strftime('%m月%d日')
        else:
            df_grouped['display_dt'] = df_grouped['dt']
            
        # 确保有星期几信息
        if 'weekday' not in df_grouped.columns and not df_grouped.empty:
            df_grouped['weekday'] = df_grouped['dt'].dt.strftime('%A')
            weekday_map = {
                'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三', 
                'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六', 
                'Sunday': '周日'
            }
            df_grouped['weekday'] = df_grouped['weekday'].map(weekday_map)
    except Exception as e:
        print(f"处理日期格式时出错: {str(e)}")
        return None, None
        
    # 如果处理后数据为空，则返回
    if df_grouped.empty:
        return None, None
        
    plt.figure(figsize=(6, 4))
    
    # 使用柱状图显示每天的行为数
    sns.barplot(x='weekday' if 'weekday' in df_grouped.columns else 'display_dt', 
                y='total_behaviors', data=df_grouped, color='#8ab6d6')
    
    # 添加折线图，只显示每天一个点(总和)
    plt.plot(df_grouped.index, df_grouped['total_behaviors'], 
             color='black', marker='o', linestyle='-', linewidth=2, markersize=8)
    
    plt.xlabel('星期', fontsize=12, fontproperties=font_prop)
    plt.ylabel('总行为数', fontsize=12, fontproperties=font_prop)
    plt.xticks(rotation=0, fontproperties=font_prop)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    max_y = df_grouped['total_behaviors'].max() if not df_grouped.empty else 0
    plt.ylim(0, max_y + 2)
    plt.tight_layout()
    
    return save_figure(plt, path_img, 'behavior_trend', user_id)

def plot_severity_distribution(df_filtered, path_img, font_prop, user_id):
    """
    绘制冲突严重程度分布图
    """
    if df_filtered.empty:
        return None, None
        
    plt.figure(figsize=(6, 4))
    severity_order = ['低', '中', '高']
    sns.countplot(x='severity', data=df_filtered, order=severity_order, palette='YlOrRd')
    plt.xlabel('冲突严重程度', fontsize=12, fontproperties=font_prop)
    plt.ylabel('数量', fontsize=12, fontproperties=font_prop)
    plt.xticks(rotation=0, fontproperties=font_prop)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.tight_layout()
    
    return save_figure(plt, path_img, 'severity_distribution', user_id)

def plot_behavior_distribution(df_filtered, path_img, font_prop, user_id):
    """
    绘制行为类型分布图
    """
    if df_filtered.empty:
        return None, None
        
    plt.figure(figsize=(7, 3.5))
    colors = ['#49beaa', '#456990', '#d62728']  # 为不同行为类型设置颜色
    sns.countplot(x='code', data=df_filtered, hue='type', palette=colors)
    plt.xlabel('', fontsize=12, fontproperties=font_prop)
    plt.ylabel('数量', fontsize=12, fontproperties=font_prop)
    plt.xticks(rotation=90, fontproperties=font_prop)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    max_y = df_filtered['code'].value_counts().max() if not df_filtered.empty else 0
    plt.ylim(0, max_y + 1)
    # 添加图例
    plt.legend(title='', fontsize=10, bbox_to_anchor=(1.005, 1.025), loc='upper left', prop=font_prop)
    plt.tight_layout()
    
    return save_figure(plt, path_img, 'behavior_distribution', user_id)

def plot_behavior_type_distribution(df_filtered, path_img, font_prop, user_id):
    """
    绘制行为严重程度分布图
    """
    if df_filtered.empty:
        return None, None
        
    plt.figure(figsize=(6, 4))
    type_order = ['消极', '中性', '积极']
    sns.countplot(x='type', data=df_filtered, order=type_order, palette='BuPu')
    plt.xlabel('行为严重程度', fontsize=12, fontproperties=font_prop)
    plt.ylabel('数量', fontsize=12, fontproperties=font_prop)
    plt.xticks(rotation=0, fontproperties=font_prop)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.tight_layout()
    
    return save_figure(plt, path_img, 'behavior_type_distribution', user_id)

def plot_behavior_percentage_trend(df, path_img, font_prop, user_id):
    """
    绘制行为类型百分比趋势图
    """
    if df.empty:
        return None, None
    
    try:
        # 确保日期格式正确
        if 'dt' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['dt']):
            df['dt'] = pd.to_datetime(df['dt'], format='%Y%m%d', errors='coerce')
        
        # 添加格式化的日期显示
        df['display_dt'] = df['dt'].dt.strftime('%m月%d日')
        
        # 按日期和行为类型分组计数
        df_counts = df.groupby(['display_dt', 'type']).size().reset_index(name='count')
        
        # 创建透视表
        df_pivot = df_counts.pivot_table(index='display_dt', columns='type', values='count', fill_value=0)
        
        # 计算百分比
        df_pivot_percentage = df_pivot.div(df_pivot.sum(axis=1), axis=0)
        
        # 设置图形
        plt.figure(figsize=(7, 3.5))
        
        # 为每种行为类型设置颜色
        colors = ['#49beaa', '#456990', '#ef767a']
        
        # 绘制归一化的堆叠条形图
        df_pivot_percentage.plot(kind='bar', stacked=True, ax=plt.gca(), color=colors, alpha=0.65)
        
        # 为每种类型添加折线图
        for i, code_type in enumerate(df_pivot_percentage.columns):
            plt.plot(df_pivot_percentage.index, df_pivot_percentage[code_type], 
                    marker='o', linestyle='-', linewidth=2, color=colors[i], label=f'{code_type} (线)')
        
        # 自定义图表
        plt.xlabel('', fontproperties=font_prop)
        plt.ylabel('百分比', fontproperties=font_prop, fontsize=12)
        plt.xticks(rotation=0, fontproperties=font_prop, fontsize=12)
        plt.yticks(fontsize=10)
        plt.ylim(0, 1)
        
        # 图例设置
        plt.legend(title='', fontsize=10, bbox_to_anchor=(1.005, 1.025), loc='upper left', prop=font_prop)
        
        # 调整布局
        plt.tight_layout()
        
        return save_figure(plt, path_img, 'behavior_percentage_trend', user_id)
    except Exception as e:
        print(f"生成行为百分比趋势图时出错: {str(e)}")
        return None, None

def plot_conflict_type_trend(df, path_img, font_prop, user_id):
    """
    绘制冲突类型趋势图，类似于示例代码中的堆叠条形图和折线图组合
    """
    if df.empty:
        return None, None
    
    try:
        # 确保日期格式正确
        if 'dt' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['dt']):
            df['dt'] = pd.to_datetime(df['dt'], format='%Y%m%d', errors='coerce')
        
        # 添加格式化的日期显示
        df['display_dt'] = df['dt'].dt.strftime('%m月%d日')
        
        # 按日期和冲突类型分组计数
        df_grouped = df.groupby(['display_dt', 'conflict_type']).size().reset_index(name='total_conflicts')
        
        # 创建透视表
        df_pivot = df_grouped.pivot_table(index='display_dt', columns='conflict_type', values='total_conflicts', aggfunc='sum', fill_value=0)
        
        # 设置图形尺寸
        plt.figure(figsize=(8, 3.5))
        
        # 使用Spectral_r颜色方案
        colors = sns.color_palette("Spectral_r", len(df_pivot.columns))
        
        # 初始化条形图底部
        bottom = None
        
        # 为每种冲突类型创建堆叠条形图
        for i, conflict in enumerate(df_pivot.columns):
            if bottom is None:
                bottom = df_pivot[conflict].copy()
                plt.bar(df_pivot.index, bottom, label=conflict, color=colors[i])
            else:
                plt.bar(df_pivot.index, df_pivot[conflict], bottom=bottom, label=conflict, color=colors[i])
                bottom += df_pivot[conflict]
        
        # 计算每天的总和
        df_sum = df_pivot.sum(axis=1)
        
        # 添加总冲突数的折线图
        plt.plot(df_pivot.index, df_sum, label='总冲突数', color='black',
                marker='o', linestyle='-', linewidth=2)
        
        # 设置标签
        plt.ylabel('总冲突数', fontsize=12, fontproperties=font_prop)
        plt.xticks(rotation=0, fontsize=10, fontproperties=font_prop)
        
        # 添加图例
        plt.legend(title='', fontsize=10, bbox_to_anchor=(1.005, 1.025), loc='upper left', prop=font_prop)
        
        # 调整布局
        plt.tight_layout()
        
        return save_figure(plt, path_img, 'conflict_type_trend', user_id)
    except Exception as e:
        print(f"生成冲突类型趋势图时出错: {str(e)}")
        return None, None

def generate_conflict_figures(user_id):
    """
    生成特定用户的冲突分析图表。

    Args:
        user_id: 用户ID。

    Returns:
        dict: 返回生成的图片路径。
    """
    font_prop, path_img = setup_plot_environment()
    
    # 从数据库获取数据
    df = fetch_conflict_data(user_id)
    
    # 初始化结果字典
    result = {
        'conflict_distribution': {'pdf': None, 'png': None},
        'conflict_trend': {'pdf': None, 'png': None},
        'conflict_type_trend': {'pdf': None, 'png': None},
        'severity_distribution': {'pdf': None, 'png': None}
    }
    
    if df.empty:
        return result
    
    # 数据预处理 - 确保dt字段为字符串
    df['dt'] = df['dt'].astype(str)
    
    # 绘制冲突类型分布图
    conflict_distribution_pdf, conflict_distribution_png = plot_conflict_distribution(df, path_img, font_prop, user_id)
    result['conflict_distribution'] = {'pdf': conflict_distribution_pdf, 'png': conflict_distribution_png}
    
    # 按日期分组并计数 - 修改为按日期计数总冲突数
    df_grouped = df.groupby('dt').size().reset_index(name='total_conflicts')
    
    # 绘制冲突分布趋势图
    conflict_trend_pdf, conflict_trend_png = plot_conflict_trend(df_grouped, path_img, font_prop, user_id)
    result['conflict_trend'] = {'pdf': conflict_trend_pdf, 'png': conflict_trend_png}
    
    # 绘制冲突类型趋势图
    conflict_type_trend_pdf, conflict_type_trend_png = plot_conflict_type_trend(df, path_img, font_prop, user_id)
    result['conflict_type_trend'] = {'pdf': conflict_type_trend_pdf, 'png': conflict_type_trend_png}
    
    # 绘制冲突严重程度分布图
    severity_distribution_pdf, severity_distribution_png = plot_severity_distribution(df, path_img, font_prop, user_id)
    result['severity_distribution'] = {'pdf': severity_distribution_pdf, 'png': severity_distribution_png}
    
    return result

def generate_behavior_figures(user_id):
    """
    生成特定用户的行为分析图表。

    Args:
        user_id: 用户ID。

    Returns:
        dict: 返回生成的图片路径。
    """
    font_prop, path_img = setup_plot_environment()
    
    # 从数据库获取数据
    df = fetch_behavior_data(user_id)
    
    # 初始化结果字典
    result = {
        'behavior_distribution': {'pdf': None, 'png': None},
        'behavior_trend': {'pdf': None, 'png': None},
        'behavior_type_distribution': {'pdf': None, 'png': None},
        'behavior_percentage_trend': {'pdf': None, 'png': None}
    }
    
    if df.empty:
        return result
    
    # 数据预处理 - 确保dt字段为字符串
    df['dt'] = df['dt'].astype(str)
    
    # 绘制行为类型分布图
    behavior_distribution_pdf, behavior_distribution_png = plot_behavior_distribution(df, path_img, font_prop, user_id)
    result['behavior_distribution'] = {'pdf': behavior_distribution_pdf, 'png': behavior_distribution_png}
    
    # 按日期分组并计数 - 修改为按日期计数总行为数
    df_grouped = df.groupby('dt').size().reset_index(name='total_behaviors')
    
    # 绘制行为分布趋势图
    behavior_trend_pdf, behavior_trend_png = plot_behavior_trend(df_grouped, path_img, font_prop, user_id)
    result['behavior_trend'] = {'pdf': behavior_trend_pdf, 'png': behavior_trend_png}
    
    # 绘制行为严重程度分布图
    behavior_type_pdf, behavior_type_png = plot_behavior_type_distribution(df, path_img, font_prop, user_id)
    result['behavior_type_distribution'] = {'pdf': behavior_type_pdf, 'png': behavior_type_png}
    
    # 绘制行为类型百分比趋势图
    behavior_percentage_pdf, behavior_percentage_png = plot_behavior_percentage_trend(df, path_img, font_prop, user_id)
    result['behavior_percentage_trend'] = {'pdf': behavior_percentage_pdf, 'png': behavior_percentage_png}
    
    return result

def fetch_conflict_data(user_id):
    """
    从数据库中获取特定用户的所有冲突场景数据。
    """
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 查询与用户相关的所有ConflictScene数据
        conflicts = session.query(ConflictScene).join(AnalysisResult).join(AudioFile).filter(AudioFile.user_id == user_id).all()
        
        # 将数据转换为DataFrame
        data = [{
            'scene_id': conflict.scene_id,
            'trigger': conflict.trigger_event,
            'process': conflict.process,
            'conflict_type': conflict.conflict_type.value,
            'severity': conflict.severity.value,
            'dt': conflict.dt
        } for conflict in conflicts]
        
        df = pd.DataFrame(data)
        session.close()
        
        # 验证和清理数据
        if not df.empty:
            # 确保dt列存在并且有值
            if 'dt' in df.columns:
                # 将非数字日期转换为当前日期
                import datetime
                current_date = datetime.datetime.now().strftime('%Y%m%d')
                df['dt'] = df['dt'].fillna(current_date)
                # 检查dt是否符合格式要求
                non_standard_dates = ~df['dt'].astype(str).str.match(r'^\d{8}$')
                if any(non_standard_dates):
                    print(f"发现{sum(non_standard_dates)}个非标准日期格式，已替换为当前日期")
                    df.loc[non_standard_dates, 'dt'] = current_date
            else:
                df['dt'] = current_date
                
        return df
    except Exception as e:
        print(f"获取冲突数据失败: {str(e)}")
        if 'session' in locals():
            session.close()
        return pd.DataFrame()  # 返回空DataFrame而不是抛出异常

def fetch_behavior_data(user_id):
    """
    从数据库中获取特定用户的所有行为场景数据。
    """
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 查询与用户相关的所有BehaviorScene数据
        behaviors = session.query(BehaviorScene).join(AnalysisResult).join(AudioFile).filter(AudioFile.user_id == user_id).all()
        
        # 将数据转换为DataFrame
        data = [{
            'behaviour_id': behavior.behaviour_id,
            'description': behavior.description,
            'code': behavior.code.value,
            'type': behavior.type.value,
            'dt': behavior.dt
        } for behavior in behaviors]
        
        df = pd.DataFrame(data)
        session.close()
        
        # 验证和清理数据
        if not df.empty:
            # 确保dt列存在并且有值
            if 'dt' in df.columns:
                # 将非数字日期转换为当前日期
                import datetime
                current_date = datetime.datetime.now().strftime('%Y%m%d')
                df['dt'] = df['dt'].fillna(current_date)
                # 检查dt是否符合格式要求
                non_standard_dates = ~df['dt'].astype(str).str.match(r'^\d{8}$')
                if any(non_standard_dates):
                    print(f"发现{sum(non_standard_dates)}个非标准日期格式，已替换为当前日期")
                    df.loc[non_standard_dates, 'dt'] = current_date
            else:
                df['dt'] = current_date
                
        return df
    except Exception as e:
        print(f"获取行为数据失败: {str(e)}")
        if 'session' in locals():
            session.close()
        return pd.DataFrame()  # 返回空DataFrame而不是抛出异常 

def generate_analysis_figures(user_id):
    """
    生成特定用户的所有分析图表，包括冲突和行为分析。

    Args:
        user_id: 用户ID。

    Returns:
        dict: 返回生成的所有图片路径。
    """
    conflict_figures = generate_conflict_figures(user_id)
    behavior_figures = generate_behavior_figures(user_id)
    
    return {
        'conflict': conflict_figures,
        'behavior': behavior_figures
    } 