# -*- coding: utf-8 -*-
"""
数据库初始化模块
功能：创建数据库和表结构
作者：Python项目架构导师
日期：2026-05-02
修复版：修复数据库连接权限问题
"""

import pymysql
import logging
from config import get_db_connection, test_connection
import utils

# 获取日志记录器
logger = utils.get_logger(__name__)


def create_database_if_not_exists() -> bool:
    """
    创建数据库（如果不存在）

    Returns:
        bool: 是否成功
    """
    try:
        # 从config.py读取数据库配置
        from config import DB_CONFIG

        # 连接到MySQL服务器（不指定数据库）
        conn = pymysql.connect(
            host=DB_CONFIG.get('host', 'localhost'),
            port=DB_CONFIG.get('port', 3306),
            user=DB_CONFIG.get('user', 'root'),
            password=DB_CONFIG.get('password', ''),
            charset=DB_CONFIG.get('charset', 'utf8mb4')
        )

        cursor = conn.cursor()

        # 创建数据库SQL语句
        sql = """
        CREATE DATABASE IF NOT EXISTS social_media_hotspot 
        CHARACTER SET utf8mb4 
        COLLATE utf8mb4_unicode_ci
        """

        cursor.execute(sql)
        conn.commit()

        logger.info("数据库 'social_media_hotspot' 创建/验证成功")

        cursor.close()
        conn.close()

        return True

    except pymysql.err.OperationalError as e:
        if e.args[0] == 1045:  # 访问被拒绝
            logger.error(f"数据库连接失败: 用户名或密码错误")
            print("❌ 数据库连接失败: 用户名或密码错误")
            print(f"请检查config.py中的配置:")
            print(f"  host: {DB_CONFIG.get('host', 'localhost')}")
            print(f"  port: {DB_CONFIG.get('port', 3306)}")
            print(f"  user: {DB_CONFIG.get('user', 'root')}")
            print(f"  password: {'*' * len(DB_CONFIG.get('password', '')) if DB_CONFIG.get('password') else '(空)'}")
        else:
            logger.error(f"数据库连接失败: {e}")
        return False
    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        return False


def create_tables(conn) -> bool:
    """
    创建数据表

    Args:
        conn: 数据库连接对象

    Returns:
        bool: 是否成功
    """
    cursor = None

    try:
        cursor = conn.cursor()

        # 1. 热点事件表
        hot_events_sql = """
        CREATE TABLE IF NOT EXISTS `hot_events` (
          `id` INT NOT NULL AUTO_INCREMENT COMMENT '自增主键',
          `event_hash` VARCHAR(32) NOT NULL COMMENT '事件去重哈希(MD5)',
          `title` VARCHAR(500) NOT NULL COMMENT '事件标题',
          `hot_value` INT NOT NULL DEFAULT 0 COMMENT '热度值',
          `source` VARCHAR(50) NOT NULL DEFAULT '微博' COMMENT '来源平台',
          `crawl_date` DATE NOT NULL COMMENT '爬取日期',
          `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `uk_event_hash` (`event_hash`),
          KEY `idx_crawl_date` (`crawl_date`),
          KEY `idx_source` (`source`),
          KEY `idx_date_source` (`crawl_date`, `source`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='热点事件表';
        """

        cursor.execute(hot_events_sql)
        logger.info("表 'hot_events' 创建/验证成功")

        # 2. 评论表
        comments_sql = """
        CREATE TABLE IF NOT EXISTS `comments` (
          `id` INT NOT NULL AUTO_INCREMENT COMMENT '自增主键',
          `event_id` INT NOT NULL COMMENT '关联事件ID',
          `content` TEXT NOT NULL COMMENT '评论内容',
          `like_count` INT NOT NULL DEFAULT 0 COMMENT '点赞数',
          `content_hash` VARCHAR(32) NOT NULL COMMENT '评论内容哈希(MD5)',
          `sentiment_label` VARCHAR(20) DEFAULT NULL COMMENT '情感标签',
          `sentiment_confidence` FLOAT DEFAULT NULL COMMENT '情感置信度',
          `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `uk_event_comment` (`event_id`, `content_hash`),
          KEY `idx_event_id` (`event_id`),
          KEY `idx_sentiment_label` (`sentiment_label`),
          KEY `idx_created_at` (`created_at`),
          CONSTRAINT `fk_comments_event` 
            FOREIGN KEY (`event_id`) 
            REFERENCES `hot_events` (`id`) 
            ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';
        """

        cursor.execute(comments_sql)
        logger.info("表 'comments' 创建/验证成功")

        # 3. 情感统计表
        sentiment_results_sql = """
        CREATE TABLE IF NOT EXISTS `sentiment_results` (
          `id` INT NOT NULL AUTO_INCREMENT COMMENT '自增主键',
          `event_id` INT NOT NULL COMMENT '关联事件ID',
          `positive_count` INT NOT NULL DEFAULT 0 COMMENT '正面评论数',
          `negative_count` INT NOT NULL DEFAULT 0 COMMENT '负面评论数',
          `neutral_count` INT NOT NULL DEFAULT 0 COMMENT '中性评论数',
          `total_count` INT NOT NULL DEFAULT 0 COMMENT '评论总数',
          `analyzed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '分析时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `uk_event_date` (`event_id`, `analyzed_at`),
          KEY `idx_event_id` (`event_id`),
          KEY `idx_analyzed_at` (`analyzed_at`),
          CONSTRAINT `fk_sentiment_event` 
            FOREIGN KEY (`event_id`) 
            REFERENCES `hot_events` (`id`) 
            ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='情感统计表';
        """

        cursor.execute(sentiment_results_sql)
        logger.info("表 'sentiment_results' 创建/验证成功")

        return True

    except Exception as e:
        logger.error(f"创建表失败: {e}")
        return False
    finally:
        if cursor:
            cursor.close()


