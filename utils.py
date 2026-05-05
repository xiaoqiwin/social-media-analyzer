# -*- coding: utf-8 -*-
"""
工具模块
功能：提供通用的工具函数，包含扩展停用词表
作者：Python项目架构导师
日期：2026-05-02
更新：添加扩展停用词表功能
"""

import os
import sys
import hashlib
import logging
import re
from datetime import datetime
from typing import List, Optional, Set, Dict, Any
import json


# 配置日志
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    配置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 如果已经配置过处理器，直接返回
    if logger.handlers:
        return logger

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # 创建文件处理器
    file_handler = logging.FileHandler('output/log.txt', encoding='utf-8')
    file_handler.setLevel(level)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger: 日志记录器
    """
    return setup_logger(name)


def ensure_output_dir(sub_dirs: List[str] = None) -> str:
    """
    确保输出目录存在

    Args:
        sub_dirs: 子目录列表

    Returns:
        str: 输出目录路径
    """
    output_dir = 'output'

    # 创建主输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 创建子目录
    if sub_dirs:
        for sub_dir in sub_dirs:
            dir_path = os.path.join(output_dir, sub_dir)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

    return output_dir


def get_md5(text: str) -> str:
    """
    计算字符串的MD5哈希值

    Args:
        text: 输入字符串

    Returns:
        str: MD5哈希值
    """
    if not text:
        return ''

    # 确保字符串是utf-8编码
    if isinstance(text, str):
        text = text.encode('utf-8')

    return hashlib.md5(text).hexdigest()


def clean_text(text: str) -> str:
    """
    清理文本，移除多余空格和特殊字符

    Args:
        text: 原始文本

    Returns:
        str: 清理后的文本
    """
    if not text:
        return ''

    # 如果text不是字符串，先转换为字符串
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return ''

    # 移除控制字符
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    # 移除多余的空白字符
    text = ' '.join(text.split())

    return text.strip()


def get_extended_stopwords() -> Set[str]:
    """
    获取扩展的中文停用词表

    Returns:
        Set[str]: 停用词集合
    """
    # 基础停用词
    stop_words = {
        # 1. 常见虚词
        '的', '了', '是', '在', '和', '就', '都', '而', '及', '与', '着', '或',
        '个', '人', '这', '那', '这个', '那个', '什么', '怎么', '为什么', '可以',
        '但', '很', '好', '要', '会', '能', '来', '去', '到', '说', '看',
        '知道', '觉得', '认为', '想', '看到', '听到', '觉得', '感到',
        '啊', '呀', '呢', '吧', '吗', '嗯', '哦', '哈', '哈哈', '呵呵',
        '自己', '这样', '那样', '那么', '这么', '这样', '那样',
        '不', '没', '没有', '不是', '不能', '不会', '不想', '不要',
        '对', '对于', '关于', '从', '向', '往', '朝', '到', '在',
        '上', '下', '左', '右', '前', '后', '里', '外', '中', '内',
        '被', '把', '给', '让', '叫', '使', '令', '将',
        '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
        '也', '又', '还', '再', '更', '最', '太', '很', '非常', '特别',
        '已经', '正在', '将要', '曾经', '经常', '总是', '有时', '偶尔',
        '因为', '所以', '如果', '虽然', '但是', '然而', '而且', '并且',
        '为了', '由于', '因此', '于是', '那么', '然后', '接着',
        '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '它们',
        '我的', '你的', '他的', '她的', '它的', '我们的', '你们的', '他们的',

        # 2. 网络用语
        '哈哈', '呵呵', '嘿嘿', '嘻嘻', '哈哈哈哈哈', '呵呵呵',
        '哦', '嗯', '额', '呃', '啊', '呀', '哇', '哟', '哎', '唉',
        '233', '666', '888', '520', '1314', 'xswl', 'yyds', 'awsl',
        '草', '卧槽', '我靠', '我去', '我擦', '尼玛', '妈呀',
        'emmmm', 'hhhh', 'hhhhh', '哈哈哈哈哈', '嘿嘿嘿',
        '捂脸', '笑哭', '笑死', '笑尿', '笑疯',
        '无语', '无奈', '摊手', '耸肩', '扶额',
        '狗头', 'doge', '滑稽', '吃瓜', '围观',
        '路过', '打卡', '签到', '冒泡', '潜水',
        '顶', '赞', '踩', '收藏', '转发', '评论',
        '前排', '沙发', '板凳', '地板', '地下室',

        # 3. 标点符号和数字
        ' ', '\t', '\n', '\r', '\u3000',  # 各种空白字符
        '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')',
        '-', '_', '=', '+', '[', ']', '{', '}', '\\', '|',
        ';', ':', "'", '"', ',', '<', '>', '.', '?', '/',
        '·', '！', '￥', '…', '（', '）', '—', '【', '】',
        '、', '；', '：', '「', '」', '『', '』', '《', '》',
        '，', '。', '？', '～', '`', '＠', '＃', '＄', '％', '＾', '＆', '＊',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        '０', '１', '２', '３', '４', '５', '６', '７', '８', '９',
        '零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
        '百', '千', '万', '亿',

        # 4. 社交媒体专用词
        '微博', '微信', 'QQ', '抖音', '快手', 'B站', '知乎', '豆瓣',
        '转发', '点赞', '评论', '收藏', '分享', '关注', '粉丝',
        '热搜', '话题', '超话', '热搜榜', '热门', '推荐',
        '直播', '主播', 'up主', '博主', '大V', '网红',
        '弹幕', '评论', '留言', '私信', '站内信',
        '置顶', '精华', '热门', '推荐', '精选',
        '客户端', 'APP', '小程序', '公众号',
        '官微', '官方', '客服', '小编', '管理员',

        # 5. 时间相关
        '今天', '明天', '昨天', '前天', '后天',
        '早上', '上午', '中午', '下午', '晚上', '凌晨',
        '今年', '去年', '明年', '前年', '后年',
        '月份', '一月', '二月', '三月', '四月', '五月', '六月',
        '七月', '八月', '九月', '十月', '十一月', '十二月',
        '周一', '周二', '周三', '周四', '周五', '周六', '周日',
        '星期', '礼拜', '小时', '分钟', '秒钟', '世纪', '年代',
        '现在', '过去', '未来', '之前', '之后', '以后', '以前',

        # 6. 人称代词
        '俺', '咱', '朕', '臣', '妾', '奴', '婢', '奴才',
        '人家', '别人', '他人', '旁人', '对方',
        '各位', '诸位', '大家', '全体', '群众', '观众', '读者',
        '本人', '自身', '本人', '本尊', '本座',
        '您', '您们', '您老', '您老人家',
        '谁', '何', '啥', '哪个', '哪些',
        '每', '各', '每', '各', '某些', '有些', '任何',
    }

    return stop_words


def get_domain_specific_stopwords(domain: str = "weibo") -> Set[str]:
    """
    获取特定领域的停用词

    Args:
        domain: 领域类型，可选: "weibo", "news", "shopping", "movie"

    Returns:
        Set[str]: 领域特定停用词
    """
    common_stopwords = get_extended_stopwords()

    domain_stopwords = {
        "weibo": {
            # 微博特有
            "转发微博", "转发", "微博", "新浪微博", "腾讯微博",
            "热搜", "热门", "话题", "超话", "话题榜",
            "评论", "点赞", "收藏", "分享", "关注",
            "博主", "大V", "网红", "up主", "主播",
            "客户端", "APP", "小程序", "公众号",
            "小编", "小编说", "小编有话说", "小编推荐",
            "官微", "官方", "客服", "管理员",
            "置顶", "精华", "热门", "推荐", "精选",
        },
        "news": {
            # 新闻媒体特有
            "本报讯", "记者", "报道", "通讯员", "摄影",
            "编辑", "责编", "审核", "校对", "签发",
            "电", "讯", "据", "报道", "获悉",
            "日前", "近日", "昨天", "今天", "明天",
            "据悉", "据了解", "据报道", "据介绍",
            "表示", "指出", "强调", "要求", "希望",
            "认为", "觉得", "相信", "预计", "估计",
        },
        "shopping": {
            # 电商评论特有
            "宝贝", "商品", "产品", "物品", "货物",
            "卖家", "买家", "客服", "掌柜", "店家",
            "快递", "物流", "包装", "发货", "收货",
            "质量", "价格", "性价比", "优惠", "折扣",
            "好评", "中评", "差评", "追评", "晒图",
            "推荐", "不推荐", "建议", "不建议", "值得",
            "五星", "四星", "三星", "二星", "一星",
        },
        "movie": {
            # 电影评论特有
            "电影", "影片", "片子", "剧情", "导演",
            "演员", "主演", "配角", "演技", "表演",
            "特效", "画面", "音乐", "配乐", "音效",
            "情节", "故事", "结局", "开头", "高潮",
            "推荐", "不推荐", "值得", "不值得", "建议",
            "星", "颗星", "分", "评分", "打分",
        }
    }

    # 合并通用停用词和领域特定停用词
    result = common_stopwords.copy()
    if domain in domain_stopwords:
        result.update(domain_stopwords[domain])

    return result


def clean_text_with_stopwords(text: str, domain: str = "weibo") -> str:
    """
    使用停用词表清洗文本

    Args:
        text: 原始文本
        domain: 领域类型

    Returns:
        str: 清洗后的文本
    """
    if not text:
        return ""

    # 获取停用词
    stopwords = get_domain_specific_stopwords(domain)

    # 尝试使用jieba分词
    try:
        import jieba
        words = jieba.lcut(text)
    except ImportError:
        # 如果jieba不可用，使用简单分词
        words = list(text)

    # 过滤停用词
    filtered_words = []
    for word in words:
        word = word.strip()
        if word and word not in stopwords and not word.isspace():
            # 检查长度
            if len(word) > 1 or (len(word) == 1 and word.isalpha()):
                filtered_words.append(word)

    # 重新组合
    return ' '.join(filtered_words)


def format_time(seconds: float) -> str:
    """
    格式化时间显示

    Args:
        seconds: 秒数

    Returns:
        str: 格式化后的时间字符串
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"


