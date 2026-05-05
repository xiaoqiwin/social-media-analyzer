# -*- coding: utf-8 -*-
"""
数据可视化模块 - 交互式三维关联分析版
功能：生成交互式"热度-传播-情感"三维关联分析柱状图
作者：Python数据可视化导师
学生：大二初学者
日期：2026-05-02
"""

import pymysql
import jieba
from collections import Counter
from datetime import datetime, timedelta
import time
import os
import re
import json
import math
from typing import List, Tuple, Dict, Any, Optional, Set

# 导入项目模块
from config import get_db_connection
import utils

# 导入pyecharts
try:
    from pyecharts import options as opts
    from pyecharts.charts import WordCloud, Line, Pie, Bar, Grid, Scatter
    from pyecharts.commons.utils import JsCode

    PYECHARTS_AVAILABLE = True
except ImportError:
    PYECHARTS_AVAILABLE = False
    print("⚠️ 未安装pyecharts，请运行: pip install pyecharts")

# 导入jieba
try:
    import jieba

    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("⚠️ 未安装jieba，请运行: pip install jieba")

# 获取日志记录器
logger = utils.get_logger(__name__)

# ==================== 增强停用词表 ====================
ENHANCED_STOPWORDS = {
    # 1. 基础虚词
    '的', '了', '是', '在', '和', '就', '都', '而', '及', '与', '着', '或', '个', '人', '这', '那', '这个', '那个',
    '什么', '怎么', '为什么', '可以', '但', '很', '好', '要', '会', '能', '来', '去', '到', '说', '看', '知道', '觉得',
    '认为', '想', '看到', '听到', '感到', '啊', '呀', '呢', '吧', '吗', '嗯', '哦', '哈', '哈哈', '呵呵', '嘿嘿',
    '自己', '这样', '那样', '那么', '这么', '之', '者', '得', '地', '不', '没', '没有', '不是', '不能', '不会', '不想',
    '不要', '别', '对', '对于', '关于', '从', '向', '往', '朝', '被', '给', '上', '下', '左', '右', '前', '后', '里',
    '外', '中', '内', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '两', '也', '又', '还', '再', '更',
    '最', '太', '非常', '特别', '比较', '已经', '正在', '将要', '曾经', '经常', '总是', '有时', '偶尔', '因为', '所以',
    '如果', '虽然', '但是', '然而', '而且', '并且', '不过', '为了', '由于', '因此', '于是', '那么', '然后', '接着',
    '而且', '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '它们', '我的', '你的', '他的', '她的',
    '它的',
    '我们的', '你们的', '他们的', '俺', '咱', '人家', '别人', '他人', '旁人', '对方', '某人', '各位', '诸位', '大家',
    '全体', '群众', '观众', '读者', '网友', '本人', '自身', '本尊', '本座', '您', '谁', '何', '啥', '哪', '哪些', '每',
    '各', '某些', '有些', '任何', '所有', '一切',

    # 2. 高频无意义词
    '就是', '不是', '没有', '真的', '什么', '怎么', '为什么', '知道', '觉得', '认为', '感觉', '感到', '看到', '听到',
    '想到', '说到', '可以', '可能', '应该', '能够', '会', '能', '要', '想', '愿意', '还是', '或者', '要么', '以及',
    '还有',
    '另外', '此外', '而且', '这样', '那样', '这么', '那么', '如此', '一样', '一般', '通常', '已经', '曾经', '正在',
    '将要',
    '马上', '立刻', '顿时', '忽然', '现在', '当时', '以前', '以后', '后来', '之前', '之后', '然后', '今天', '明天',
    '昨天',
    '前天', '后天', '每天', '天天', '早上', '上午', '中午', '下午', '晚上', '凌晨', '夜里', '时候', '时间', '时刻',
    '期间',
    '阶段', '过程', '结果', '开始', '结束', '完成', '进行', '继续', '停止', '结束', '出来', '进去', '过来', '过去',
    '起来',
    '下去', '上来', '一下', '一些', '一点', '一方面', '一直', '一切', '一样', '很多', '许多', '大量', '不少', '几个',
    '各种',
    '太', '非常', '特别', '十分', '极其', '相当', '比较', '挺', '怪', '很', '最', '更', '太', '真', '实在', '确实',
    '的确',
    '只', '仅', '就', '才', '都', '全', '总', '共', '一概', '根本', '简直', '几乎', '差不多', '大概', '大约', '约',
    '其实',
    '实际上', '事实上', '说白了', '说到底', '归根到底', '反正', '横竖', '左右', '上下', '前后', '内外', '里外', '不仅',
    '不但',
    '不光', '不只', '而且', '并且', '况且', '虽然', '尽管', '虽说', '即使', '哪怕', '就算', '纵然', '但是', '可是',
    '然而',
    '不过', '只是', '偏偏', '因为', '由于', '因此', '因而', '所以', '于是', '从而', '如果', '假如', '假使', '假若',
    '倘若',
    '要是', '若是', '无论', '不管', '不论', '任凭', '只要', '只有', '除非', '一边', '一方面', '一直', '一块儿', '一起',
    '一道',
    '又', '也', '还', '再', '更', '最', '越', '愈', '越发',

    # 3. 社交媒体专用词
    '微博', '转发', '评论', '点赞', '收藏', '分享', '关注', '粉丝', '热搜', '话题', '超话', '热门', '热搜榜', '话题榜',
    '博主', '大V', '网红', 'up主', '主播', '小编', '管理员', '客户端', 'APP', '小程序', '公众号', '官微', '官方',
    '客服',
    '置顶', '精华', '推荐', '精选', '哈哈', '呵呵', '嘿嘿', '嘻嘻', '哈哈哈哈', '哈哈哈哈哈哈', '233', '666', '888',
    'xswl', 'yyds', 'awsl', 'dbq', 'bhs', '捂脸', '笑哭', '笑死', '笑尿', '笑疯', '无语', '无奈', '摊手', '耸肩',
    '扶额',
    '狗头', 'doge', '滑稽', '吃瓜', '围观', '路过', '打卡', '签到', '冒泡', '潜水', '前排', '沙发', '板凳', '顶', '赞',
    '踩',
    '微博智', '视频', '图片', '链接', '网页', 'http', 'https', 'com', 'cn', 'www', 'html', 'php', 'asp',

    # 4. 网络用语/口语
    '卧槽', '我靠', '我去', '我擦', '尼玛', '妈呀', '天哪', '天啊', 'emmmm', 'emmm', 'hhhh', 'hhhhh', '啊啊', '啊啊啊',
    '哦哦', '嗯嗯', '对对', '好好', '行行', '算了', '罢了', '而已', '罢了', '随便', '随意', '任意', '爱咋咋地',
    '无所谓',
    '不在乎', '拜托', '求求', '谢谢', '感谢', '多谢', '不用谢', '不客气', '加油', '努力', '坚持', '奋斗', '拼搏',
    '冲刺',

    # 5. 标点符号和特殊字符
    ' ', '\t', '\n', '\r', '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+', '[', ']', '{',
    '}',
    '\\', '|', ';', ':', "'", '"', ',', '<', '>', '.', '?', '/', '·', '！', '￥', '…', '（', '）', '—', '【', '】',
    '、', '；', '：', '「', '」', '『', '』', '《', '》', '，', '。', '？', '～', '`', '＠', '＃', '＄', '％', '＾', '＆',
    '＊', '０', '１', '２', '３', '４', '５', '６', '７', '８', '９',
}


def filter_words(words: List[str]) -> List[str]:
    """执行6层严格过滤"""
    filtered_words = []

    for word in words:
        word = word.strip()

        # 1. 停用词过滤
        if word in ENHANCED_STOPWORDS:
            continue

        # 2. 纯数字过滤
        if word.isdigit():
            continue

        # 3. 纯标点过滤
        if re.match(r'^[^\w\u4e00-\u9fff]+$', word):
            continue

        # 4. 中文单字过滤（保留英文单词）
        if len(word) == 1 and '\u4e00' <= word <= '\u9fff':
            continue

        # 5. 过长词过滤
        if len(word) > 10:
            continue

        # 6. 特殊字符过滤（保留纯中文词）
        if re.search(r'[^\u4e00-\u9fff\w]', word):
            continue

        filtered_words.append(word)

    return filtered_words


def clean_text_for_wordcloud(text: str) -> str:
    """清洗文本，用于词云生成"""
    if not text:
        return ""

    # 去掉URL
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)

    # 去掉@用户名
    text = re.sub(r'@[^\s]+', '', text)

    # 去掉#话题#
    text = re.sub(r'#([^#]+)#', '', text)

    # 去掉表情符号[doge]
    text = re.sub(r'\[[^\]]+\]', '', text)

    # 去掉HTML标签
    text = re.sub(r'<[^>]+>', '', text)

    return text


def ensure_charts_dir() -> str:
    """确保图表输出目录存在"""
    return utils.ensure_output_dir(['charts'])


def format_hot_value(hot_value: float) -> str:
    """
    格式化热度值

    Args:
        hot_value: 热度值

    Returns:
        格式化后的热度字符串
    """
    if hot_value >= 10000:
        return f"{hot_value / 10000:.1f}万"
    elif hot_value >= 1000:
        return f"{hot_value / 1000:.1f}千"
    else:
        return str(int(hot_value))


def get_dominant_sentiment(positive_ratio: float, negative_ratio: float, neutral_ratio: float) -> str:
    """
    获取主导情感

    Args:
        positive_ratio: 正面占比
        negative_ratio: 负面占比
        neutral_ratio: 中性占比

    Returns:
        主导情感标签
    """
    if positive_ratio >= negative_ratio and positive_ratio >= neutral_ratio:
        return "positive"
    elif negative_ratio >= positive_ratio and negative_ratio >= neutral_ratio:
        return "negative"
    else:
        return "neutral"


def get_events_for_search(conn) -> List[Dict]:
    """获取可用于搜索的事件列表"""
    cursor = None
    try:
        cursor = conn.cursor()
        sql = """
        SELECT 
            e.id,
            e.title,
            e.hot_value,
            COUNT(c.id) as comment_count
        FROM hot_events e
        LEFT JOIN comments c ON e.id = c.event_id
        GROUP BY e.id, e.title, e.hot_value
        HAVING COUNT(c.id) > 0
        ORDER BY e.hot_value DESC
        LIMIT 100
        """
        cursor.execute(sql)
        events = cursor.fetchall()
        return events
    except Exception as e:
        logger.error(f"获取事件列表失败: {e}")
        return []
    finally:
        if cursor:
            cursor.close()


