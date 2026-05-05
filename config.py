# -*- coding: utf-8 -*-
"""
数据库配置文件
功能：管理数据库连接配置和连接对象
作者：Python项目架构导师
日期：2026-05-02
"""

import pymysql
from typing import Dict, Any, Optional

# 数据库配置字典
DB_CONFIG: Dict[str, Any] = {
    'host': 'localhost',  # MySQL服务器地址
    'port': 3306,  # MySQL端口，默认3306
    'user': 'root',  # 数据库用户名
    'password': '123456',  # 数据库密码（请修改为你的实际密码）
    'database': 'social_media_hotspot',  # 数据库名
    'charset': 'utf8mb4',  # 字符编码，支持emoji
    'cursorclass': pymysql.cursors.DictCursor  # 返回字典格式的结果
}


class DatabaseConfig:
    """
    数据库配置类
    使用类封装配置，便于扩展和管理
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据库配置

        Args:
            config: 数据库配置字典，如果为None则使用默认配置
        """
        self.config = config or DB_CONFIG.copy()

    def get_config(self) -> Dict[str, Any]:
        """
        获取数据库配置

        Returns:
            Dict[str, Any]: 数据库配置字典
        """
        return self.config

    def update_config(self, key: str, value: Any) -> None:
        """
        更新配置项

        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value

    def validate_config(self) -> bool:
        """
        验证配置是否完整

        Returns:
            bool: 配置是否有效
        """
        required_keys = ['host', 'port', 'user', 'password', 'database', 'charset']
        for key in required_keys:
            if key not in self.config or self.config[key] is None:
                return False
        return True


def get_db_connection(config: Optional[Dict[str, Any]] = None) -> pymysql.connections.Connection:
    """
    获取数据库连接对象

    Args:
        config: 数据库配置字典，如果为None则使用默认配置

    Returns:
        pymysql.connections.Connection: 数据库连接对象

    Raises:
        pymysql.Error: 数据库连接失败时抛出
    """
    # 使用传入的配置或默认配置
    db_config = config or DB_CONFIG

    try:
        # 创建数据库连接
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            charset=db_config['charset'],
            cursorclass=db_config.get('cursorclass', pymysql.cursors.DictCursor)
        )
        return connection
    except pymysql.Error as e:
        raise Exception(f"数据库连接失败: {e}")


def test_connection() -> bool:
    """
    测试数据库连接

    Returns:
        bool: 连接是否成功
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False


if __name__ == "__main__":
    """
    直接运行此文件时，测试数据库连接
    """
    print("测试数据库连接...")
    if test_connection():
        print("✅ 数据库连接成功！")
    else:
        print("❌ 数据库连接失败，请检查config.py中的配置")
        print("\n当前配置:")
        for key, value in DB_CONFIG.items():
            if key != 'password':
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {'*' * len(value) if value else '(空)'}")
        print("\n请确保:")
        print("1. MySQL服务正在运行")
        print("2. 数据库'social_media_hotspot'已存在")
        print("3. 用户名和密码正确")
        print("4. 用户有访问数据库的权限")