def verify_tables(conn) -> bool:
    """
    验证表是否创建成功

    Args:
        conn: 数据库连接对象

    Returns:
        bool: 是否验证成功
    """
    cursor = None

    try:
        cursor = conn.cursor()

        # 执行SHOW TABLES查询
        cursor.execute("SHOW TABLES")
        tables_result = cursor.fetchall()

        # 提取表名
        table_names = []
        for row in tables_result:
            if isinstance(row, dict):
                # 字典格式
                table_name = list(row.values())[0]
            elif isinstance(row, tuple):
                # 元组格式
                table_name = row[0]
            else:
                # 其他格式
                table_name = str(row)
            table_names.append(table_name)

        required_tables = {'hot_events', 'comments', 'sentiment_results'}
        existing_tables = set(table_names)

        # 检查缺失的表
        missing_tables = required_tables - existing_tables

        if missing_tables:
            logger.error(f"缺少以下表: {', '.join(missing_tables)}")
            return False

        logger.info(f"所有表已存在: {', '.join(table_names)}")
        return True

    except Exception as e:
        logger.error(f"验证表失败: {e}")
        return False
    finally:
        if cursor:
            cursor.close()


def show_table_structure(conn) -> None:
    """
    显示表结构

    Args:
        conn: 数据库连接对象
    """
    cursor = None

    try:
        cursor = conn.cursor()

        tables = ['hot_events', 'comments', 'sentiment_results']

        for table_name in tables:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()

            print(f"\n表 '{table_name}' 结构:")
            print("-" * 60)
            print(f"{'字段名':<20} {'类型':<20} {'是否为空':<10} {'键':<10} {'默认值':<20} {'额外信息'}")
            print("-" * 60)

            for column in columns:
                if isinstance(column, dict):
                    field = column.get('Field', '')
                    field_type = column.get('Type', '')
                    null = column.get('Null', '')
                    key = column.get('Key', '')
                    default = column.get('Default', '')
                    extra = column.get('Extra', '')
                elif isinstance(column, tuple):
                    field = column[0]
                    field_type = column[1]
                    null = column[2]
                    key = column[3]
                    default = column[4] if len(column) > 4 else ''
                    extra = column[5] if len(column) > 5 else ''
                else:
                    continue

                print(f"{field:<20} {field_type:<20} {null:<10} {key:<10} {str(default):<20} {extra}")

    except Exception as e:
        logger.error(f"获取表结构失败: {e}")
    finally:
        if cursor:
            cursor.close()


def manual_database_creation_guide():
    """
    手动创建数据库的指导
    """
    print("\n" + "=" * 60)
    print("📋 手动创建数据库指南")
    print("=" * 60)

    from config import DB_CONFIG

    print("如果自动创建数据库失败，请按以下步骤操作：")
    print()
    print("1. 打开MySQL命令行客户端或MySQL Workbench")
    print("2. 使用root用户登录MySQL:")
    print(f"   mysql -u root -p")
    print("3. 输入root用户的密码")
    print("4. 执行以下SQL语句创建数据库:")
    print(f"   CREATE DATABASE IF NOT EXISTS social_media_hotspot")
    print(f"   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print("5. 授予权限（可选，如果使用非root用户）:")
    print(f"   GRANT ALL PRIVILEGES ON social_media_hotspot.*")
    print(f"   TO '{DB_CONFIG.get('user', 'root')}'@'localhost';")
    print("6. 刷新权限:")
    print(f"   FLUSH PRIVILEGES;")
    print("7. 退出MySQL:")
    print(f"   exit;")
    print("=" * 60)
    print("完成以上步骤后，重新运行数据库初始化。")
    print("=" * 60)


def run_db_init() -> bool:
    """
    运行数据库初始化

    这个函数将被main.py调用

    Returns:
        bool: 是否成功
    """
    print("🔧 开始数据库初始化...")
    print("=" * 60)

    conn = None

    try:
        # 1. 创建数据库（如果不存在）
        print("步骤1: 创建数据库...")
        if not create_database_if_not_exists():
            print("❌ 创建数据库失败")
            manual_database_creation_guide()
            return False

        # 2. 获取数据库连接
        print("步骤2: 连接到数据库...")
        try:
            conn = get_db_connection()
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            print("\n可能的原因:")
            print("1. 数据库用户没有权限访问social_media_hotspot数据库")
            print("2. 数据库用户不存在")
            print("3. 网络连接问题")

            manual_database_creation_guide()
            return False

        # 3. 创建表
        print("步骤3: 创建数据表...")
        if not create_tables(conn):
            print("❌ 创建表失败")
            return False

        # 4. 验证表
        print("步骤4: 验证表结构...")
        if not verify_tables(conn):
            print("❌ 验证表失败")
            return False

        # 5. 显示表结构
        print("步骤5: 显示表结构...")
        show_table_structure(conn)

        # 提交事务
        conn.commit()

        print("\n" + "=" * 60)
        print("✅ 数据库初始化完成！")
        print("数据库名: social_media_hotspot")
        print("字符集: utf8mb4 (支持emoji)")
        print("包含表: hot_events, comments, sentiment_results")
        print("=" * 60)

        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        if conn:
            conn.close()
            logger.debug("数据库连接已关闭")


if __name__ == "__main__":
    """
    直接运行此模块时，初始化数据库
    """
    success = run_db_init()
    if success:
        print("✅ 数据库初始化完成！")
    else:
        print("❌ 数据库初始化失败！")