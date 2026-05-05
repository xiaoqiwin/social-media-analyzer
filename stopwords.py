# -*- coding: utf-8 -*-
"""
中文停用词表管理器
功能：提供多领域的中文停用词表
作者：Python文本处理导师
日期：2026-05-02
"""

import os
from typing import Set, List, Dict, Optional
from datetime import datetime


class StopWordsManager:
    """停用词管理器"""

    def __init__(self):
        """初始化停用词管理器"""
        self._stopwords = self._load_all_stopwords()

    def _load_all_stopwords(self) -> Dict[str, Set[str]]:
        """加载所有停用词"""
        return {
            "common": self._get_common_stopwords(),
            "weibo": self._get_weibo_stopwords(),
            "news": self._get_news_stopwords(),
            "shopping": self._get_shopping_stopwords(),
            "movie": self._get_movie_stopwords(),
            "academic": self._get_academic_stopwords(),
            "legal": self._get_legal_stopwords(),
            "medical": self._get_medical_stopwords(),
        }

    def _get_common_stopwords(self) -> Set[str]:
        """获取通用停用词"""
        return {
            # 常用虚词
            '的', '了', '是', '在', '和', '就', '都', '而', '及', '与',
            '着', '或', '个', '人', '这', '那', '这个', '那个',

            # 人称代词
            '我', '你', '他', '她', '它', '我们', '你们', '他们',
            '我的', '你的', '他的', '她的', '它的', '我们的',

            # 助词
            '啊', '呀', '呢', '吧', '吗', '嗯', '哦', '哈',

            # 标点符号
            ' ', '\t', '\n', '\r', ',', '.', '?', '!', ';', ':',
            '，', '。', '？', '！', '；', '：',

            # 数字
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',

            # 连接词
            '和', '与', '同', '跟', '及', '以及', '连同',

            # 副词
            '很', '非常', '极其', '十分', '特别', '格外',

            # 介词
            '在', '于', '从', '自', '自从', '由',
        }

    def _get_weibo_stopwords(self) -> Set[str]:
        """获取微博停用词"""
        return {
            # 微博相关
            '微博', '转发', '评论', '点赞', '收藏', '分享',
            '热搜', '话题', '超话', '热门',
            '博主', '大V', '网红', 'up主',
            '哈哈', '呵呵', '嘿嘿', '嘻嘻',
            '233', '666', '888', 'xswl', 'yyds',
            '捂脸', '笑哭', '笑死', '吃瓜', '围观',
            '前排', '沙发', '板凳', '地板',
            '官微', '官方', '小编', '管理员',
        }

    def _get_news_stopwords(self) -> Set[str]:
        """获取新闻停用词"""
        return {
            '本报讯', '记者', '报道', '通讯员', '摄影',
            '编辑', '责编', '审核', '校对', '签发',
            '电', '讯', '据', '报道', '获悉',
            '日前', '近日', '昨天', '今天', '明天',
            '据悉', '据了解', '据报道', '据介绍',
            '表示', '指出', '强调', '要求', '希望',
        }

    def _get_shopping_stopwords(self) -> Set[str]:
        """获取电商停用词"""
        return {
            '宝贝', '商品', '产品', '物品',
            '卖家', '买家', '客服', '掌柜',
            '快递', '物流', '包装', '发货',
            '质量', '价格', '性价比', '优惠',
            '好评', '中评', '差评', '追评',
            '推荐', '不推荐', '建议', '不值得',
        }

    def _get_movie_stopwords(self) -> Set[str]:
        """获取电影评论停用词"""
        return {
            '电影', '影片', '片子', '剧情',
            '导演', '演员', '主演', '配角',
            '特效', '画面', '音乐', '配乐',
            '情节', '故事', '结局', '开头',
            '推荐', '不推荐', '值得', '不值得',
            '星', '颗星', '分', '评分',
        }

    def _get_academic_stopwords(self) -> Set[str]:
        """获取学术停用词"""
        return {
            '研究', '论文', '文献', '综述',
            '方法', '结果', '讨论', '结论',
            '实验', '数据', '分析', '统计',
            '表', '图', '公式', '定理',
            '参考文献', '引用', '注释',
            '作者', '单位', '摘要', '关键词',
        }

    def _get_legal_stopwords(self) -> Set[str]:
        """获取法律停用词"""
        return {
            '法', '法律', '法规', '条例',
            '规定', '条款', '条目', '项',
            '违反', '违法', '违规', '犯罪',
            '法院', '法庭', '法官', '律师',
            '原告', '被告', '证人', '证据',
            '判决', '裁定', '决定', '裁决',
        }

    def _get_medical_stopwords(self) -> Set[str]:
        """获取医疗停用词"""
        return {
            '患者', '病人', '病例', '病历',
            '症状', '体征', '诊断', '治疗',
            '药物', '药品', '剂量', '用法',
            '检查', '检验', '化验', '结果',
            '医院', '医生', '护士', '科室',
        }

    def get_stopwords(self, domains: Optional[List[str]] = None) -> Set[str]:
        """
        获取停用词表

        Args:
            domains: 领域列表，如["common", "weibo"]

        Returns:
            Set[str]: 停用词集合
        """
        if domains is None:
            domains = ["common"]

        stopwords = set()
        for domain in domains:
            if domain in self._stopwords:
                stopwords.update(self._stopwords[domain])

        return stopwords

    def add_stopwords(self, words: List[str], domain: str = "custom"):
        """
        添加停用词

        Args:
            words: 停用词列表
            domain: 领域名称
        """
        if domain not in self._stopwords:
            self._stopwords[domain] = set()

        self._stopwords[domain].update(words)

    def remove_stopwords(self, words: List[str], domain: Optional[str] = None):
        """
        移除停用词

        Args:
            words: 要移除的词列表
            domain: 领域名称，None表示从所有领域移除
        """
        if domain:
            if domain in self._stopwords:
                for word in words:
                    if word in self._stopwords[domain]:
                        self._stopwords[domain].remove(word)
        else:
            for dom in self._stopwords:
                for word in words:
                    if word in self._stopwords[dom]:
                        self._stopwords[dom].remove(word)

    def save_to_file(self, filepath: str, domain: Optional[str] = None):
        """
        保存停用词到文件

        Args:
            filepath: 文件路径
            domain: 领域名称，None表示保存所有领域
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if domain:
                    if domain in self._stopwords:
                        for word in sorted(self._stopwords[domain]):
                            f.write(f"{word}\n")
                else:
                    for dom, words in sorted(self._stopwords.items()):
                        f.write(f"# {dom}\n")
                        for word in sorted(words):
                            f.write(f"{word}\n")
                        f.write("\n")
            print(f"✅ 停用词已保存到 {filepath}")
        except Exception as e:
            print(f"❌ 保存停用词失败: {e}")

    def load_from_file(self, filepath: str, domain: str = "custom"):
        """
        从文件加载停用词

        Args:
            filepath: 文件路径
            domain: 领域名称
        """
        if domain not in self._stopwords:
            self._stopwords[domain] = set()

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self._stopwords[domain].add(line)
            print(f"✅ 从 {filepath} 加载停用词成功")
        except FileNotFoundError:
            print(f"⚠️ 停用词文件不存在: {filepath}")
        except Exception as e:
            print(f"❌ 加载停用词失败: {e}")

    def get_domain_list(self) -> List[str]:
        """
        获取可用领域列表

        Returns:
            List[str]: 领域名称列表
        """
        return list(self._stopwords.keys())

    def get_domain_size(self, domain: str) -> int:
        """
        获取指定领域的停用词数量

        Args:
            domain: 领域名称

        Returns:
            int: 停用词数量
        """
        if domain in self._stopwords:
            return len(self._stopwords[domain])
        return 0

    def get_total_size(self) -> int:
        """
        获取所有停用词的总数（去重后）

        Returns:
            int: 停用词总数
        """
        all_words = set()
        for words in self._stopwords.values():
            all_words.update(words)
        return len(all_words)


# 全局停用词管理器实例
_stopwords_manager = StopWordsManager()


def get_stopwords(domains: Optional[List[str]] = None) -> Set[str]:
    """
    获取停用词表（便捷函数）

    Args:
        domains: 领域列表

    Returns:
        Set[str]: 停用词集合
    """
    return _stopwords_manager.get_stopwords(domains)


def clean_text_with_stopwords(text: str, domains: Optional[List[str]] = None) -> str:
    """
    使用停用词清洗文本（便捷函数）

    Args:
        text: 原始文本
        domains: 领域列表

    Returns:
        str: 清洗后的文本
    """
    if not text:
        return ""

    stopwords = get_stopwords(domains)

    # 尝试使用jieba分词
    try:
        import jieba
        words = jieba.lcut(text)
    except ImportError:
        # 如果jieba不可用，使用简单分词
        words = [char for char in text]

    # 过滤停用词
    filtered_words = []
    for word in words:
        word = word.strip()
        if word and word not in stopwords and not word.isspace():
            # 过滤短词（除非是中文或英文单词）
            if len(word) >= 2 or word.isalpha():
                filtered_words.append(word)

    return ' '.join(filtered_words)


def get_stopwords_manager() -> StopWordsManager:
    """
    获取停用词管理器实例

    Returns:
        StopWordsManager: 停用词管理器
    """
    return _stopwords_manager


# 测试函数
def test_stopwords():
    """测试停用词功能"""
    print("🧪 测试停用词功能...")

    # 测试文本
    test_text = "今天微博热搜上有个话题很有趣，网友们都在讨论#这个话题#，哈哈！"

    # 使用通用停用词
    cleaned1 = clean_text_with_stopwords(test_text, ["common"])
    print(f"通用清洗: {cleaned1}")

    # 使用微博停用词
    cleaned2 = clean_text_with_stopwords(test_text, ["common", "weibo"])
    print(f"微博清洗: {cleaned2}")

    # 统计停用词数量
    manager = get_stopwords_manager()
    common_count = manager.get_domain_size("common")
    weibo_count = manager.get_domain_size("weibo")
    total_count = manager.get_total_size()

    print(f"通用停用词: {common_count} 个")
    print(f"微博停用词: {weibo_count} 个")
    print(f"总停用词数: {total_count} 个")
    print(f"可用领域: {', '.join(manager.get_domain_list())}")

    return cleaned1, cleaned2


if __name__ == "__main__":
    test_stopwords()