def generate_wordcloud(conn, event_id: Optional[int] = None, max_words: int = 100) -> Optional[str]:
    """生成词云图，支持按事件搜索，词大小按词频比例缩放"""
    if not PYECHARTS_AVAILABLE or not JIEBA_AVAILABLE:
        logger.error("未安装pyecharts或jieba，无法生成词云图")
        return None

    cursor = None
    try:
        cursor = conn.cursor()

        # 获取评论内容
        if event_id:
            sql = """
            SELECT content 
            FROM comments 
            WHERE event_id = %s AND LENGTH(content) > 5
            LIMIT 2000
            """
            cursor.execute(sql, (event_id,))
        else:
            sql = """
            SELECT content 
            FROM comments 
            WHERE LENGTH(content) > 5
            ORDER BY like_count DESC
            LIMIT 2000
            """
            cursor.execute(sql)

        comments = cursor.fetchall()

        if not comments:
            logger.warning("没有评论数据生成词云图")
            return None

        logger.info(f"获取到 {len(comments)} 条评论")

        # 合并所有评论并清洗
        all_text = ""
        for comment in comments:
            cleaned_comment = clean_text_for_wordcloud(comment['content'])
            all_text += cleaned_comment + " "

        logger.info("文本清洗完成，开始分词...")

        # 使用jieba分词
        words = jieba.lcut(all_text)
        logger.info(f"原始分词数量: {len(words)}")

        # 执行6层严格过滤
        filtered_words = filter_words(words)
        logger.info(f"过滤后词数: {len(filtered_words)}")

        if len(filtered_words) < 10:
            logger.warning("过滤后有效关键词不足")
            return None

        # 统计词频
        word_counts = Counter(filtered_words)

        # 取前max_words个词
        top_words = word_counts.most_common(max_words)

        # 打印TOP20关键词
        logger.info("TOP20关键词:")
        for i, (word, count) in enumerate(top_words[:20], 1):
            logger.info(f"  {i:2d}. {word:10s}: {count}")

        # 按最小最大词频比例计算每个词的大小
        # 实现差异化：出现次数越多词越大，出现越少词越小
        min_count = top_words[-1][1]  # 最小词频
        max_count = top_words[0][1]   # 最大词频

        # 为了避免除零，确保最小值至少为1
        if max_count == min_count:
            max_count = min_count + 1

        # 定义字号范围
        min_font_size = 14
        max_font_size = 120

        # 按比例缩放每个词的大小
        data = []
        for word, count in top_words:
            # 线性比例缩放
            ratio = (count - min_count) / (max_count - min_count)
            font_size = int(min_font_size + ratio * (max_font_size - min_font_size))
            # 确保至少为最小值
            font_size = max(font_size, min_font_size)
            data.append((word, font_size))

        # 获取图表标题
        if event_id:
            cursor.execute("SELECT title FROM hot_events WHERE id = %s", (event_id,))
            event_result = cursor.fetchone()
            event_title = event_result['title'] if event_result else f"事件{event_id}"
            chart_title = f"词云图 - {event_title[:30]}"
            series_name = f"{event_title[:20]}高频词"
        else:
            chart_title = "热点话题高频词云"
            series_name = "热点话题高频词"

        # 创建词云图，背景设为白色
        wordcloud = (
            WordCloud(
                init_opts=opts.InitOpts(
                    bg_color="#ffffff",
                    width="100%",
                    height="600px"
                )
            )
            .add(
                series_name=series_name,
                data_pair=data,
                word_size_range=[min_font_size, max_font_size],
                shape="circle",
                rotate_step=45,
                textstyle_opts=opts.TextStyleOpts(font_family="Microsoft YaHei")
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=chart_title,
                    title_textstyle_opts=opts.TextStyleOpts(font_size=20)
                ),
                tooltip_opts=opts.TooltipOpts(
                    is_show=True,
                    formatter=JsCode("""
                        function(params) {
                            return params.name + ': ' + params.value + '次';
                        }
                    """)
                ),
            )
        )

        # 保存文件
        output_dir = ensure_charts_dir()
        if event_id:
            file_path = os.path.join(output_dir, f"wordcloud_event_{event_id}.html")
        else:
            file_path = os.path.join(output_dir, "wordcloud.html")
        wordcloud.render(file_path)

        logger.info(f"词云图已保存: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"生成词云图失败: {e}")
        return None
    finally:
        if cursor:
            cursor.close()


def get_all_events_wordcloud_data(conn) -> Dict[int, List[Tuple[str, int]]]:
    """获取所有事件的词云数据，用于嵌入单个HTML"""
    if not JIEBA_AVAILABLE:
        return {}

    cursor = None
    try:
        cursor = conn.cursor()

        # 获取所有有评论的事件
        cursor.execute("""
            SELECT DISTINCT event_id 
            FROM comments 
            WHERE LENGTH(content) > 5
        """)
        event_ids = [row['event_id'] for row in cursor.fetchall()]

        all_wordcloud_data = {}

        for event_id in event_ids:
            cursor.execute("""
                SELECT content 
                FROM comments 
                WHERE event_id = %s AND LENGTH(content) > 5
                LIMIT 500
            """, (event_id,))
            comments = cursor.fetchall()

            if not comments:
                continue

            # 合并并清洗文本
            all_text = ""
            for comment in comments:
                cleaned = clean_text_for_wordcloud(comment['content'])
                all_text += cleaned + " "

            # 分词过滤
            words = jieba.lcut(all_text)
            filtered = filter_words(words)

            if len(filtered) < 5:
                continue

            # 统计词频
            word_counts = Counter(filtered)
            top_words = word_counts.most_common(50)

            if top_words:
                # 计算比例缩放后的字号
                min_count = top_words[-1][1]
                max_count = top_words[0][1]
                if max_count == min_count:
                    max_count = min_count + 1

                min_font = 12
                max_font = 80

                scaled_data = []
                for word, count in top_words:
                    ratio = (count - min_count) / (max_count - min_count)
                    font_size = int(min_font + ratio * (max_font - min_font))
                    scaled_data.append((word, font_size))

                all_wordcloud_data[event_id] = scaled_data

        # 同时获取全部事件的词云数据
        cursor.execute("""
            SELECT content 
            FROM comments 
            WHERE LENGTH(content) > 5
            ORDER BY like_count DESC
            LIMIT 2000
        """)
        all_comments = cursor.fetchall()

        if all_comments:
            all_text = ""
            for comment in all_comments:
                cleaned = clean_text_for_wordcloud(comment['content'])
                all_text += cleaned + " "

            words = jieba.lcut(all_text)
            filtered = filter_words(words)

            if len(filtered) >= 10:
                word_counts = Counter(filtered)
                top_words = word_counts.most_common(100)

                min_count = top_words[-1][1]
                max_count = top_words[0][1]
                if max_count == min_count:
                    max_count = min_count + 1

                min_font = 14
                max_font = 120

                scaled_data = []
                for word, count in top_words:
                    ratio = (count - min_count) / (max_count - min_count)
                    font_size = int(min_font + ratio * (max_font - min_font))
                    scaled_data.append((word, font_size))

                all_wordcloud_data[0] = scaled_data  # 0表示全部事件

        return all_wordcloud_data

    except Exception as e:
        logger.error(f"获取词云数据失败: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()


def generate_wordcloud_with_search(conn) -> Optional[str]:
    """生成带事件搜索功能的词云图HTML页面（保留作为独立页面）"""
    return generate_wordcloud(conn)


def generate_hot_trend(conn) -> Optional[str]:
    """生成热度趋势折线图"""
    if not PYECHARTS_AVAILABLE:
        logger.error("未安装pyecharts，无法生成折线图")
        return None

    cursor = None
    try:
        cursor = conn.cursor()

        # SQL：查询当天所有事件，按小时聚合总热度和事件数
        sql = """
        SELECT 
            HOUR(created_at) as hour, 
            SUM(hot_value) as total_hot_value, 
            COUNT(*) as event_count 
        FROM hot_events 
        WHERE DATE(created_at) = CURDATE() 
        GROUP BY HOUR(created_at) 
        ORDER BY hour
        """
        cursor.execute(sql)
        results = cursor.fetchall()

        # 如果没有今天的数据，自动取最近一天的数据
        if not results:
            logger.info("没有今天的数据，查询最近一天的数据...")
            sql = """
            SELECT 
                HOUR(created_at) as hour, 
                SUM(hot_value) as total_hot_value, 
                COUNT(*) as event_count 
            FROM hot_events 
            WHERE DATE(created_at) = (
                SELECT MAX(DATE(created_at)) FROM hot_events
            )
            GROUP BY HOUR(created_at) 
            ORDER BY hour
            """
            cursor.execute(sql)
            results = cursor.fetchall()

        if not results:
            logger.warning("没有热度数据")
            return None

        # 处理数据
        hours = []
        hot_values = []
        event_counts = []

        for row in results:
            hour = row['hour']
            hours.append(f"{int(hour)}:00")
            hot_values.append(float(row['total_hot_value'] or 0))
            event_counts.append(int(row['event_count'] or 0))

        if len(hours) < 2:
            logger.warning("数据点不足，无法展示趋势")
            return None

        # 创建折线图，背景设为白色
        line = (
            Line(
                init_opts=opts.InitOpts(
                    bg_color="#ffffff",
                    width="100%",
                    height="500px"
                )
            )
            .add_xaxis(hours)
            .add_yaxis(
                "总热度值",
                hot_values,
                yaxis_index=0,
                is_smooth=True,
                linestyle_opts=opts.LineStyleOpts(width=3),
                itemstyle_opts=opts.ItemStyleOpts(color="#5470c6"),
                label_opts=opts.LabelOpts(is_show=False),
                areastyle_opts=opts.AreaStyleOpts(opacity=0.1, color="#5470c6")
            )
            .add_yaxis(
                "事件数",
                event_counts,
                yaxis_index=1,
                is_smooth=True,
                linestyle_opts=opts.LineStyleOpts(width=2, type_="dashed"),
                itemstyle_opts=opts.ItemStyleOpts(color="#91cc75"),
                label_opts=opts.LabelOpts(is_show=False)
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="历史热点总热度趋势",
                    subtitle="按小时聚合所有事件热度",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=20)
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    formatter=JsCode("""
                    function(params) {
                        return '时间: ' + params[0].axisValue + '<br/>' +
                               '总热度: ' + params[0].value + '<br/>' +
                               '事件数: ' + params[1].value;
                    }
                    """)
                ),
                xaxis_opts=opts.AxisOpts(
                    name="时间（小时）",
                    name_location="middle",
                    name_gap=30,
                    axislabel_opts=opts.LabelOpts(rotate=45)
                ),
                yaxis_opts=opts.AxisOpts(
                    name="总热度值",
                    name_location="middle",
                    name_gap=50
                ),
                legend_opts=opts.LegendOpts(
                    pos_top="5%"
                ),
                datazoom_opts=[opts.DataZoomOpts()],
            )
        )

        # 添加第二个Y轴
        line.extend_axis(
            yaxis=opts.AxisOpts(
                name="事件数",
                name_location="middle",
                name_gap=50,
                axislabel_opts=opts.LabelOpts(formatter="{value}"),
                splitline_opts=opts.SplitLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(opacity=0.2)
                ),
            )
        )

        # 保存文件
        output_dir = ensure_charts_dir()
        file_path = os.path.join(output_dir, "hot_trend.html")
        line.render(file_path)

        logger.info(f"热度趋势图已保存: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"生成热度趋势图失败: {e}")
        return None
    finally:
        if cursor:
            cursor.close()


def generate_sentiment_pie(conn, event_id: Optional[int] = None) -> Optional[str]:
    """生成情感分布饼图"""
    if not PYECHARTS_AVAILABLE:
        logger.error("未安装pyecharts，无法生成饼图")
        return None

    cursor = None
    try:
        cursor = conn.cursor()

        if event_id:
            # 统计单个事件的情感分布
            sql = """
            SELECT 
                COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive,
                COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative,
                COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutral
            FROM comments 
            WHERE event_id = %s
            """
            cursor.execute(sql, (event_id,))
            result = cursor.fetchone()

            # 获取事件标题
            cursor.execute("SELECT title FROM hot_events WHERE id = %s", (event_id,))
            event_title = cursor.fetchone()['title']
            chart_title = f"基于规则和词典的匹配算法分类 ({event_title[:20]}...)"
        else:
            # 统计所有事件的情感分布
            sql = """
            SELECT
                COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive,
                COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative,
                COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutral
            FROM comments
            WHERE sentiment_label IS NOT NULL
            """
            cursor.execute(sql)
            result = cursor.fetchone()
            chart_title = "基于规则和词典的匹配算法分类展示正面、负面、中性评论的分布比例"

        if not result or (result['positive'] == 0 and result['negative'] == 0 and result['neutral'] == 0):
            logger.warning("没有情感分析数据")
            return None

        # 准备数据
        data = [
            ("正面", int(result['positive'] or 0)),
            ("负面", int(result['negative'] or 0)),
            ("中性", int(result['neutral'] or 0))
        ]

        # 过滤掉数量为0的项
        data = [(label, value) for label, value in data if value > 0]

        if not data:
            logger.warning("情感数据全为0")
            return None

        # 计算总数
        total = sum(value for _, value in data)

        # 创建饼图，背景设为白色
        pie = (
            Pie(
                init_opts=opts.InitOpts(
                    bg_color="#ffffff",
                    width="100%",
                    height="500px"
                )
            )
            .add(
                "",
                data,
                radius=["30%", "75%"],
                center=["50%", "50%"],
                rosetype="radius",
                label_opts=opts.LabelOpts(
                    formatter="{b}: {c} ({d}%)",
                    font_size=14
                )
            )
            .set_colors(["#91cc75", "#ee6666", "#fac858"])
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=chart_title,
                    subtitle=f"总评论数: {total}",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=20)
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="item",
                    formatter="{a} <br/>{b}: {c} ({d}%)"
                ),
                legend_opts=opts.LegendOpts(
                    orient="vertical",
                    pos_top="15%",
                    pos_left="2%"
                ),
            )
            .set_series_opts(
                label_opts=opts.LabelOpts(
                    font_size=12,
                    formatter="{b}: {c} ({d}%)"
                )
            )
        )

        # 保存文件
        output_dir = ensure_charts_dir()
        file_path = os.path.join(output_dir, "sentiment_pie.html")
        pie.render(file_path)

        logger.info(f"情感分布饼图已保存: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"生成情感分布饼图失败: {e}")
        return None
    finally:
        if cursor:
            cursor.close()


def generate_top10_bar(conn) -> Optional[str]:
    """生成TOP10热点事件柱状图"""
    if not PYECHARTS_AVAILABLE:
        logger.error("未安装pyecharts，无法生成柱状图")
        return None

    cursor = None
    try:
        cursor = conn.cursor()

        # 获取TOP10热点事件
        sql = """
        SELECT title, hot_value, source, crawl_date
        FROM hot_events
        WHERE crawl_date = CURDATE()
        ORDER BY hot_value DESC
        LIMIT 10
        """
        cursor.execute(sql)
        results = cursor.fetchall()

        if not results:
            # 如果没有今天的数据，获取所有数据
            sql = """
            SELECT title, hot_value, source, crawl_date
            FROM hot_events
            ORDER BY hot_value DESC
            LIMIT 10
            """
            cursor.execute(sql)
            results = cursor.fetchall()

        if not results:
            logger.warning("没有热点事件数据")
            return None

        # 处理数据
        titles = []
        hot_values = []

        for i, row in enumerate(results):
            title = row['title'][:20] + "..." if len(row['title']) > 20 else row['title']
            titles.append(title)
            hot_values.append(float(row['hot_value']))

        # 创建柱状图，背景设为白色
        bar = (
            Bar(
                init_opts=opts.InitOpts(
                    bg_color="#ffffff",
                    width="100%",
                    height="500px"
                )
            )
            .add_xaxis(titles)
            .add_yaxis(
                "热度值",
                hot_values,
                itemstyle_opts=opts.ItemStyleOpts(color="#5470c6"),
                label_opts=opts.LabelOpts(
                    position="top",
                    formatter="{c}",
                    font_size=12
                )
            )
            .reversal_axis()
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="TOP10热点事件",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=20)
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    formatter=JsCode("""
                    function(params) {
                        var title = %s[params[0].dataIndex];
                        var value = params[0].value;
                        var source = %s[params[0].dataIndex];
                        var date = %s[params[0].dataIndex];
                        return '标题: ' + title + '<br/>' +
                               '热度: ' + value + '<br/>' +
                               '来源: ' + source + '<br/>' +
                               '日期: ' + date;
                    }
                    """ % (
                        [row['title'] for row in results],
                        [row['source'] for row in results],
                        [str(row['crawl_date']) for row in results]
                    ))
                ),
                xaxis_opts=opts.AxisOpts(
                    name="热度值",
                    name_location="middle",
                    name_gap=30
                ),
                yaxis_opts=opts.AxisOpts(
                    name="事件标题",
                    name_location="middle",
                    name_gap=50,
                    axislabel_opts=opts.LabelOpts(font_size=12)
                ),
                datazoom_opts=[opts.DataZoomOpts(type_="inside")],
            )
        )

        # 保存文件
        output_dir = ensure_charts_dir()
        file_path = os.path.join(output_dir, "top10_bar.html")
        bar.render(file_path)

        logger.info(f"TOP10柱状图已保存: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"生成TOP10柱状图失败: {e}")
        return None
    finally:
        if cursor:
            cursor.close()


def generate_interactive_3d_chart(conn) -> Optional[str]:
    """
    生成交互式"热度-传播-情感"三维关联分析柱状图

    Args:
        conn: 数据库连接对象

    Returns:
        Optional[str]: 生成的HTML文件路径，失败返回None
    """
    cursor = None
    try:
        cursor = conn.cursor()

        # 检查sentiment_results表是否存在
        cursor.execute("""
        SELECT COUNT(*) as table_exists 
        FROM information_schema.tables 
        WHERE table_schema = DATABASE() 
        AND table_name = 'sentiment_results'
        """)
        table_result = cursor.fetchone()

        if not table_result or table_result['table_exists'] == 0:
            logger.warning("sentiment_results 表不存在，无法生成三维关联分析图")
            print("⚠️ 提示: sentiment_results 表不存在")
            print("   可能原因:")
            print("   1. 情感分析模块未运行")
            print("   2. 情感统计表未创建")
            print("   3. 数据库表结构不完整")
            print("   正在尝试备选方案...")
            return generate_3d_backup_chart(conn)

        # SQL获取事件数据
        sql = """
        SELECT 
            e.id, 
            e.title, 
            e.hot_value, 
            s.positive_count, 
            s.negative_count, 
            s.neutral_count, 
            s.total_count as comment_count, 
            CASE 
                WHEN s.total_count > 0 THEN s.positive_count * 100.0 / s.total_count
                ELSE 0 
            END as positive_ratio,
            CASE 
                WHEN s.total_count > 0 THEN s.negative_count * 100.0 / s.total_count
                ELSE 0 
            END as negative_ratio,
            CASE 
                WHEN s.total_count > 0 THEN s.neutral_count * 100.0 / s.total_count
                ELSE 0 
            END as neutral_ratio
        FROM hot_events e
        JOIN sentiment_results s ON e.id = s.event_id
        WHERE s.total_count >= 5
        ORDER BY e.hot_value DESC
        LIMIT 50
        """
        cursor.execute(sql)
        results = cursor.fetchall()

        if not results or len(results) < 2:
            logger.warning(f"数据不足，只有 {len(results) if results else 0} 个事件有完整统计数据")
            print(f"⚠️ 提示: 只有 {len(results) if results else 0} 个事件有情感统计数据")
            print("   最少需要2个有情感统计数据的事件")
            print("   正在尝试备选方案...")
            return generate_3d_backup_chart(conn)

        logger.info(f"获取到 {len(results)} 个事件进行三维关联分析")

        # 处理数据
        events_data = []
        for row in results:
            event_id = int(row['id'])
            title = row['title']
            # 标题截断（超过8字显示省略号）
            display_title = title[:8] + "..." if len(title) > 8 else title
            hot_value = float(row['hot_value'] or 0)
            comment_count = int(row['comment_count'] or 0)
            positive_ratio = float(row['positive_ratio'] or 0)
            negative_ratio = float(row['negative_ratio'] or 0)
            neutral_ratio = float(row['neutral_ratio'] or 0)

            # 格式化热度
            formatted_hot = format_hot_value(hot_value)

            # 确定主导情感
            dominant = get_dominant_sentiment(positive_ratio, negative_ratio, neutral_ratio)

            events_data.append({
                'id': event_id,
                'title': title,
                'display_title': display_title,
                'hot_value': hot_value,
                'formatted_hot': formatted_hot,
                'comment_count': comment_count,
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'neutral_ratio': neutral_ratio,
                'dominant': dominant
            })

        # 生成HTML文件
        output_dir = ensure_charts_dir()
        file_path = os.path.join(output_dir, "interactive_3d_chart.html")

        # 创建HTML内容
        html_content = generate_interactive_html(events_data)

        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"交互式三维关联分析图已保存: {file_path}")

        # 打印统计数据
        print(f"\n📊 三维关联分析数据统计:")
        print(f"   总事件数: {len(events_data)}")
        positive_events = [e for e in events_data if e['dominant'] == 'positive']
        negative_events = [e for e in events_data if e['dominant'] == 'negative']
        neutral_events = [e for e in events_data if e['dominant'] == 'neutral']
        print(f"   正面主导事件: {len(positive_events)} 个")
        print(f"   负面主导事件: {len(negative_events)} 个")
        print(f"   中性主导事件: {len(neutral_events)} 个")

        if positive_events:
            avg_positive_ratio = sum(e['positive_ratio'] for e in positive_events) / len(positive_events)
            print(f"   正面事件平均正面占比: {avg_positive_ratio:.1f}%")

        if negative_events:
            avg_negative_ratio = sum(e['negative_ratio'] for e in negative_events) / len(negative_events)
            print(f"   负面事件平均负面占比: {avg_negative_ratio:.1f}%")

        return file_path

    except Exception as e:
        logger.error(f"生成交互式三维关联分析图失败: {e}")
        import traceback
        traceback.print_exc()
        print(f"❌ 错误详情: {e}")
        print("正在尝试备选方案...")
        return generate_3d_backup_chart(conn)
    finally:
        if cursor:
            cursor.close()