def print_progress_bar(iteration: int, total: int, prefix: str = '', suffix: str = '',
                       length: int = 50, fill: str = '█'):
    """
    打印进度条

    Args:
        iteration: 当前迭代
        total: 总迭代次数
        prefix: 前缀
        suffix: 后缀
        length: 进度条长度
        fill: 填充字符
    """
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)

    # 使用\r实现进度条原地更新
    if iteration < total:
        end_char = '\r'
    else:
        end_char = '\n'

    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=end_char)

    # 如果完成，打印新行
    if iteration == total:
        print()


def load_json_file(filepath: str) -> Optional[Dict]:
    """
    加载JSON文件

    Args:
        filepath: 文件路径

    Returns:
        Optional[Dict]: 解析后的数据
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return None


def save_json_file(filepath: str, data: Dict) -> bool:
    """
    保存JSON文件

    Args:
        filepath: 文件路径
        data: 要保存的数据

    Returns:
        bool: 是否成功
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存JSON文件失败: {e}")
        return False


if __name__ == "__main__":
    """测试工具函数"""
    print("🧪 测试工具函数...")

    # 测试MD5
    test_text = "测试文本"
    md5_hash = get_md5(test_text)
    print(f"MD5哈希测试: '{test_text}' -> {md5_hash}")

    # 测试文本清理
    dirty_text = "  这是  测试 文本\n\t包含多余空格  "
    cleaned = clean_text(dirty_text)
    print(f"文本清理测试: '{dirty_text}' -> '{cleaned}'")

    # 测试停用词
    stopwords = get_extended_stopwords()
    print(f"停用词表大小: {len(stopwords)} 个词")

    # 测试领域特定停用词
    weibo_stopwords = get_domain_specific_stopwords("weibo")
    print(f"微博停用词表大小: {len(weibo_stopwords)} 个词")

    # 测试停用词清理
    test_comment = "今天微博热搜上这个话题太火了！哈哈哈哈，大家都在讨论#这个话题#"
    cleaned_comment = clean_text_with_stopwords(test_comment, "weibo")
    print(f"停用词清理测试: '{test_comment}' -> '{cleaned_comment}'")