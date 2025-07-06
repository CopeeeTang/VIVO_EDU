# -*- coding: utf-8 -*-
"""
数据库迁移脚本
应用新的算法模型变更
"""

import logging
from sqlalchemy import text
from ..extensions import db

logger = logging.getLogger(__name__)


def migrate_database():
    """执行数据库迁移"""
    logger.info("开始数据库迁移...")
    
    try:
        # 创建新的表
        create_enhanced_tables()
        
        # 执行数据迁移
        migrate_existing_data()
        
        logger.info("数据库迁移完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        db.session.rollback()
        return False


def create_enhanced_tables():
    """创建增强的表结构"""
    logger.info("创建新的表结构...")
    
    # 创建亲子画像表
    parent_child_profile_sql = """
    CREATE TABLE IF NOT EXISTS parent_child_profiles (
        profile_id INT AUTO_INCREMENT PRIMARY KEY,
        analysis_id INT NOT NULL,
        parenting_style TEXT,
        sentiment_analysis TEXT,
        communication_patterns TEXT,
        topic_analysis TEXT,
        conflict_analysis TEXT,
        advantage_analysis TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (analysis_id) REFERENCES analysis_results(analysis_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 创建场景重建表
    scenery_rebuild_sql = """
    CREATE TABLE IF NOT EXISTS scenery_rebuilds (
        scenery_id INT AUTO_INCREMENT PRIMARY KEY,
        analysis_id INT NOT NULL,
        scene_count INT NOT NULL DEFAULT 0,
        scene_summaries TEXT,
        processing_status VARCHAR(50) DEFAULT 'completed',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (analysis_id) REFERENCES analysis_results(analysis_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 创建场景详情表
    scene_details_sql = """
    CREATE TABLE IF NOT EXISTS scene_details (
        detail_id INT AUTO_INCREMENT PRIMARY KEY,
        scenery_id INT NOT NULL,
        scene_id INT NOT NULL,
        event_description TEXT,
        change_process TEXT,
        key_details TEXT,
        time_range VARCHAR(100),
        participants TEXT,
        emotional_tone VARCHAR(50),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (scenery_id) REFERENCES scenery_rebuilds(scenery_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 创建知识库检索结果表
    knowledge_base_results_sql = """
    CREATE TABLE IF NOT EXISTS knowledge_base_results (
        kb_result_id INT AUTO_INCREMENT PRIMARY KEY,
        analysis_id INT NOT NULL,
        query_text TEXT,
        search_type VARCHAR(50),
        total_results INT DEFAULT 0,
        search_results TEXT,
        educational_advice TEXT,
        advice_status VARCHAR(50) DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (analysis_id) REFERENCES analysis_results(analysis_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 创建干预策略表
    intervention_strategies_sql = """
    CREATE TABLE IF NOT EXISTS intervention_strategies (
        strategy_id INT AUTO_INCREMENT PRIMARY KEY,
        analysis_id INT NOT NULL,
        strategy_content TEXT,
        strategy_type VARCHAR(100),
        priority VARCHAR(20),
        applicable_scenarios TEXT,
        expected_outcomes TEXT,
        implementation_suggestions TEXT,
        precautions TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (analysis_id) REFERENCES analysis_results(analysis_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 创建分析任务表
    analysis_tasks_sql = """
    CREATE TABLE IF NOT EXISTS analysis_tasks (
        task_id VARCHAR(50) PRIMARY KEY,
        file_id VARCHAR(36) NOT NULL,
        user_id INT NOT NULL,
        status VARCHAR(50) DEFAULT 'pending',
        current_step VARCHAR(100),
        total_steps INT DEFAULT 6,
        completed_steps INT DEFAULT 0,
        progress_percentage INT DEFAULT 0,
        error_message TEXT,
        started_at DATETIME,
        completed_at DATETIME,
        processing_duration FLOAT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (file_id) REFERENCES audio_files(file_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 创建系统配置表
    system_configs_sql = """
    CREATE TABLE IF NOT EXISTS system_configs (
        config_id INT AUTO_INCREMENT PRIMARY KEY,
        config_key VARCHAR(100) UNIQUE NOT NULL,
        config_value TEXT,
        config_type VARCHAR(20) NOT NULL DEFAULT 'string',
        description VARCHAR(255),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 执行SQL语句
    sql_statements = [
        parent_child_profile_sql,
        scenery_rebuild_sql,
        scene_details_sql,
        knowledge_base_results_sql,
        intervention_strategies_sql,
        analysis_tasks_sql,
        system_configs_sql
    ]
    
    for sql in sql_statements:
        try:
            db.session.execute(text(sql))
            db.session.commit()
            logger.info(f"成功创建表")
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            db.session.rollback()
            raise


def migrate_existing_data():
    """迁移现有数据"""
    logger.info("开始迁移现有数据...")
    
    try:
        # 为现有的分析结果创建空的关联记录
        migrate_analysis_results()
        
        # 插入默认系统配置
        insert_default_configs()
        
        logger.info("数据迁移完成")
        
    except Exception as e:
        logger.error(f"数据迁移失败: {e}")
        raise


def migrate_analysis_results():
    """为现有分析结果创建关联记录"""
    logger.info("为现有分析结果创建关联记录...")
    
    # 获取所有现有的分析结果
    existing_results = db.session.execute(
        text("SELECT analysis_id FROM analysis_results")
    ).fetchall()
    
    for result in existing_results:
        analysis_id = result[0]
        
        # 为每个分析结果创建空的关联记录
        try:
            # 检查是否已存在记录，避免重复插入
            existing_profile = db.session.execute(
                text("SELECT profile_id FROM parent_child_profiles WHERE analysis_id = :analysis_id"),
                {"analysis_id": analysis_id}
            ).fetchone()
            
            if not existing_profile:
                # 创建亲子画像记录
                db.session.execute(
                    text("""
                        INSERT INTO parent_child_profiles (analysis_id, created_at, updated_at) 
                        VALUES (:analysis_id, NOW(), NOW())
                    """),
                    {"analysis_id": analysis_id}
                )
                
                # 创建场景重建记录
                db.session.execute(
                    text("""
                        INSERT INTO scenery_rebuilds (analysis_id, scene_count, created_at, updated_at) 
                        VALUES (:analysis_id, 0, NOW(), NOW())
                    """),
                    {"analysis_id": analysis_id}
                )
                
                # 创建知识库检索记录
                db.session.execute(
                    text("""
                        INSERT INTO knowledge_base_results (analysis_id, total_results, created_at, updated_at) 
                        VALUES (:analysis_id, 0, NOW(), NOW())
                    """),
                    {"analysis_id": analysis_id}
                )
                
                # 创建干预策略记录
                db.session.execute(
                    text("""
                        INSERT INTO intervention_strategies (analysis_id, created_at, updated_at) 
                        VALUES (:analysis_id, NOW(), NOW())
                    """),
                    {"analysis_id": analysis_id}
                )
                
                logger.info(f"为分析结果 {analysis_id} 创建关联记录")
        
        except Exception as e:
            logger.warning(f"为分析结果 {analysis_id} 创建关联记录失败: {e}")
            continue
    
    db.session.commit()


def insert_default_configs():
    """插入默认系统配置"""
    logger.info("插入默认系统配置...")
    
    default_configs = [
        {
            'config_key': 'api_retry_count',
            'config_value': '3',
            'config_type': 'int',
            'description': 'API调用重试次数'
        },
        {
            'config_key': 'api_timeout',
            'config_value': '60',
            'config_type': 'int',
            'description': 'API调用超时时间（秒）'
        },
        {
            'config_key': 'max_file_size_mb',
            'config_value': '100',
            'config_type': 'int',
            'description': '最大文件大小（MB）'
        },
        {
            'config_key': 'supported_audio_formats',
            'config_value': '["wav", "mp3", "m4a", "aac", "ogg", "pcm"]',
            'config_type': 'json',
            'description': '支持的音频格式'
        },
        {
            'config_key': 'enable_async_processing',
            'config_value': 'true',
            'config_type': 'bool',
            'description': '启用异步处理'
        },
        {
            'config_key': 'knowledge_base_enabled',
            'config_value': 'true',
            'config_type': 'bool',
            'description': '启用知识库检索'
        }
    ]
    
    for config in default_configs:
        try:
            # 检查配置是否已存在
            existing = db.session.execute(
                text("SELECT config_id FROM system_configs WHERE config_key = :key"),
                {"key": config['config_key']}
            ).fetchone()
            
            if not existing:
                db.session.execute(
                    text("""
                        INSERT INTO system_configs (config_key, config_value, config_type, description) 
                        VALUES (:key, :value, :type, :desc)
                    """),
                    {
                        "key": config['config_key'],
                        "value": config['config_value'],
                        "type": config['config_type'],
                        "desc": config['description']
                    }
                )
                logger.info(f"插入配置: {config['config_key']}")
        
        except Exception as e:
            logger.warning(f"插入配置 {config['config_key']} 失败: {e}")
            continue
    
    db.session.commit()


def rollback_migration():
    """回滚迁移（删除新创建的表）"""
    logger.warning("开始回滚数据库迁移...")
    
    tables_to_drop = [
        'scene_details',
        'scenery_rebuilds',
        'parent_child_profiles',
        'knowledge_base_results',
        'intervention_strategies',
        'analysis_tasks',
        'system_configs'
    ]
    
    for table in tables_to_drop:
        try:
            db.session.execute(text(f"DROP TABLE IF EXISTS {table}"))
            logger.info(f"删除表: {table}")
        except Exception as e:
            logger.error(f"删除表 {table} 失败: {e}")
    
    db.session.commit()
    logger.warning("数据库迁移回滚完成")


def check_migration_status():
    """检查迁移状态"""
    try:
        # 检查是否存在新表
        result = db.session.execute(
            text("SHOW TABLES LIKE 'parent_child_profiles'")
        ).fetchone()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"检查迁移状态失败: {e}")
        return False


if __name__ == "__main__":
    # 直接运行迁移
    success = migrate_database()
    if success:
        print("数据库迁移成功完成")
    else:
        print("数据库迁移失败") 