def generate_3d_backup_chart(conn) -> Optional[str]:
    """
    生成备选的三维关联分析图（当sentiment_results表不存在时使用）

    Args:
        conn: 数据库连接对象

    Returns:
        Optional[str]: 生成的HTML文件路径，失败返回None
    """
    cursor = None
    try:
        cursor = conn.cursor()

        print("正在尝试备选方案：直接从comments表统计情感数据...")

        # SQL：直接从comments表统计每个事件的情感分布
        sql = """
        SELECT 
            e.id,
            e.title,
            e.hot_value,
            COUNT(c.id) as comment_count,
            COUNT(CASE WHEN c.sentiment_label = 'positive' THEN 1 END) as positive_count,
            COUNT(CASE WHEN c.sentiment_label = 'negative' THEN 1 END) as negative_count,
            COUNT(CASE WHEN c.sentiment_label = 'neutral' THEN 1 END) as neutral_count
        FROM hot_events e
        LEFT JOIN comments c ON e.id = c.event_id
        WHERE c.sentiment_label IS NOT NULL
        GROUP BY e.id, e.title, e.hot_value
        HAVING comment_count >= 5
        ORDER BY e.hot_value DESC
        LIMIT 30
        """
        cursor.execute(sql)
        results = cursor.fetchall()

        if not results or len(results) < 2:
            logger.warning(f"备选方案数据不足，只有 {len(results) if results else 0} 个事件")
            print(f"⚠️ 备选方案: 只有 {len(results) if results else 0} 个事件有评论数据")

            # 尝试更宽松的条件
            sql = """
            SELECT 
                e.id,
                e.title,
                e.hot_value,
                COUNT(c.id) as comment_count
            FROM hot_events e
            LEFT JOIN comments c ON e.id = c.event_id
            GROUP BY e.id, e.title, e.hot_value
            HAVING comment_count > 0
            ORDER BY e.hot_value DESC
            LIMIT 20
            """
            cursor.execute(sql)
            results = cursor.fetchall()

            if not results or len(results) < 2:
                print("❌ 备选方案失败：没有足够的数据生成图表")
                return None

        logger.info(f"备选方案获取到 {len(results)} 个事件")

        # 处理数据
        events_data = []
        for row in results:
            event_id = int(row['id'])
            title = row['title']
            display_title = title[:8] + "..." if len(title) > 8 else title
            hot_value = float(row['hot_value'] or 0)
            comment_count = int(row['comment_count'] or 0)

            # 计算情感占比
            positive_count = int(row.get('positive_count', 0) or 0)
            negative_count = int(row.get('negative_count', 0) or 0)
            neutral_count = int(row.get('neutral_count', 0) or 0)

            positive_ratio = 0
            negative_ratio = 0
            neutral_ratio = 0

            if comment_count > 0:
                positive_ratio = positive_count * 100.0 / comment_count
                negative_ratio = negative_count * 100.0 / comment_count
                neutral_ratio = neutral_count * 100.0 / comment_count

            # 格式化热度
            formatted_hot = format_hot_value(hot_value)

            # 确定主导情感
            dominant = get_dominant_sentiment(positive_ratio, negative_ratio, neutral_ratio)

            events_data.append({
                'id': event_id,
                'title': title,
                'display_title': display_title,
                'hot_value': hot_value,
                'formatted_hot': formatted_hot,
                'comment_count': comment_count,
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'neutral_ratio': neutral_ratio,
                'dominant': dominant
            })

        # 生成HTML文件
        output_dir = ensure_charts_dir()
        file_path = os.path.join(output_dir, "interactive_3d_chart_backup.html")

        # 创建HTML内容
        html_content = generate_interactive_html(events_data)

        # 在标题中添加提示
        html_content = html_content.replace(
            "三维关联分析：热度-传播-情感",
            "三维关联分析：热度-传播-情感（备选方案）"
        )

        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ 备选三维关联分析图已生成: {file_path}")
        print(f"   使用 {len(events_data)} 个事件的数据")
        print(f"   注: 从comments表直接统计，数据可能不完整")

        return file_path

    except Exception as e:
        logger.error(f"生成备选三维关联分析图失败: {e}")
        print(f"❌ 备选方案也失败: {e}")
        return None
    finally:
        if cursor:
            cursor.close()


