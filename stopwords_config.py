# -*- coding: utf-8 -*-
"""
停用词配置文件
功能：配置和管理停用词
作者：Python文本处理导师
日期：2026-05-02
"""

import os
from typing import Set, List, Dict
from datetime import datetime

# 停用词配置文件
STOPWORDS_CONFIG = {
    # 是否启用停用词过滤
    "enabled": True,

    # 默认领域
    "default_domains": ["common", "weibo"],

    # 自定义停用词文件路径
    "custom_stopwords_file": "custom_stopwords.txt",

    # 停用词过滤级别
    "filter_level": "medium",  # low, medium, high

    # 是否过滤单字
    "filter_single_char": True,

    # 是否过滤数字
    "filter_digits": True,

    # 是否过滤特殊字符
    "filter_special_chars": True,

    # 是否过滤英文单词
    "filter_english": False,

    # 最小词长
    "min_word_length": 2,

    # 最大词长
    "max_word_length": 10,
}


def get_filter_config(level: str = None) -> Dict:
    """
    获取过滤配置

    Args:
        level: 过滤级别

    Returns:
        Dict: 过滤配置
    """
    config = STOPWORDS_CONFIG.copy()

    if level:
        config["filter_level"] = level

    # 根据过滤级别调整配置
    if config["filter_level"] == "low":
        config.update({
            "filter_single_char": False,
            "filter_digits": False,
            "filter_special_chars": False,
            "min_word_length": 1,
        })
    elif config["filter_level"] == "high":
        config.update({
            "filter_single_char": True,
            "filter_digits": True,
            "filter_special_chars": True,
            "filter_english": True,
            "min_word_length": 2,
            "max_word_length": 8,
        })
    else:  # medium
        config.update({
            "filter_single_char": True,
            "filter_digits": True,
            "filter_special_chars": True,
            "filter_english": False,
            "min_word_length": 2,
            "max_word_length": 10,
        })

    return config


def load_custom_stopwords(filepath: str = None) -> Set[str]:
    """
    加载自定义停用词

    Args:
        filepath: 文件路径

    Returns:
        Set[str]: 自定义停用词集合
    """
    if filepath is None:
        filepath = STOPWORDS_CONFIG["custom_stopwords_file"]

    custom_words = set()

    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        custom_words.add(line)
            print(f"✅ 已加载 {len(custom_words)} 个自定义停用词")
    except Exception as e:
        print(f"❌ 加载自定义停用词失败: {e}")

    return custom_words


def save_custom_stopwords(words: List[str], filepath: str = None):
    """
    保存自定义停用词

    Args:
        words: 停用词列表
        filepath: 文件路径
    """
    if filepath is None:
        filepath = STOPWORDS_CONFIG["custom_stopwords_file"]

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# 自定义停用词表\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# 每行一个停用词\n\n")
            for word in sorted(words):
                f.write(f"{word}\n")
        print(f"✅ 已保存 {len(words)} 个自定义停用词到 {filepath}")
    except Exception as e:
        print(f"❌ 保存自定义停用词失败: {e}")


def get_config_info() -> Dict:
    """
    获取配置信息

    Returns:
        Dict: 配置信息
    """
    config = STOPWORDS_CONFIG.copy()

    # 添加自定义停用词数量
    custom_words = load_custom_stopwords()
    config["custom_stopwords_count"] = len(custom_words)

    return config


def print_config_info():
    """打印配置信息"""
    config = get_config_info()

    print("📋 停用词配置信息")
    print("=" * 50)
    print(f"启用状态: {'✅' if config['enabled'] else '❌'}")
    print(f"默认领域: {', '.join(config['default_domains'])}")
    print(f"过滤级别: {config['filter_level']}")
    print(f"过滤单字: {'✅' if config['filter_single_char'] else '❌'}")
    print(f"过滤数字: {'✅' if config['filter_digits'] else '❌'}")
    print(f"过滤特殊字符: {'✅' if config['filter_special_chars'] else '❌'}")
    print(f"过滤英文: {'✅' if config['filter_english'] else '❌'}")
    print(f"最小词长: {config['min_word_length']}")
    print(f"最大词长: {config['max_word_length']}")
    print(f"自定义停用词文件: {config['custom_stopwords_file']}")
    print(f"自定义停用词数量: {config['custom_stopwords_count']}")
    print("=" * 50)


def update_config(**kwargs):
    """
    更新配置

    Args:
        **kwargs: 配置键值对
    """
    global STOPWORDS_CONFIG

    for key, value in kwargs.items():
        if key in STOPWORDS_CONFIG:
            STOPWORDS_CONFIG[key] = value
        else:
            print(f"⚠️ 未知配置项: {key}")


if __name__ == "__main__":
    """测试停用词配置"""
    print("🧪 测试停用词配置...")

    # 打印配置信息
    print_config_info()

    # 测试自定义停用词
    test_words = ["测试词1", "测试词2", "测试词3"]
    save_custom_stopwords(test_words, "test_stopwords.txt")

    # 加载自定义停用词
    loaded_words = load_custom_stopwords("test_stopwords.txt")
    print(f"加载的自定义停用词: {loaded_words}")

    # 清理测试文件
    if os.path.exists("test_stopwords.txt"):
        os.remove("test_stopwords.txt")
        print("✅ 已清理测试文件")