def generate_interactive_html(events_data: List[Dict]) -> str:
    """
    生成交互式HTML内容

    Args:
        events_data: 事件数据列表

    Returns:
        HTML字符串
    """
    # 将数据转换为JSON字符串
    events_json = json.dumps(events_data, ensure_ascii=False)

    # 获取当前时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 创建HTML内容
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>三维关联分析：热度-传播-情感</title>

    <!-- 引入ECharts -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            background: #ffffff;
            color: #333;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* 头部 */
        .header {{
            background: white;
            border-radius: 12px;
            padding: 25px 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}

        .header h1 {{
            color: #1a1a1a;
            font-size: 28px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .header h1 .icon {{
            font-size: 32px;
        }}

        .subtitle {{
            color: #666;
            font-size: 15px;
        }}

        /* 控制面板 */
        .control-panel {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}

        .control-section {{
            margin-bottom: 20px;
        }}

        .control-section:last-child {{
            margin-bottom: 0;
        }}

        .section-title {{
            font-size: 16px;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .control-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .btn {{
            padding: 8px 16px;
            background: white;
            border: 1px solid #e1e5e9;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .btn:hover {{
            background: #f8f9fa;
            border-color: #d0d7de;
        }}

        .btn-primary {{
            background: #1890ff;
            color: white;
            border-color: #1890ff;
        }}

        .btn-primary:hover {{
            background: #40a9ff;
            border-color: #40a9ff;
        }}

        .btn-success {{
            background: #52c41a;
            color: white;
            border-color: #52c41a;
        }}

        .btn-success:hover {{
            background: #73d13d;
            border-color: #73d13d;
        }}

        .btn-warning {{
            background: #faad14;
            color: white;
            border-color: #faad14;
        }}

        .btn-warning:hover {{
            background: #ffc53d;
            border-color: #ffc53d;
        }}

        .btn-danger {{
            background: #ff4d4f;
            color: white;
            border-color: #ff4d4f;
        }}

        .btn-danger:hover {{
            background: #ff7875;
            border-color: #ff7875;
        }}

        /* 事件选择器 */
        .event-selector {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 12px;
            max-height: 300px;
            overflow-y: auto;
            padding: 5px;
        }}

        .event-card {{
            background: white;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            padding: 12px;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
        }}

        .event-card:hover {{
            border-color: #1890ff;
            box-shadow: 0 4px 12px rgba(24, 144, 255, 0.1);
        }}

        .event-card.selected {{
            border-color: #1890ff;
            background: #f0f7ff;
        }}

        .event-card.positive {{
            border-left: 4px solid #52c41a;
        }}

        .event-card.negative {{
            border-left: 4px solid #ff4d4f;
        }}

        .event-card.neutral {{
            border-left: 4px solid #faad14;
        }}

        .event-checkbox {{
            position: absolute;
            top: 10px;
            right: 10px;
            width: 20px;
            height: 20px;
            border: 2px solid #d9d9d9;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .event-checkbox.checked {{
            background: #1890ff;
            border-color: #1890ff;
        }}

        .event-checkbox.checked::after {{
            content: '✓';
            color: white;
            font-size: 12px;
        }}

        .event-title {{
            font-weight: 600;
            margin-bottom: 6px;
            font-size: 15px;
            padding-right: 25px;
        }}

        .event-stats {{
            display: flex;
            gap: 12px;
            font-size: 13px;
            color: #666;
        }}

        .event-stat {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .hot-value {{
            color: #1890ff;
            font-weight: 600;
        }}

        .comment-count {{
            color: #722ed1;
            font-weight: 600;
        }}

        .sentiment-badge {{
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}

        .sentiment-positive {{
            background: #f6ffed;
            color: #52c41a;
        }}

        .sentiment-negative {{
            background: #fff2f0;
            color: #ff4d4f;
        }}

        .sentiment-neutral {{
            background: #fffbe6;
            color: #faad14;
        }}

        /* 统计栏 */
        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}

        .stat-card {{
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}

        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 4px;
        }}

        .stat-label {{
            font-size: 13px;
            color: #666;
        }}

        .stat-positive {{
            color: #52c41a;
        }}

        .stat-negative {{
            color: #ff4d4f;
        }}

        .stat-neutral {{
            color: #faad14;
        }}

        /* 洞察面板 */
        .insight-panel {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}

        .insight-content {{
            line-height: 1.8;
        }}

        .insight-highlight {{
            font-weight: 600;
            color: #1890ff;
        }}

        .insight-warning {{
            color: #ff4d4f;
            font-weight: 600;
        }}

        /* 图表容器 */
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}

        .chart-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        #mainChart {{
            width: 100%;
            height: 500px;
        }}

        /* 图例 */
        .legend {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
        }}

        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
        }}

        .legend-positive {{
            background: #52c41a;
        }}

        .legend-negative {{
            background: #ff4d4f;
        }}

        .legend-neutral {{
            background: #faad14;
        }}

        /* 底部信息 */
        .footer {{
            text-align: center;
            color: #999;
            font-size: 13px;
            margin-top: 20px;
            padding: 20px;
        }}

        /* 响应式设计 */
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}

            .event-selector {{
                grid-template-columns: 1fr;
            }}

            .control-buttons {{
                flex-direction: column;
            }}

            .btn {{
                width: 100%;
                justify-content: center;
            }}

            .stats-bar {{
                grid-template-columns: 1fr;
            }}

            #mainChart {{
                height: 400px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>
                <span class="icon">📊</span>
                三维关联分析：热度-传播-情感
            </h1>
            <p class="subtitle">支持交互式事件对比分析 | 数据更新时间: {current_time}</p>
        </div>

        <!-- 控制面板 -->
        <div class="control-panel">
            <!-- 批量操作 -->
            <div class="control-section">
                <div class="section-title">
                    <span>🔧</span>
                    批量操作
                </div>
                <div class="control-buttons">
                    <button class="btn btn-primary" onclick="selectAll()">
                        <span>✓</span>
                        全选
                    </button>
                    <button class="btn btn-danger" onclick="deselectAll()">
                        <span>✕</span>
                        取消全选
                    </button>
                    <button class="btn btn-success" onclick="selectTop10()">
                        <span>🏆</span>
                        选中TOP10
                    </button>
                </div>
            </div>

            <!-- 排序选项 -->
            <div class="control-section">
                <div class="section-title">
                    <span>📈</span>
                    排序方式
                </div>
                <div class="control-buttons">
                    <button class="btn" onclick="sortByHot()">
                        <span>🔥</span>
                        按热度排序
                    </button>
                    <button class="btn" onclick="sortByComments()">
                        <span>💬</span>
                        按评论数排序
                    </button>
                </div>
            </div>

            <!-- 事件选择器 -->
            <div class="control-section">
                <div class="section-title">
                    <span>🎯</span>
                    事件选择器
                </div>
                <div class="event-selector" id="eventSelector">
                    <!-- 事件卡片将通过JavaScript动态生成 -->
                </div>
            </div>
        </div>

        <!-- 统计栏 -->
        <div class="stats-bar" id="statsBar">
            <!-- 统计卡片将通过JavaScript动态生成 -->
        </div>

        <!-- 洞察面板 -->
        <div class="insight-panel">
            <div class="section-title">
                <span>💡</span>
                智能洞察
            </div>
            <div class="insight-content" id="insightContent">
                <!-- 洞察内容将通过JavaScript动态生成 -->
            </div>
        </div>

        <!-- 主图表 -->
        <div class="chart-container">
            <div class="chart-title">
                <span>📊</span>
                热度-传播-情感三维关联分析
            </div>
            <div id="mainChart"></div>
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color legend-positive"></div>
                    <span>正面主导</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-negative"></div>
                    <span>负面主导</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-neutral"></div>
                    <span>中性主导</span>
                </div>
            </div>
        </div>

        <!-- 底部信息 -->
        <div class="footer">
            <p>© 2026 社交媒体热点话题分析系统 | 三维关联分析工具 v1.0</p>
            <p>使用ECharts生成，支持交互式操作 | 生成时间: {current_time}</p>
        </div>
    </div>

    <!-- 事件数据 -->
    <script>
        // 事件数据
        const allEvents = {events_json};

        // 选中的事件ID
        let selectedEventIds = [];

        // 排序状态
        let currentSort = 'hot'; // 'hot' 或 'comments'

        // 初始化函数
        function init() {{
            // 默认选中TOP10
            selectTop10();

            // 渲染事件选择器
            renderEventSelector();

            // 渲染统计栏
            renderStatsBar();

            // 渲染洞察面板
            renderInsightPanel();

            // 渲染图表
            renderChart();

            // 添加窗口大小变化监听
            window.addEventListener('resize', function() {{
                if (window.chartInstance) {{
                    window.chartInstance.resize();
                }}
            }});
        }}

        // 渲染事件选择器
        function renderEventSelector() {{
            const selector = document.getElementById('eventSelector');
            selector.innerHTML = '';

            // 根据当前排序状态排序事件
            const sortedEvents = [...allEvents];
            if (currentSort === 'hot') {{
                sortedEvents.sort((a, b) => b.hot_value - a.hot_value);
            }} else {{
                sortedEvents.sort((a, b) => b.comment_count - a.comment_count);
            }}

            sortedEvents.forEach(event => {{
                const isSelected = selectedEventIds.includes(event.id);

                // 确定情感标签和颜色
                let sentimentLabel, sentimentClass, sentimentColor;
                if (event.dominant === 'positive') {{
                    sentimentLabel = '正面';
                    sentimentClass = 'sentiment-positive';
                    sentimentColor = '#52c41a';
                }} else if (event.dominant === 'negative') {{
                    sentimentLabel = '负面';
                    sentimentClass = 'sentiment-negative';
                    sentimentColor = '#ff4d4f';
                }} else {{
                    sentimentLabel = '中性';
                    sentimentClass = 'sentiment-neutral';
                    sentimentColor = '#faad14';
                }}

                const card = document.createElement('div');
                card.className = `event-card ${{event.dominant}} ${{isSelected ? 'selected' : ''}}`;
                card.onclick = () => toggleEvent(event.id);
                card.title = event.title;

                card.innerHTML = `
                    <div class="event-checkbox ${{isSelected ? 'checked' : ''}}"></div>
                    <div class="event-title">${{event.display_title}}</div>
                    <div class="event-stats">
                        <div class="event-stat">
                            <span>🔥</span>
                            <span class="hot-value">${{event.formatted_hot}}</span>
                        </div>
                        <div class="event-stat">
                            <span>💬</span>
                            <span class="comment-count">${{event.comment_count}}</span>
                        </div>
                        <div class="event-stat">
                            <span>📊</span>
                            <span class="sentiment-badge ${{sentimentClass}}">${{sentimentLabel}}</span>
                        </div>
                    </div>
                `;

                selector.appendChild(card);
            }});
        }}

        // 渲染统计栏
        function renderStatsBar() {{
            const statsBar = document.getElementById('statsBar');
            const selectedEvents = allEvents.filter(e => selectedEventIds.includes(e.id));

            if (selectedEvents.length === 0) {{
                statsBar.innerHTML = '<div class="stat-card"><div class="stat-value">0</div><div class="stat-label">请选择至少一个事件进行分析</div></div>';
                return;
            }}

            // 计算统计指标
            const totalEvents = selectedEvents.length;
            const totalComments = selectedEvents.reduce((sum, e) => sum + e.comment_count, 0);
            const avgHotValue = selectedEvents.reduce((sum, e) => sum + e.hot_value, 0) / totalEvents;
            const avgPositiveRatio = selectedEvents.reduce((sum, e) => sum + e.positive_ratio, 0) / totalEvents;

            const positiveEvents = selectedEvents.filter(e => e.dominant === 'positive').length;
            const negativeEvents = selectedEvents.filter(e => e.dominant === 'negative').length;
            const neutralEvents = selectedEvents.filter(e => e.dominant === 'neutral').length;

            statsBar.innerHTML = `
                <div class="stat-card">
                    <div class="stat-value">${{totalEvents}}</div>
                    <div class="stat-label">选中事件数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${{totalComments}}</div>
                    <div class="stat-label">总评论数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${{avgHotValue.toFixed(0)}}</div>
                    <div class="stat-label">平均热度</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value stat-positive">${{avgPositiveRatio.toFixed(1)}}%</div>
                    <div class="stat-label">平均正面占比</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value stat-positive">${{positiveEvents}}</div>
                    <div class="stat-label">正面事件</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value stat-negative">${{negativeEvents}}</div>
                    <div class="stat-label">负面事件</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value stat-neutral">${{neutralEvents}}</div>
                    <div class="stat-label">中性事件</div>
                </div>
            `;
        }}

        // 渲染洞察面板
        function renderInsightPanel() {{
            const insightContent = document.getElementById('insightContent');
            const selectedEvents = allEvents.filter(e => selectedEventIds.includes(e.id));

            if (selectedEvents.length === 0) {{
                insightContent.innerHTML = '<p>请选择至少一个事件进行分析，获取智能洞察。</p>';
                return;
            }}

            if (selectedEvents.length < 2) {{
                insightContent.innerHTML = '<p>请选择至少2个事件进行对比分析。</p>';
                return;
            }}

            // 找出最高热度事件
            const maxHotEvent = [...selectedEvents].sort((a, b) => b.hot_value - a.hot_value)[0];

            // 找出最高传播事件
            const maxCommentEvent = [...selectedEvents].sort((a, b) => b.comment_count - a.comment_count)[0];

            // 统计正面/负面事件
            const positiveEvents = selectedEvents.filter(e => e.dominant === 'positive');
            const negativeEvents = selectedEvents.filter(e => e.dominant === 'negative');
            const neutralEvents = selectedEvents.filter(e => e.dominant === 'neutral');

            // 找出高热度负面事件
            const highHotNegativeEvents = negativeEvents.filter(e => e.hot_value > 10000);

            // 生成洞察文本
            let insightHTML = '<p>';

            // 1. 总体情况
            insightHTML += `当前选中 <span class="insight-highlight">${{selectedEvents.length}}个事件</span>进行分析。`;

            // 2. 最高热度事件
            insightHTML += ` 其中<span class="insight-highlight">"${{maxHotEvent.display_title}}"</span>热度最高(${{maxHotEvent.formatted_hot}})，`;

            // 3. 最高传播事件
            if (maxCommentEvent.id !== maxHotEvent.id) {{
                insightHTML += `<span class="insight-highlight">"${{maxCommentEvent.display_title}}"</span>讨论最热烈(${{maxCommentEvent.comment_count}}条评论)，`;
            }}

            // 4. 情感分布
            insightHTML += ` 从情感分布看，正面事件${{positiveEvents.length}}个，负面事件${{negativeEvents.length}}个，中性事件${{neutralEvents.length}}个。`;

            // 5. 高热度负面事件预警
            if (highHotNegativeEvents.length > 0) {{
                insightHTML += ` <span class="insight-warning">⚠️ 发现${{highHotNegativeEvents.length}}个高热度负面事件，需重点关注！</span>`;
            }}

            insightHTML += '</p>';

            // 6. 情感与热度关联
            if (negativeEvents.length > 0) {{
                const avgNegativeHot = negativeEvents.reduce((sum, e) => sum + e.hot_value, 0) / negativeEvents.length;
                const avgAllHot = selectedEvents.reduce((sum, e) => sum + e.hot_value, 0) / selectedEvents.length;

                if (avgNegativeHot > avgAllHot) {{
                    insightHTML += `<p>负面事件平均热度(${{avgNegativeHot.toFixed(0)}})高于整体平均(${{avgAllHot.toFixed(0)}})，说明负面情绪更容易引发高关注。</p>`;
                }}
            }}

            // 7. 传播与情感关联
            if (positiveEvents.length > 0 && negativeEvents.length > 0) {{
                const avgPositiveComments = positiveEvents.reduce((sum, e) => sum + e.comment_count, 0) / positiveEvents.length;
                const avgNegativeComments = negativeEvents.reduce((sum, e) => sum + e.comment_count, 0) / negativeEvents.length;

                if (avgNegativeComments > avgPositiveComments) {{
                    insightHTML += `<p>负面事件平均评论数(${{avgNegativeComments.toFixed(0)}})高于正面事件(${{avgPositiveComments.toFixed(0)}})，负面情绪更容易引发讨论。</p>`;
                }}
            }}

            insightContent.innerHTML = insightHTML;
        }}

        // 渲染图表
        function renderChart() {{
            const selectedEvents = allEvents.filter(e => selectedEventIds.includes(e.id));

            if (selectedEvents.length === 0) {{
                document.getElementById('mainChart').innerHTML = '<div style="text-align: center; padding: 50px; color: #999;">请选择至少一个事件进行图表分析</div>';
                return;
            }}

            // 根据当前排序状态排序选中的事件
            const chartEvents = [...selectedEvents];
            if (currentSort === 'hot') {{
                chartEvents.sort((a, b) => b.hot_value - a.hot_value);
            }} else {{
                chartEvents.sort((a, b) => b.comment_count - a.comment_count);
            }}

            // 准备图表数据
            const xAxisData = chartEvents.map(e => {{
                // X轴标签：事件标题 + 热度值
                return e.display_title + '\\n(' + e.formatted_hot + ')';
            }});

            const seriesData = chartEvents.map(e => {{
                // 柱高：评论数
                // 颜色：根据主导情感
                let color;
                if (e.dominant === 'positive') {{
                    color = '#52c41a';
                }} else if (e.dominant === 'negative') {{
                    color = '#ff4d4f';
                }} else {{
                    color = '#faad14';
                }}

                return {{
                    value: e.comment_count,
                    itemStyle: {{
                        color: color,
                        borderRadius: [4, 4, 0, 0]  // 顶部圆角
                    }},
                    // tooltip数据
                    eventId: e.id,
                    title: e.title,
                    hotValue: e.hot_value,
                    formattedHot: e.formatted_hot,
                    commentCount: e.comment_count,
                    positiveRatio: e.positive_ratio,
                    negativeRatio: e.negative_ratio,
                    neutralRatio: e.neutral_ratio,
                    dominant: e.dominant
                }};
            }});

            // 初始化ECharts实例
            const chartDom = document.getElementById('mainChart');
            if (window.chartInstance) {{
                window.chartInstance.dispose();
            }}
            window.chartInstance = echarts.init(chartDom);

            // 配置项
            const option = {{
                tooltip: {{
                    trigger: 'item',
                    formatter: function(params) {{
                        const data = params.data;
                        let sentimentLabel = '';
                        if (data.dominant === 'positive') {{
                            sentimentLabel = '正面主导';
                        }} else if (data.dominant === 'negative') {{
                            sentimentLabel = '负面主导';
                        }} else {{
                            sentimentLabel = '中性主导';
                        }}

                        return `
                            <div style="font-weight: bold; margin-bottom: 8px;">${{data.title}}</div>
                            <div>🔥 热度: ${{data.formattedHot}} (${{data.hotValue.toFixed(0)}})</div>
                            <div>💬 评论数: ${{data.commentCount}}</div>
                            <div>📊 情感分布:</div>
                            <div>  - 正面: ${{data.positiveRatio.toFixed(1)}}%</div>
                            <div>  - 负面: ${{data.negativeRatio.toFixed(1)}}%</div>
                            <div>  - 中性: ${{data.neutralRatio.toFixed(1)}}%</div>
                            <div>🎯 主导情感: ${{sentimentLabel}}</div>
                        `;
                    }},
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    borderColor: '#e1e5e9',
                    borderWidth: 1,
                    textStyle: {{
                        color: '#333',
                        fontSize: 13
                    }},
                    extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 6px;'
                }},
                grid: {{
                    left: '3%',
                    right: '4%',
                    bottom: '10%',
                    top: '10%',
                    containLabel: true
                }},
                xAxis: {{
                    type: 'category',
                    data: xAxisData,
                    axisLabel: {{
                        color: '#666',
                        fontSize: 12,
                        interval: 0,
                        formatter: function(value) {{
                            // 处理换行显示
                            return value.split('\\\\n').join('\\n');
                        }},
                        lineHeight: 16
                    }},
                    axisLine: {{
                        lineStyle: {{
                            color: '#e1e5e9'
                        }}
                    }},
                    axisTick: {{
                        alignWithLabel: true
                    }}
                }},
                yAxis: {{
                    type: 'value',
                    name: '评论数（传播量）',
                    nameTextStyle: {{
                        color: '#666',
                        fontSize: 13
                    }},
                    axisLabel: {{
                        color: '#666',
                        fontSize: 12
                    }},
                    axisLine: {{
                        show: true,
                        lineStyle: {{
                            color: '#e1e5e9'
                        }}
                    }},
                    splitLine: {{
                        lineStyle: {{
                            color: '#f0f0f0',
                            type: 'dashed'
                        }}
                    }}
                }},
                series: [
                    {{
                        name: '评论数',
                        type: 'bar',
                        barWidth: '60%',
                        data: seriesData,
                        label: {{
                            show: true,
                            position: 'top',
                            formatter: '{{c}}',
                            color: '#333',
                            fontSize: 12
                        }},
                        emphasis: {{
                            itemStyle: {{
                                shadowColor: 'rgba(0, 0, 0, 0.5)',
                                shadowBlur: 10
                            }}
                        }}
                    }}
                ],
                dataZoom: [
                    {{
                        type: 'inside',
                        xAxisIndex: 0,
                        start: 0,
                        end: 100
                    }},
                    {{
                        show: true,
                        xAxisIndex: 0,
                        type: 'slider',
                        bottom: 20,
                        start: 0,
                        end: 100,
                        height: 20,
                        backgroundColor: '#f0f0f0',
                        fillerColor: 'rgba(24, 144, 255, 0.2)',
                        borderColor: '#e1e5e9',
                        textStyle: {{
                            color: '#666',
                            fontSize: 12
                        }}
                    }}
                ]
            }};

            // 使用配置项和数据显示图表
            window.chartInstance.setOption(option);
        }}

        // 切换事件选择
        function toggleEvent(eventId) {{
            const index = selectedEventIds.indexOf(eventId);
            if (index === -1) {{
                selectedEventIds.push(eventId);
            }} else {{
                selectedEventIds.splice(index, 1);
            }}

            // 重新渲染所有组件
            renderEventSelector();
            renderStatsBar();
            renderInsightPanel();
            renderChart();
        }}

        // 全选
        function selectAll() {{
            selectedEventIds = allEvents.map(e => e.id);
            renderEventSelector();
            renderStatsBar();
            renderInsightPanel();
            renderChart();
        }}

        // 取消全选
        function deselectAll() {{
            selectedEventIds = [];
            renderEventSelector();
            renderStatsBar();
            renderInsightPanel();
            renderChart();
        }}

        // 选中TOP10
        function selectTop10() {{
            // 按热度排序，取前10个
            const top10Events = [...allEvents]
                .sort((a, b) => b.hot_value - a.hot_value)
                .slice(0, 10)
                .map(e => e.id);

            selectedEventIds = top10Events;
            currentSort = 'hot';
            renderEventSelector();
            renderStatsBar();
            renderInsightPanel();
            renderChart();
        }}

        // 按热度排序
        function sortByHot() {{
            currentSort = 'hot';
            renderEventSelector();
            renderChart();
        }}

        // 按评论数排序
        function sortByComments() {{
            currentSort = 'comments';
            renderEventSelector();
            renderChart();
        }}

        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>'''

    return html_content


def _get_dashboard_data(conn) -> Dict[str, Any]:
    """获取统一仪表板所需的所有数据"""
    data = {
        'wordcloud': {},
        'hot_trend': {'hours': [], 'hot_values': [], 'event_counts': [], 'all_dates': [], 'all_data': {}, 'current_date': ''},
        'sentiment_pie': {'positive': 0, 'negative': 0, 'neutral': 0},
        'top10_bar': {'titles': [], 'hot_values': [], 'sources': [], 'dates': []},
        'events_3d': [],
        'events_list': []
    }

    cursor = None
    try:
        cursor = conn.cursor()

        # 1. 获取词云数据（所有事件）
        if JIEBA_AVAILABLE:
            print("   正在获取所有事件的词云数据...")
            data['wordcloud'] = get_all_events_wordcloud_data(conn)
            print(f"   词云数据: {len(data['wordcloud'])} 个事件（包含全部事件）")
        else:
            print("   ⚠️ jieba未安装，跳过词云数据")

        # 2. 获取热度趋势数据（所有历史日期，按日期分组）
        print("   正在获取历史热度趋势数据...")
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                HOUR(created_at) as hour, 
                SUM(hot_value) as total_hot_value, 
                COUNT(*) as event_count 
            FROM hot_events 
            GROUP BY DATE(created_at), HOUR(created_at) 
            ORDER BY date, hour
        """)
        results = cursor.fetchall()

        # 按日期分组存储
        hot_trend_by_date = {}
        available_dates = set()
        for row in results:
            date_str = str(row['date'])
            available_dates.add(date_str)
            if date_str not in hot_trend_by_date:
                hot_trend_by_date[date_str] = {'hours': [], 'hot_values': [], 'event_counts': []}
            hot_trend_by_date[date_str]['hours'].append(f"{int(row['hour'])}:00")
            hot_trend_by_date[date_str]['hot_values'].append(float(row['total_hot_value'] or 0))
            hot_trend_by_date[date_str]['event_counts'].append(int(row['event_count'] or 0))

        # 默认使用最近有数据的日期
        default_date = max(available_dates) if available_dates else None
        if default_date and default_date in hot_trend_by_date:
            default_data = hot_trend_by_date[default_date]
            data['hot_trend']['hours'] = default_data['hours']
            data['hot_trend']['hot_values'] = default_data['hot_values']
            data['hot_trend']['event_counts'] = default_data['event_counts']
            data['hot_trend']['all_dates'] = sorted(list(available_dates))
            data['hot_trend']['all_data'] = hot_trend_by_date
            data['hot_trend']['current_date'] = default_date
            print(f"   历史热度数据: {len(available_dates)} 个日期，默认显示 {default_date}")
        else:
            print("   ⚠️ 没有历史热度数据")

        # 3. 获取情感分布数据
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive,
                COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative,
                COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutral
            FROM comments
            WHERE sentiment_label IS NOT NULL
        """)
        result = cursor.fetchone()
        if result:
            data['sentiment_pie']['positive'] = int(result['positive'] or 0)
            data['sentiment_pie']['negative'] = int(result['negative'] or 0)
            data['sentiment_pie']['neutral'] = int(result['neutral'] or 0)

        # 4. 获取TOP10数据
        cursor.execute("""
            SELECT title, hot_value, source, crawl_date
            FROM hot_events
            WHERE crawl_date = CURDATE()
            ORDER BY hot_value DESC
            LIMIT 10
        """)
        results = cursor.fetchall()
        if not results:
            cursor.execute("""
                SELECT title, hot_value, source, crawl_date
                FROM hot_events
                ORDER BY hot_value DESC
                LIMIT 10
            """)
            results = cursor.fetchall()

        for row in results:
            title = row['title'][:20] + "..." if len(row['title']) > 20 else row['title']
            data['top10_bar']['titles'].append(title)
            data['top10_bar']['hot_values'].append(float(row['hot_value']))
            data['top10_bar']['sources'].append(row['source'])
            data['top10_bar']['dates'].append(str(row['crawl_date']))

        # 5. 获取3D分析数据
        print("   正在获取三维分析数据...")
        cursor.execute("""
            SELECT COUNT(*) as table_exists
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = 'sentiment_results'
        """)
        has_sentiment_table = cursor.fetchone()['table_exists'] > 0
        print(f"   sentiment_results表: {'存在' if has_sentiment_table else '不存在，使用comments表'}")

        if has_sentiment_table:
            # 先检查sentiment_results表是否有数据
            cursor.execute("SELECT COUNT(*) as cnt FROM sentiment_results")
            sentiment_count = cursor.fetchone()['cnt']
            print(f"   sentiment_results表数据量: {sentiment_count}")
            
            if sentiment_count > 0:
                cursor.execute("""
                    SELECT 
                        e.id, e.title, e.hot_value,
                        s.positive_count, s.negative_count, s.neutral_count, s.total_count as comment_count,
                        CASE WHEN s.total_count > 0 THEN s.positive_count * 100.0 / s.total_count ELSE 0 END as positive_ratio,
                        CASE WHEN s.total_count > 0 THEN s.negative_count * 100.0 / s.total_count ELSE 0 END as negative_ratio,
                        CASE WHEN s.total_count > 0 THEN s.neutral_count * 100.0 / s.total_count ELSE 0 END as neutral_ratio
                    FROM hot_events e
                    JOIN sentiment_results s ON e.id = s.event_id
                    WHERE s.total_count >= 1
                    ORDER BY e.hot_value DESC
                    LIMIT 50
                """)
            else:
                print("   sentiment_results表为空，使用comments表")
                has_sentiment_table = False
                
        if not has_sentiment_table:
            cursor.execute("""
                SELECT 
                    e.id, e.title, e.hot_value,
                    COUNT(c.id) as comment_count,
                    COUNT(CASE WHEN c.sentiment_label = 'positive' THEN 1 END) as positive_count,
                    COUNT(CASE WHEN c.sentiment_label = 'negative' THEN 1 END) as negative_count,
                    COUNT(CASE WHEN c.sentiment_label = 'neutral' THEN 1 END) as neutral_count
                FROM hot_events e
                LEFT JOIN comments c ON e.id = c.event_id
                GROUP BY e.id, e.title, e.hot_value
                HAVING comment_count >= 1
                ORDER BY e.hot_value DESC
                LIMIT 50
            """)

        results = cursor.fetchall()
        print(f"   三维分析数据: 查询到 {len(results)} 个事件")
        for row in results:
            comment_count = int(row['comment_count'] or 0)
            positive_count = int(row.get('positive_count', 0) or 0)
            negative_count = int(row.get('negative_count', 0) or 0)
            neutral_count = int(row.get('neutral_count', 0) or 0)

            positive_ratio = 0
            negative_ratio = 0
            neutral_ratio = 0
            if comment_count > 0:
                positive_ratio = positive_count * 100.0 / comment_count
                negative_ratio = negative_count * 100.0 / comment_count
                neutral_ratio = neutral_count * 100.0 / comment_count

            dominant = get_dominant_sentiment(positive_ratio, negative_ratio, neutral_ratio)

            data['events_3d'].append({
                'id': int(row['id']),
                'title': row['title'],
                'display_title': row['title'][:8] + "..." if len(row['title']) > 8 else row['title'],
                'hot_value': float(row['hot_value'] or 0),
                'formatted_hot': format_hot_value(float(row['hot_value'] or 0)),
                'comment_count': comment_count,
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'neutral_ratio': neutral_ratio,
                'dominant': dominant
            })

        # 6. 获取事件列表（用于词云图选择）
        cursor.execute("""
            SELECT 
                e.id, e.title, e.hot_value, COUNT(c.id) as comment_count
            FROM hot_events e
            LEFT JOIN comments c ON e.id = c.event_id
            GROUP BY e.id, e.title, e.hot_value
            HAVING COUNT(c.id) > 0
            ORDER BY e.hot_value DESC
            LIMIT 100
        """)
        events_list = cursor.fetchall()
        print(f"   事件列表: 查询到 {len(events_list)} 个有评论的事件")
        for row in events_list:
            data['events_list'].append({
                'id': int(row['id']),
                'title': row['title'],
                'hot_value': float(row['hot_value'] or 0),
                'formatted_hot': format_hot_value(float(row['hot_value'] or 0)),
                'comment_count': int(row['comment_count'] or 0)
            })

        print(f"   仪表板数据汇总: 词云{len(data['wordcloud'])}个, 趋势{len(data['hot_trend']['hours'])}小时, "
              f"情感{sum(data['sentiment_pie'].values())}条, TOP10{len(data['top10_bar']['titles'])}个, "
              f"3D分析{len(data['events_3d'])}个")
        return data

    except Exception as e:
        logger.error(f"获取仪表板数据失败: {e}")
        return data
    finally:
        if cursor:
            cursor.close()


def generate_charts_viewer(conn) -> Optional[str]:
    """
    生成统一仪表板HTML页面（单文件包含所有图表）

    Args:
        conn: 数据库连接对象

    Returns:
        Optional[str]: 生成的HTML文件路径
    """
    output_dir = ensure_charts_dir()
    viewer_path = os.path.join(output_dir, "index.html")

    try:
        # 获取所有数据
        print("   正在查询数据库获取所有图表数据...")
        data = _get_dashboard_data(conn)

        # 序列化数据为JSON
        wordcloud_data_json = json.dumps(data['wordcloud'], ensure_ascii=False)
        hot_trend_json = json.dumps(data['hot_trend'], ensure_ascii=False)
        sentiment_pie_json = json.dumps(data['sentiment_pie'], ensure_ascii=False)
        top10_bar_json = json.dumps(data['top10_bar'], ensure_ascii=False)
        events_3d_json = json.dumps(data['events_3d'], ensure_ascii=False)
        events_list_json = json.dumps(data['events_list'], ensure_ascii=False)

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 计算统计数据
        has_wordcloud = len(data['wordcloud']) > 0
        has_hot_trend = len(data['hot_trend']['hours']) >= 2
        has_sentiment = (data['sentiment_pie']['positive'] + data['sentiment_pie']['negative'] +
                        data['sentiment_pie']['neutral']) > 0
        has_top10 = len(data['top10_bar']['titles']) > 0
        has_3d = len(data['events_3d']) >= 2

        available_count = sum([has_wordcloud, has_hot_trend, has_sentiment, has_top10, has_3d])

        # 创建HTML内容 - 单文件包含所有图表
        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>社交媒体热点分析系统 - 统一仪表板 v{current_time}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts-wordcloud@2.1.0/dist/echarts-wordcloud.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            background: #ffffff;
            color: #333;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}

        /* 头部 */
        .header {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid #f0f0f0;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; color: #1a1a1a; }}
        .subtitle {{ color: #666; font-size: 14px; margin-bottom: 20px; }}

        /* 统计栏 */
        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #fafafa;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            border: 1px solid #f0f0f0;
        }}
        .stat-value {{ font-size: 24px; font-weight: 700; color: #1890ff; }}
        .stat-label {{ font-size: 12px; color: #666; margin-top: 4px; }}

        /* 导航标签 */
        .nav-tabs {{
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .nav-tab {{
            padding: 10px 20px;
            background: white;
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .nav-tab:hover {{ border-color: #1890ff; color: #1890ff; }}
        .nav-tab.active {{
            background: #1890ff;
            color: white;
            border-color: #1890ff;
        }}

        /* 内容区域 */
        .content-area {{ display: none; }}
        .content-area.active {{ display: block; }}

        /* 图表卡片 */
        .chart-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid #f0f0f0;
        }}
        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .chart-title {{ font-size: 18px; font-weight: 600; }}
        .chart-container {{ width: 100%; height: 500px; }}

        /* 词云图事件选择器 */
        .event-selector {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 10px;
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 15px;
            padding: 5px;
        }}
        .event-card {{
            background: #fafafa;
            border: 2px solid #e8e8e8;
            border-radius: 8px;
            padding: 10px 12px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 13px;
        }}
        .event-card:hover {{ border-color: #1890ff; }}
        .event-card.selected {{
            border-color: #1890ff;
            background: #f0f7ff;
        }}
        .event-card .event-title {{ font-weight: 600; margin-bottom: 4px; }}
        .event-card .event-stats {{ color: #666; font-size: 12px; }}
        .search-box {{
            width: 100%;
            padding: 10px 14px;
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 14px;
        }}
        .search-box:focus {{ outline: none; border-color: #1890ff; }}

        /* 3D分析事件卡片 */
        .event-selector-3d {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 10px;
            max-height: 350px;
            overflow-y: auto;
            margin-bottom: 15px;
            padding: 5px;
        }}
        .event-card-3d {{
            background: white;
            border: 2px solid #e8e8e8;
            border-radius: 8px;
            padding: 12px;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
        }}
        .event-card-3d:hover {{ border-color: #1890ff; box-shadow: 0 2px 8px rgba(24,144,255,0.1); }}
        .event-card-3d.selected {{
            border-color: #1890ff;
            background: #f0f7ff;
        }}
        .event-card-3d.positive {{ border-left: 4px solid #52c41a; }}
        .event-card-3d.negative {{ border-left: 4px solid #ff4d4f; }}
        .event-card-3d.neutral {{ border-left: 4px solid #faad14; }}
        .checkbox {{
            position: absolute;
            top: 10px;
            right: 10px;
            width: 18px;
            height: 18px;
            border: 2px solid #d9d9d9;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
        }}
        .checkbox.checked {{ background: #1890ff; border-color: #1890ff; color: white; }}

        /* 控制按钮 */
        .control-btns {{
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }}
        .ctrl-btn {{
            padding: 6px 14px;
            background: white;
            border: 1px solid #e8e8e8;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
        }}
        .ctrl-btn:hover {{ background: #f5f5f5; }}
        .ctrl-btn.primary {{ background: #1890ff; color: white; border-color: #1890ff; }}
        .ctrl-btn.primary:hover {{ background: #40a9ff; }}

        /* 洞察面板 */
        .insight-panel {{
            background: #f6ffed;
            border: 1px solid #b7eb8f;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            font-size: 14px;
        }}

        /* 底部 */
        .footer {{
            text-align: center;
            color: #999;
            font-size: 13px;
            margin-top: 30px;
            padding: 20px;
        }}

        /* AI聊天面板 */
        .ai-chat-panel {{
            position: fixed;
            bottom: 80px;
            right: 20px;
            width: 450px;
            height: 600px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.15);
            display: none;
            flex-direction: column;
            z-index: 1000;
            border: 1px solid #e8e8e8;
            overflow: hidden;
        }}
        .ai-chat-panel.active {{
            display: flex;
        }}
        .ai-chat-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            font-size: 16px;
        }}
        .ai-chat-close {{
            background: none;
            border: none;
            color: white;
            font-size: 18px;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.2s;
        }}
        .ai-chat-close:hover {{
            background: rgba(255,255,255,0.2);
        }}
        .ai-chat-context {{
            background: #f8f9fa;
            padding: 10px 15px;
            border-bottom: 1px solid #e8e8e8;
            font-size: 12px;
            color: #666;
        }}
        .ai-context-info {{
            margin-bottom: 4px;
        }}
        .ai-context-info span {{
            color: #1890ff;
            font-weight: 600;
        }}
        .ai-chat-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .ai-message {{
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.6;
            word-wrap: break-word;
        }}
        .ai-message.user {{
            align-self: flex-end;
            background: #1890ff;
            color: white;
            border-bottom-right-radius: 4px;
        }}
        .ai-message.ai {{
            align-self: flex-start;
            background: #f0f0f0;
            color: #333;
            border-bottom-left-radius: 4px;
        }}
        .ai-message.loading {{
            align-self: flex-start;
            background: #f0f0f0;
            color: #666;
            font-style: italic;
        }}
        .ai-message.error {{
            align-self: flex-start;
            background: #fff2f0;
            color: #ff4d4f;
            border: 1px solid #ffccc7;
        }}
        .ai-chat-input-area {{
            padding: 15px;
            border-top: 1px solid #e8e8e8;
            display: flex;
            gap: 10px;
        }}
        .ai-chat-input {{
            flex: 1;
            padding: 10px 14px;
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
        }}
        .ai-chat-input:focus {{
            border-color: #1890ff;
        }}
        .ai-chat-send {{
            padding: 10px 20px;
            background: #1890ff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }}
        .ai-chat-send:hover {{
            background: #40a9ff;
        }}
        .ai-chat-toggle {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            z-index: 999;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .ai-chat-toggle:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        }}
        .ai-btn {{
            padding: 6px 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            margin-left: 10px;
            transition: opacity 0.2s;
        }}
        .ai-btn:hover {{
            opacity: 0.9;
        }}
        @media (max-width: 768px) {{
            .chart-container {{ height: 350px; }}
            .event-selector {{ grid-template-columns: 1fr; }}
            .nav-tabs {{ flex-direction: column; }}
            .ai-chat-panel {{
                width: calc(100% - 40px);
                height: calc(100% - 120px);
                bottom: 80px;
                right: 20px;
                left: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 社交媒体热点话题分析系统</h1>
            <p class="subtitle">统一仪表板 v5.0 | 数据更新时间: {current_time}</p>
            <p class="subtitle" style="color: #1890ff; font-weight: 600;">✨ 新功能: 历史趋势支持选择任意日期 | 词云图支持所有事件切换</p>
            <div class="stats-bar">
                <div class="stat-card">
                    <div class="stat-value">{len(data['events_list'])}</div>
                    <div class="stat-label">热点事件</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{available_count}</div>
                    <div class="stat-label">可用图表</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(data['events_3d'])}</div>
                    <div class="stat-label">可分析事件</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{sum(data['sentiment_pie'].values())}</div>
                    <div class="stat-label">已分析评论</div>
                </div>
            </div>
            <div class="nav-tabs">
                <button class="nav-tab active" onclick="showTab('wordcloud')">☁️ 词云图</button>
                <button class="nav-tab" onclick="showTab('hot_trend')">📈 历史趋势</button>
                <button class="nav-tab" onclick="showTab('sentiment_pie')">🥧 情感分布</button>
                <button class="nav-tab" onclick="showTab('top10_bar')">📊 TOP10榜单</button>
                <button class="nav-tab" onclick="showTab('interactive_3d')">🔗 三维分析</button>
            </div>
        </div>

        <!-- 词云图 -->
        <div class="content-area active" id="tab-wordcloud">
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">☁️ 热点话题词云图</span>
                    <button class="ai-btn" onclick="toggleAIChat(); updateAIContext('词云图', aiCurrentEventTitle || '全部事件');">🤖 AI分析</button>
                </div>
                <input type="text" class="search-box" id="wordcloudSearch" placeholder="搜索事件..." oninput="filterWordcloudEvents()">
                <div class="control-btns">
                    <button class="ctrl-btn primary" onclick="showAllWordcloud()">全部事件</button>
                    <button class="ctrl-btn" onclick="sortWordcloudEvents('hot')">按热度排序</button>
                    <button class="ctrl-btn" onclick="sortWordcloudEvents('comments')">按评论数排序</button>
                </div>
                <div class="event-selector" id="wordcloudEvents"></div>
                <div class="chart-container" id="wordcloudChart"></div>
            </div>
        </div>

        <!-- 热度趋势 -->
        <div class="content-area" id="tab-hot_trend">
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">📈 历史热点总热度趋势</span>
                </div>
                <div style="margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
                    <label style="font-size: 14px; color: #666;">选择日期:</label>
                    <select id="dateSelector" class="search-box" style="width: auto; min-width: 150px;" onchange="changeDate()">
                        <!-- 日期选项将通过JS动态生成 -->
                    </select>
                    <span id="currentDateDisplay" style="font-size: 14px; color: #1890ff; font-weight: 600;"></span>
                </div>
                <div class="chart-container" id="hotTrendChart"></div>
            </div>
        </div>

        <!-- 情感分布 -->
        <div class="content-area" id="tab-sentiment_pie">
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">🥧 基于规则和词典的匹配算法分类</span>
                </div>
                <div class="chart-container" id="sentimentPieChart"></div>
            </div>
        </div>

        <!-- TOP10 -->
        <div class="content-area" id="tab-top10_bar">
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">📊 TOP10热点事件</span>
                </div>
                <div class="chart-container" id="top10BarChart"></div>
            </div>
        </div>

        <!-- 三维分析 -->
        <div class="content-area" id="tab-interactive_3d">
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">🔗 热度-传播-情感三维关联分析</span>
                    <button class="ai-btn" onclick="toggleAIChat(); updateAIContext('三维分析', '已选' + aiSelectedEvents.length + '个事件');">🤖 AI分析</button>
                </div>
                <div class="control-btns">
                    <button class="ctrl-btn primary" onclick="selectAll3D()">全选</button>
                    <button class="ctrl-btn" onclick="deselectAll3D()">取消全选</button>
                    <button class="ctrl-btn" onclick="selectTop10_3D()">选中TOP10</button>
                    <button class="ctrl-btn" onclick="sort3DEvents('hot')">按热度排序</button>
                    <button class="ctrl-btn" onclick="sort3DEvents('comments')">按评论数排序</button>
                </div>
                <div class="event-selector-3d" id="events3D"></div>
                <div class="insight-panel" id="insightPanel"></div>
                <div class="chart-container" id="chart3D"></div>
            </div>
        </div>

        <div class="footer">
            <p>© 2026 社交媒体热点话题分析系统 | 统一仪表板 v5.0 (历史趋势版)</p>
            <p>所有图表集成于单一HTML文件 | 生成时间: {current_time} | 支持历史日期选择</p>
        </div>
    </div>

    <!-- AI聊天界面 -->
    <div class="ai-chat-panel" id="aiChatPanel">
        <div class="ai-chat-header">
            <span>🤖 千问AI智能分析</span>
            <button class="ai-chat-close" onclick="toggleAIChat()">✕</button>
        </div>
        <div class="ai-chat-context" id="aiChatContext">
            <div class="ai-context-info">💡 当前分析模块：<span id="aiCurrentModule">未选择</span></div>
            <div class="ai-context-info">📊 选中数据：<span id="aiCurrentData">无</span></div>
        </div>
        <div class="ai-chat-messages" id="aiChatMessages"></div>
        <div class="ai-chat-input-area">
            <input type="text" class="ai-chat-input" id="aiChatInput" placeholder="输入问题，AI将基于图表数据回答..." onkeypress="if(event.key==='Enter')sendAIQuestion()">
            <button class="ai-chat-send" onclick="sendAIQuestion()">发送</button>
        </div>
    </div>
    <button class="ai-chat-toggle" id="aiChatToggle" onclick="toggleAIChat()">🤖 AI分析</button>

    <script>
        // ==================== 数据 ====================
        const wordcloudData = {wordcloud_data_json};
        const hotTrendData = {hot_trend_json};
        const sentimentPieData = {sentiment_pie_json};
        const top10BarData = {top10_bar_json};
        const events3D = {events_3d_json};
        const eventsList = {events_list_json};

        // ==================== 标签页切换 ====================
        function showTab(tabName) {{
            document.querySelectorAll('.content-area').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tabName).classList.add('active');
            event.target.classList.add('active');

            // 初始化对应图表
            if (tabName === 'wordcloud') initWordcloud();
            if (tabName === 'hot_trend') initHotTrend();
            if (tabName === 'sentiment_pie') initSentimentPie();
            if (tabName === 'top10_bar') initTop10Bar();
            if (tabName === 'interactive_3d') init3DChart();
        }}

        // ==================== 词云图 ====================
        let currentWordcloudEvent = 0;
        let wordcloudSort = 'hot';

        function renderWordcloudEvents() {{
            const container = document.getElementById('wordcloudEvents');
            const searchTerm = document.getElementById('wordcloudSearch').value.toLowerCase();
            let events = [...eventsList];

            if (searchTerm) {{
                events = events.filter(e => e.title.toLowerCase().includes(searchTerm));
            }}

            if (wordcloudSort === 'hot') {{
                events.sort((a, b) => b.hot_value - a.hot_value);
            }} else {{
                events.sort((a, b) => b.comment_count - a.comment_count);
            }}

            container.innerHTML = '';
            events.forEach(event => {{
                const hasData = wordcloudData[event.id] && wordcloudData[event.id].length > 0;
                const card = document.createElement('div');
                card.className = `event-card ${{currentWordcloudEvent === event.id ? 'selected' : ''}} ${{!hasData ? '' : ''}}`;
                card.style.opacity = hasData ? '1' : '0.5';
                card.onclick = () => {{ if (hasData) switchWordcloudEvent(event.id); }};
                card.innerHTML = `
                    <div class="event-title">${{event.title}}</div>
                    <div class="event-stats">
                        🔥 ${{event.formatted_hot}} | 💬 ${{event.comment_count}}` +
                        (hasData ? '' : ' | ⚠️ 无词云数据') + `
                    </div>
                `;
                container.appendChild(card);
            }});
        }}

        function switchWordcloudEvent(eventId) {{
            currentWordcloudEvent = eventId;
            aiCurrentEventId = eventId;
            const event = eventsList.find(e => e.id === eventId);
            aiCurrentEventTitle = event ? event.title : '全部事件';
            updateAIContext('词云图', aiCurrentEventTitle);
            renderWordcloudEvents();
            renderWordcloud();
        }}

        function showAllWordcloud() {{
            currentWordcloudEvent = 0;
            document.getElementById('wordcloudSearch').value = '';
            renderWordcloudEvents();
            renderWordcloud();
        }}

        function filterWordcloudEvents() {{
            renderWordcloudEvents();
        }}

        function sortWordcloudEvents(sortType) {{
            wordcloudSort = sortType;
            renderWordcloudEvents();
        }}

        function renderWordcloud() {{
            const chartDom = document.getElementById('wordcloudChart');
            const chart = echarts.init(chartDom);
            const data = wordcloudData[currentWordcloudEvent] || [];

            const eventInfo = currentWordcloudEvent === 0
                ? '全部事件'
                : (eventsList.find(e => e.id === currentWordcloudEvent)?.title || '未知事件');

            chart.setOption({{
                title: {{
                    text: '词云图 - ' + eventInfo,
                    left: 'center',
                    textStyle: {{ fontSize: 18 }}
                }},
                tooltip: {{
                    show: true,
                    formatter: function(p) {{ return p.name + ': ' + p.value + '次'; }}
                }},
                series: [{{
                    type: 'wordCloud',
                    shape: 'circle',
                    left: 'center',
                    top: 'center',
                    width: '90%',
                    height: '90%',
                    right: null,
                    bottom: null,
                    sizeRange: [12, 100],
                    rotationRange: [-45, 45],
                    rotationStep: 45,
                    gridSize: 8,
                    drawOutOfBound: false,
                    textStyle: {{
                        fontFamily: 'Microsoft YaHei',
                        fontWeight: 'bold',
                        color: function() {{
                            return 'rgb(' + [
                                Math.round(Math.random() * 160 + 50),
                                Math.round(Math.random() * 160 + 50),
                                Math.round(Math.random() * 160 + 50)
                            ].join(',') + ')';
                        }}
                    }},
                    emphasis: {{
                        focus: 'self',
                        textStyle: {{ textShadowBlur: 10, textShadowColor: '#333' }}
                    }},
                    data: data.map(item => ({{ name: item[0], value: item[1] }}))
                }}]
            }});
        }}

        function initWordcloud() {{
            renderWordcloudEvents();
            renderWordcloud();
        }}

        // ==================== 热度趋势 ====================
        let currentHotTrendDate = hotTrendData.current_date || '';
        let hotTrendChart = null;

        function initDateSelector() {{
            const selector = document.getElementById('dateSelector');
            const display = document.getElementById('currentDateDisplay');

            if (!hotTrendData.all_dates || hotTrendData.all_dates.length === 0) {{
                selector.innerHTML = '<option>无可用日期</option>';
                display.textContent = '';
                return;
            }}

            selector.innerHTML = '';
            hotTrendData.all_dates.forEach(date => {{
                const option = document.createElement('option');
                option.value = date;
                option.textContent = date;
                if (date === currentHotTrendDate) {{
                    option.selected = true;
                }}
                selector.appendChild(option);
            }});

            display.textContent = '当前: ' + currentHotTrendDate;
        }}

        function changeDate() {{
            const selector = document.getElementById('dateSelector');
            const selectedDate = selector.value;
            const display = document.getElementById('currentDateDisplay');

            if (selectedDate && hotTrendData.all_data && hotTrendData.all_data[selectedDate]) {{
                currentHotTrendDate = selectedDate;
                display.textContent = '当前: ' + selectedDate;

                const dateData = hotTrendData.all_data[selectedDate];
                renderHotTrendChart(dateData.hours, dateData.hot_values, dateData.event_counts, selectedDate);
            }}
        }}

        function renderHotTrendChart(hours, hotValues, eventCounts, dateStr) {{
            if (!hotTrendChart) {{
                hotTrendChart = echarts.init(document.getElementById('hotTrendChart'));
            }}

            hotTrendChart.setOption({{
                title: {{
                    text: '历史热点总热度趋势',
                    subtext: '日期: ' + dateStr,
                    left: 'center'
                }},
                tooltip: {{
                    trigger: 'axis',
                    axisPointer: {{ type: 'cross' }}
                }},
                legend: {{ data: ['总热度值', '事件数'], top: 40 }},
                grid: {{ left: '3%', right: '4%', bottom: '10%', top: '20%', containLabel: true }},
                xAxis: {{
                    type: 'category',
                    data: hours,
                    axisLabel: {{ rotate: 45 }}
                }},
                yAxis: [
                    {{ type: 'value', name: '总热度值', position: 'left' }},
                    {{ type: 'value', name: '事件数', position: 'right' }}
                ],
                series: [
                    {{
                        name: '总热度值',
                        type: 'line',
                        data: hotValues,
                        smooth: true,
                        yAxisIndex: 0,
                        lineStyle: {{ width: 3, color: '#5470c6' }},
                        itemStyle: {{ color: '#5470c6' }},
                        areaStyle: {{ opacity: 0.1, color: '#5470c6' }}
                    }},
                    {{
                        name: '事件数',
                        type: 'line',
                        data: eventCounts,
                        smooth: true,
                        yAxisIndex: 1,
                        lineStyle: {{ width: 2, type: 'dashed', color: '#91cc75' }},
                        itemStyle: {{ color: '#91cc75' }}
                    }}
                ],
                dataZoom: [{{ type: 'inside' }}, {{ type: 'slider', bottom: 0 }}]
            }}, true);
        }}

        function initHotTrend() {{
            initDateSelector();
            renderHotTrendChart(
                hotTrendData.hours,
                hotTrendData.hot_values,
                hotTrendData.event_counts,
                currentHotTrendDate
            );
        }}

        // ==================== 情感分布 ====================
        function initSentimentPie() {{
            const chart = echarts.init(document.getElementById('sentimentPieChart'));
            const data = [
                {{ value: sentimentPieData.positive, name: '正面' }},
                {{ value: sentimentPieData.negative, name: '负面' }},
                {{ value: sentimentPieData.neutral, name: '中性' }}
            ].filter(item => item.value > 0);

            const total = sentimentPieData.positive + sentimentPieData.negative + sentimentPieData.neutral;

            chart.setOption({{
                title: {{
                    text: '基于规则和词典的匹配算法分类',
                    subtext: '总评论数: ' + total,
                    left: 'center'
                }},
                tooltip: {{
                    trigger: 'item',
                    formatter: '{{b}}: {{c}} ({{d}}%)'
                }},
                legend: {{
                    orient: 'vertical',
                    left: 'left',
                    top: 'center'
                }},
                series: [{{
                    name: '情感分布',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    center: ['60%', '50%'],
                    roseType: 'radius',
                    itemStyle: {{ borderRadius: 5 }},
                    label: {{ formatter: '{{b}}: {{c}} ({{d}}%)' }},
                    data: data,
                    color: ['#91cc75', '#ee6666', '#fac858']
                }}]
            }});
        }}

        // ==================== TOP10 ====================
        function initTop10Bar() {{
            const chart = echarts.init(document.getElementById('top10BarChart'));
            chart.setOption({{
                title: {{ text: 'TOP10热点事件', left: 'center' }},
                tooltip: {{
                    trigger: 'axis',
                    formatter: function(params) {{
                        const idx = params[0].dataIndex;
                        return '标题: ' + top10BarData.titles[idx] + '<br/>' +
                               '热度: ' + params[0].value + '<br/>' +
                               '来源: ' + top10BarData.sources[idx] + '<br/>' +
                               '日期: ' + top10BarData.dates[idx];
                    }}
                }},
                grid: {{ left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true }},
                xAxis: {{ type: 'value', name: '热度值' }},
                yAxis: {{
                    type: 'category',
                    data: top10BarData.titles.slice().reverse(),
                    axisLabel: {{ fontSize: 11 }}
                }},
                series: [{{
                    name: '热度值',
                    type: 'bar',
                    data: top10BarData.hot_values.slice().reverse(),
                    itemStyle: {{ color: '#5470c6', borderRadius: [0, 4, 4, 0] }},
                    label: {{
                        show: true,
                        position: 'right',
                        formatter: '{{c}}'
                    }}
                }}]
            }});
        }}

        // ==================== 三维分析 ====================
        let selected3DEventIds = [];
        let sort3D = 'hot';
        let chart3DInstance = null;

        function render3DEvents() {{
            const container = document.getElementById('events3D');
            let events = [...events3D];

            if (sort3D === 'hot') {{
                events.sort((a, b) => b.hot_value - a.hot_value);
            }} else {{
                events.sort((a, b) => b.comment_count - a.comment_count);
            }}

            container.innerHTML = '';
            events.forEach(event => {{
                const isSelected = selected3DEventIds.includes(event.id);
                const card = document.createElement('div');
                card.className = `event-card-3d ${{event.dominant}} ${{isSelected ? 'selected' : ''}}`;
                card.onclick = () => toggle3DEvent(event.id);

                let sentimentLabel = event.dominant === 'positive' ? '正面'
                    : event.dominant === 'negative' ? '负面' : '中性';

                card.innerHTML = `
                    <div class="checkbox ${{isSelected ? 'checked' : ''}}">${{isSelected ? '✓' : ''}}</div>
                    <div style="font-weight:600;margin-bottom:4px;padding-right:20px;">${{event.display_title}}</div>
                    <div style="font-size:12px;color:#666;">
                        🔥 ${{event.formatted_hot}} | 💬 ${{event.comment_count}} | 📊 ${{sentimentLabel}}
                    </div>
                `;
                container.appendChild(card);
            }});
        }}

        function toggle3DEvent(eventId) {{
            const idx = selected3DEventIds.indexOf(eventId);
            if (idx === -1) {{
                selected3DEventIds.push(eventId);
            }} else {{
                selected3DEventIds.splice(idx, 1);
            }}
            aiSelectedEvents = selected3DEventIds;
            updateAIContext('三维分析', '已选' + aiSelectedEvents.length + '个事件');
            render3DEvents();
            render3DChart();
            renderInsight();
        }}

        function selectAll3D() {{
            selected3DEventIds = events3D.map(e => e.id);
            render3DEvents();
            render3DChart();
            renderInsight();
        }}

        function deselectAll3D() {{
            selected3DEventIds = [];
            render3DEvents();
            render3DChart();
            renderInsight();
        }}

        function selectTop10_3D() {{
            selected3DEventIds = events3D.slice(0, 10).map(e => e.id);
            sort3D = 'hot';
            render3DEvents();
            render3DChart();
            renderInsight();
        }}

        function sort3DEvents(sortType) {{
            sort3D = sortType;
            render3DEvents();
        }}

        function renderInsight() {{
            const panel = document.getElementById('insightPanel');
            const selected = events3D.filter(e => selected3DEventIds.includes(e.id));

            if (selected.length === 0) {{
                panel.innerHTML = '<strong>💡 智能洞察：</strong>请选择至少一个事件进行分析。';
                return;
            }}

            const maxHot = selected.reduce((m, e) => e.hot_value > m.hot_value ? e : m, selected[0]);
            const positiveCount = selected.filter(e => e.dominant === 'positive').length;
            const negativeCount = selected.filter(e => e.dominant === 'negative').length;
            const neutralCount = selected.filter(e => e.dominant === 'neutral').length;

            panel.innerHTML = `<strong>💡 智能洞察：</strong>选中 <b>${{selected.length}}</b> 个事件，` +
                `其中"<b>${{maxHot.display_title}}</b>"热度最高(${{maxHot.formatted_hot}})。` +
                `情感分布：正面<b>${{positiveCount}}</b>个、负面<b>${{negativeCount}}</b>个、中性<b>${{neutralCount}}</b>个。`;
        }}

        function render3DChart() {{
            if (!chart3DInstance) {{
                chart3DInstance = echarts.init(document.getElementById('chart3D'));
            }}
            const selected = events3D.filter(e => selected3DEventIds.includes(e.id));

            if (selected.length === 0) {{
                chart3DInstance.clear();
                return;
            }}

            let chartEvents = [...selected];
            if (sort3D === 'hot') {{
                chartEvents.sort((a, b) => b.hot_value - a.hot_value);
            }} else {{
                chartEvents.sort((a, b) => b.comment_count - a.comment_count);
            }}

            const xData = chartEvents.map(e => e.display_title + '\\n(' + e.formatted_hot + ')');
            const seriesData = chartEvents.map(e => {{
                let color = e.dominant === 'positive' ? '#52c41a'
                    : e.dominant === 'negative' ? '#ff4d4f' : '#faad14';
                return {{
                    value: e.comment_count,
                    itemStyle: {{ color: color, borderRadius: [4, 4, 0, 0] }},
                    eventData: e
                }};
            }});

            chart3DInstance.setOption({{
                title: {{ text: '热度-传播-情感三维关联分析', left: 'center' }},
                tooltip: {{
                    trigger: 'item',
                    formatter: function(params) {{
                        const d = params.data.eventData;
                        return `<div style="font-weight:bold">${{d.title}}</div>` +
                               `🔥 热度: ${{d.formatted_hot}}<br/>` +
                               `💬 评论数: ${{d.comment_count}}<br/>` +
                               `📊 正面: ${{d.positive_ratio.toFixed(1)}}% | 负面: ${{d.negative_ratio.toFixed(1)}}% | 中性: ${{d.neutral_ratio.toFixed(1)}}%`;
                    }}
                }},
                grid: {{ left: '3%', right: '4%', bottom: '10%', top: '10%', containLabel: true }},
                xAxis: {{
                    type: 'category',
                    data: xData,
                    axisLabel: {{ rotate: 45, fontSize: 11 }}
                }},
                yAxis: {{ type: 'value', name: '评论数（传播量）' }},
                series: [{{
                    type: 'bar',
                    barWidth: '60%',
                    data: seriesData,
                    label: {{ show: true, position: 'top', formatter: '{{c}}' }}
                }}],
                dataZoom: [{{ type: 'inside' }}, {{ type: 'slider', bottom: 0, height: 20 }}]
            }}, true);
        }}

        function init3DChart() {{
            console.log('初始化3D图表，事件数量:', events3D.length);
            console.log('events3D数据:', events3D);
            
            if (events3D.length === 0) {{
                document.getElementById('events3D').innerHTML = '<div style="padding:20px;color:#999;text-align:center;">暂无三维分析数据<br>可能原因：<br>1. 数据库中没有评论数据<br>2. 情感分析模块未运行（选项3）<br>3. 数据不满足分析条件<br><br>请先运行选项2爬取数据，再运行选项3进行情感分析</div>';
                document.getElementById('insightPanel').innerHTML = '<strong>💡 智能洞察：</strong>暂无数据。请先完成数据爬取和情感分析。';
                if (chart3DInstance) chart3DInstance.clear();
                return;
            }}
            
            if (selected3DEventIds.length === 0) {{
                selected3DEventIds = events3D.slice(0, 10).map(e => e.id);
                console.log('自动选中前10个事件:', selected3DEventIds);
            }}
            render3DEvents();
            render3DChart();
            renderInsight();
        }}

        // ==================== 初始化 ====================
        window.addEventListener('resize', function() {{
            ['wordcloudChart', 'hotTrendChart', 'sentimentPieChart', 'top10BarChart', 'chart3D'].forEach(id => {{
                const chart = echarts.getInstanceByDom(document.getElementById(id));
                if (chart) chart.resize();
            }});
        }});

        // ==================== AI聊天功能 ====================
        let aiChatOpen = false;
        let aiCurrentModule = '';
        let aiCurrentEventId = null;
        let aiCurrentEventTitle = '';
        let aiSelectedEvents = [];
        // AI服务器地址配置
        // 生产环境: 使用Render部署的地址 (部署后修改为实际地址)
        // 本地开发: http://localhost:5000
        const AI_SERVER_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:5000'
            : 'https://social-media-ai-server.onrender.com';  // 请修改为你的Render服务地址

        function toggleAIChat() {{
            const panel = document.getElementById('aiChatPanel');
            aiChatOpen = !aiChatOpen;
            panel.classList.toggle('active', aiChatOpen);
        }}

        function updateAIContext(module, data) {{
            aiCurrentModule = module;
            document.getElementById('aiCurrentModule').textContent = module;
            document.getElementById('aiCurrentData').textContent = data;
        }}

        function addAIMessage(content, type) {{
            const container = document.getElementById('aiChatMessages');
            const msg = document.createElement('div');
            msg.className = 'ai-message ' + type;
            msg.innerHTML = content;
            container.appendChild(msg);
            container.scrollTop = container.scrollHeight;
        }}

        async function sendAIQuestion() {{
            const input = document.getElementById('aiChatInput');
            const question = input.value.trim();
            if (!question) return;

            input.value = '';
            addAIMessage(question, 'user');
            addAIMessage('正在分析数据并生成回复...', 'loading');

            try {{
                let response;
                if (aiCurrentModule === '词云图' && aiCurrentEventId !== null) {{
                    const currentWordcloud = wordcloudData[aiCurrentEventId] || [];
                    response = await fetch(AI_SERVER_URL + '/api/ai/analyze-wordcloud', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            event_id: aiCurrentEventId,
                            event_title: aiCurrentEventTitle,
                            wordcloud_data: currentWordcloud,
                            question: question
                        }})
                    }});
                }} else if (aiCurrentModule === '三维分析' && aiSelectedEvents.length > 0) {{
                    const selectedData = events3D.filter(e => aiSelectedEvents.includes(e.id));
                    response = await fetch(AI_SERVER_URL + '/api/ai/analyze-3d', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            selected_events: selectedData,
                            question: question
                        }})
                    }});
                }} else {{
                    response = await fetch(AI_SERVER_URL + '/api/ai/chat', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            question: question,
                            context: '当前在' + aiCurrentModule + '模块'
                        }})
                    }});
                }}

                const result = await response.json();

                const loadingMsgs = document.querySelectorAll('.ai-message.loading');
                loadingMsgs.forEach(msg => msg.remove());

                if (result.success) {{
                    addAIMessage(result.answer, 'ai');
                }} else {{
                    addAIMessage('抱歉，分析失败：' + (result.error || '未知错误'), 'error');
                }}
            }} catch (error) {{
                const loadingMsgs = document.querySelectorAll('.ai-message.loading');
                loadingMsgs.forEach(msg => msg.remove());
                const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
                if (isLocal) {{
                    addAIMessage('网络错误，请确保AI服务已启动（运行 ai_server.py）', 'error');
                }} else {{
                    addAIMessage('网络错误，无法连接到AI服务。请检查网络连接或稍后再试。', 'error');
                }}
            }}
        }}

        // 默认显示词云图
        document.addEventListener('DOMContentLoaded', function() {{
            initWordcloud();
        }});
    </script>
</body>
</html>'''

        # 保存HTML文件
        with open(viewer_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"统一仪表板已保存: {viewer_path}")
        return viewer_path

    except Exception as e:
        logger.error(f"生成统一仪表板失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_all_charts(conn) -> Dict[str, Any]:
    """
    一键生成所有图表，包括集成查看器

    Args:
        conn: 数据库连接对象

    Returns:
        Dict[str, Any]: 生成结果统计
    """
    if not PYECHARTS_AVAILABLE or not JIEBA_AVAILABLE:
        logger.error("缺少必要依赖库")
        return {"success": False, "error": "缺少必要依赖库"}

    print("🎨 开始生成所有图表（交互式三维分析版）...")
    print("=" * 60)

    start_time = time.time()
    results = {
        "wordcloud": None,
        "hot_trend": None,
        "sentiment_pie": None,
        "top10_bar": None,
        "interactive_3d": None,
        "viewer": None
    }

    try:
        # 1. 生成词云图（带事件搜索功能）
        print("1. 正在生成词云图...")
        results["wordcloud"] = generate_wordcloud_with_search(conn)

        # 2. 生成热度趋势图
        print("2. 正在生成热度趋势图...")
        results["hot_trend"] = generate_hot_trend(conn)

        # 3. 生成情感分布饼图
        print("3. 正在生成情感分布饼图...")
        results["sentiment_pie"] = generate_sentiment_pie(conn)

        # 4. 生成TOP10柱状图
        print("4. 正在生成TOP10柱状图...")
        results["top10_bar"] = generate_top10_bar(conn)

        # 5. 生成交互式三维关联分析图
        print("5. 正在生成交互式三维关联分析图...")
        print("   （自动检测数据源，支持备选方案）")
        results["interactive_3d"] = generate_interactive_3d_chart(conn)

        # 6. 生成统一仪表板（单HTML文件包含所有图表）
        print("6. 正在生成统一仪表板（单HTML文件）...")
        results["viewer"] = generate_charts_viewer(conn)

        # 统计结果
        elapsed_time = time.time() - start_time
        success_count = sum(1 for path in results.values() if path is not None)

        print("\n" + "=" * 60)
        print("📊 图表生成完成总结")
        print("=" * 60)
        print(f"⏱️ 总耗时: {elapsed_time:.1f}秒")
        print(f"✅ 成功生成: {success_count}/6 个组件")
        print("🎯 功能亮点:")
        print("  1. ✅ 统一仪表板：单HTML文件包含所有5个图表功能")
        print("  2. ✅ 词云图：支持所有事件动态切换，词大小按比例缩放")
        print("  3. ✅ 历史热度趋势图：支持选择任意日期查看")
        print("  4. ✅ 情感分布饼图：直观展示情感比例")
        print("  5. ✅ TOP10柱状图：热点事件排行榜")
        print("  6. ✅ 交互式三维分析：热度-传播-情感关联分析")
        print()

        for chart_name, file_path in results.items():
            if file_path:
                status = "✅"
                if chart_name == "interactive_3d" and "backup" in str(file_path):
                    status = "⚠️"
                print(f"  {status} {chart_name}: 已生成")
                if chart_name == "viewer":
                    print(f"     文件: {file_path} (统一仪表板)")
                else:
                    print(f"     文件: {file_path}")
            else:
                print(f"  ❌ {chart_name}: 生成失败")

        print("=" * 60)

        return {
            "success": success_count > 0,
            "total": 6,
            "success_count": success_count,
            "results": results,
            "time_cost": elapsed_time
        }

    except Exception as e:
        logger.error(f"生成所有图表失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def run_visualizer() -> bool:
        """
        运行数据可视化模块的主函数

        这个函数将被main.py调用

        Returns:
            bool: 是否运行成功
        """
        if not PYECHARTS_AVAILABLE or not JIEBA_AVAILABLE:
            print("❌ 未安装必要的依赖库")
            print("请运行以下命令安装:")
            print("  pip install pyecharts jieba")
            return False

        print("🎨 启动数据可视化模块 - 交互式三维分析版")
        print("=" * 60)
        print("✨ 新增功能:")
        print("  1. 交互式三维关联分析柱状图")
        print("  2. 支持事件选择对比分析")
        print("  3. 智能洞察面板")
        print("  4. 实时统计栏")
        print("  5. 网格卡片式事件选择器")
        print("=" * 60)

        # 询问是否需要诊断
        if input("\n🔍 是否需要诊断数据库状态？(y/n, 默认n): ").strip().lower() == 'y':
            conn = get_db_connection()
            try:
                diagnose_database(conn)
            finally:
                if conn:
                    conn.close()

            confirm = input("是否继续生成图表？(y/n, 默认y): ").strip().lower()
            if confirm == 'n':
                print("已取消图表生成")
                return False

        conn = None
        try:
            # 获取数据库连接
            conn = get_db_connection()

            # 生成所有图表
            result = generate_all_charts(conn)

            if result.get("success", False):
                print("✅ 数据可视化模块运行完成！")
                viewer_path = result.get("results", {}).get("viewer")
                if viewer_path:
                    print(f"📁 集成查看器: {viewer_path}")
                    print(f"📁 单个图表: {os.path.abspath('output/charts')}")
                    print("\n💡 建议: 打开集成查看器文件查看所有图表")

                    # 特别提示交互式三维分析功能
                    interactive_3d_path = result.get("results", {}).get("interactive_3d")
                    if interactive_3d_path:
                        print(f"\n🌟 重点推荐: 交互式三维关联分析")
                        print(f"   功能: 支持选择任意事件进行对比分析")
                        print(f"   文件: {interactive_3d_path}")

                        if "backup" in str(interactive_3d_path):
                            print(f"   ⚠️ 注: 使用了备选方案生成，情感数据可能不完整")
                            print(f"   建议运行情感分析模块（选项3）后再试")
            else:
                print("⚠️ 数据可视化模块部分图表生成失败")

                # 显示具体哪些失败
                results = result.get("results", {})
                failed_charts = [name for name, path in results.items() if not path and name != "viewer"]
                if failed_charts:
                    print(f"   失败的图表: {', '.join(failed_charts)}")
                    print(f"   建议运行诊断功能检查数据状态")

            return result.get("success", False)

        except Exception as e:
            logger.error(f"数据可视化模块运行失败: {e}")
            print(f"❌ 错误: {e}")
            return False
        finally:
            if conn:
                conn.close()



def diagnose_database(conn) -> Dict[str, Any]:
    """
    诊断数据库状态，帮助解决三维分析图生成问题

    Args:
        conn: 数据库连接对象

    Returns:
        Dict[str, Any]: 诊断结果
    """
    cursor = None
    try:
        cursor = conn.cursor()

        print("\n🔍 数据库诊断报告")
        print("=" * 60)

        # 检查表是否存在
        tables = ['hot_events', 'comments', 'sentiment_results']
        table_status = {}

        for table in tables:
            cursor.execute(f"""
            SELECT COUNT(*) as table_exists 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = %s
            """, (table,))
            result = cursor.fetchone()
            exists = result['table_exists'] > 0 if result else False
            table_status[table] = exists

        # 统计数据
        stats = {}

        # hot_events
        if table_status['hot_events']:
            cursor.execute("SELECT COUNT(*) as count FROM hot_events")
            stats['hot_events'] = cursor.fetchone()['count']
        else:
            stats['hot_events'] = 0

        # comments
        if table_status['comments']:
            cursor.execute("SELECT COUNT(*) as count FROM comments")
            stats['comments'] = cursor.fetchone()['count']

            # 有情感标签的评论
            cursor.execute("""
            SELECT 
                COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive,
                COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative,
                COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutral,
                COUNT(CASE WHEN sentiment_label IS NULL THEN 1 END) as unanalyzed
            FROM comments
            """)
            sentiment_stats = cursor.fetchone()
        else:
            stats['comments'] = 0
            sentiment_stats = None

        # sentiment_results
        if table_status['sentiment_results']:
            cursor.execute("SELECT COUNT(*) as count FROM sentiment_results")
            stats['sentiment_results'] = cursor.fetchone()['count']
        else:
            stats['sentiment_results'] = 0

        # 打印诊断结果
        print("📊 表状态:")
        for table, exists in table_status.items():
            status = "✅ 存在" if exists else "❌ 不存在"
            count = stats.get(table, 0)
            print(f"  {table}: {status} ({count} 条记录)")

        print("\n📈 数据统计:")
        print(f"  热点事件总数: {stats['hot_events']}")
        print(f"  评论总数: {stats['comments']}")

        if sentiment_stats:
            print(f"  正面评论: {sentiment_stats['positive']}")
            print(f"  负面评论: {sentiment_stats['negative']}")
            print(f"  中性评论: {sentiment_stats['neutral']}")
            print(f"  未分析评论: {sentiment_stats['unanalyzed']}")

        print(f"  情感统计结果: {stats['sentiment_results']}")

        # 检查今天的数据
        cursor.execute("SELECT COUNT(*) as count FROM hot_events WHERE DATE(created_at) = CURDATE()")
        today_hot_events = cursor.fetchone()['count']
        print(f"  今天的热点事件: {today_hot_events}")

        # 提供建议
        print("\n💡 建议:")
        if not table_status['sentiment_results']:
            print("  ❌ sentiment_results 表不存在")
            print("    解决方案: 运行情感分析模块（选项3）")

        if stats['comments'] == 0:
            print("  ❌ 没有评论数据")
            print("    解决方案: 运行爬虫模块（选项2）")

        if stats['hot_events'] == 0:
            print("  ❌ 没有热点事件数据")
            print("    解决方案: 运行爬虫模块（选项2）")

        if sentiment_stats and sentiment_stats['unanalyzed'] > 0:
            print(f"  ⚠️ 有 {sentiment_stats['unanalyzed']} 条评论未分析")
            print("    解决方案: 运行情感分析模块（选项3）")

        if today_hot_events == 0:
            print("  ⚠️ 今天没有热点事件")
            print("    解决方案: 运行爬虫模块获取最新热点")

        print("=" * 60)

        return {
            "tables": table_status,
            "stats": stats,
            "today_hot_events": today_hot_events
        }

    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()


if __name__ == "__main__":
    """
    直接运行此模块时，执行数据可视化
    """
    print("🎨 数据可视化模块独立运行 - 交互式三维分析版")
    print("=" * 60)

    success = run_visualizer()
    if success:
        print("✅ 数据可视化模块执行完成！")
    else:
        print("❌ 数据可视化模块执行失败！")