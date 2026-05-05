# -*- coding: utf-8 -*-
"""
情感分析模块 - 系统适配版
功能：对评论进行情感分析，适配主系统
作者：Python情感分析导师
日期：2026-05-02
适配版：保持新功能，适配主系统调用
"""

import pymysql
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import re

# 尝试导入SnowNLP
try:
    from snownlp import SnowNLP

    SNOW_NLP_AVAILABLE = True
except ImportError:
    SNOW_NLP_AVAILABLE = False
    print("⚠️ 未安装snownlp，请运行: pip install snownlp")

# 导入项目模块
from config import get_db_connection
import utils

# 获取日志记录器
logger = utils.get_logger(__name__)


def analyze_single(content: str) -> Tuple[str, float]:
    """
    分析单条评论的情感

    Args:
        content: 评论内容

    Returns:
        Tuple[str, float]: (情感标签, 置信度)
    """
    if not SNOW_NLP_AVAILABLE:
        logger.error("SnowNLP未安装")
        return "neutral", 0.5

    try:
        # 清洗文本
        cleaned_text = utils.clean_text(content)

        if not cleaned_text or len(cleaned_text) < 3:
            return "neutral", 0.5

        # 创建SnowNLP对象
        s = SnowNLP(cleaned_text)

        # 获取情感分数 (0-1之间，越接近1表示越正面)
        sentiment_score = s.sentiments

        # 根据阈值划分情感类别
        if sentiment_score > 0.6:  # 正面
            label = "positive"
            confidence = sentiment_score
        elif sentiment_score < 0.4:  # 负面
            label = "negative"
            confidence = 1 - sentiment_score  # 负面置信度
        else:  # 中性
            label = "neutral"
            confidence = 0.5

        return label, round(confidence, 4)  # 保留4位小数

    except Exception as e:
        logger.error(f"情感分析失败: {e}")
        return "neutral", 0.5


def batch_analyze(conn, batch_size: int = 500,
                  commit_every: int = 100,
                  total_limit: Optional[int] = None) -> Dict[str, Any]:
    """
    批量分析评论的主流程 - 适配版

    Args:
        conn: 数据库连接对象
        batch_size: 每次从数据库获取的最大评论数
        commit_every: 每分析多少条提交一次
        total_limit: 总共分析多少条，None表示无限制

    Returns:
        Dict[str, Any]: 统计信息
    """
    cursor = None
    stats = {
        'total_processed': 0,  # 总共处理的评论数
        'success': 0,  # 成功分析的评论数
        'failed': 0,  # 分析失败的评论数
        'positive': 0,  # 正面评论数
        'negative': 0,  # 负面评论数
        'neutral': 0,  # 中性评论数
        'processing_time': 0.0,  # 总处理时间
        'avg_time_per_comment': 0.0,  # 每条评论平均处理时间
    }

    try:
        cursor = conn.cursor()
        start_time = time.time()

        # 如果指定了总数限制，计算需要多少次循环
        if total_limit and total_limit > 0:
            total_batches = (total_limit + batch_size - 1) // batch_size
        else:
            total_batches = None

        batch_count = 0

        while True:
            # 如果有限制且已达到限制，退出
            if total_limit and stats['total_processed'] >= total_limit:
                logger.info(f"已达到处理限制 {total_limit} 条，停止处理")
                break

            # 计算本次需要获取的数量
            current_batch_size = batch_size
            if total_limit:
                remaining = total_limit - stats['total_processed']
                if remaining < current_batch_size:
                    current_batch_size = remaining

            # 查询未分析的评论
            sql = """
            SELECT id, content, event_id, like_count
            FROM comments 
            WHERE sentiment_label IS NULL 
            AND LENGTH(content) > 2
            ORDER BY like_count DESC, id
            LIMIT %s
            """

            cursor.execute(sql, (current_batch_size,))
            comments = cursor.fetchall()

            if not comments:
                logger.info("没有更多需要情感分析的评论")
                break

            batch_count += 1
            current_batch_size = len(comments)
            logger.info(f"第{batch_count}批: 开始分析 {current_batch_size} 条评论")

            # 处理当前批次
            batch_start_time = time.time()
            batch_success = 0
            batch_failed = 0
            batch_positive = 0
            batch_negative = 0
            batch_neutral = 0

            for i, comment in enumerate(comments, 1):
                try:
                    comment_id = comment['id']
                    content = comment['content']
                    event_id = comment['event_id']

                    # 分析情感
                    label, confidence = analyze_single(content)

                    # 更新数据库
                    update_sql = """
                    UPDATE comments 
                    SET sentiment_label = %s, sentiment_confidence = %s
                    WHERE id = %s
                    """
                    cursor.execute(update_sql, (label, confidence, comment_id))

                    if cursor.rowcount > 0:
                        batch_success += 1

                        # 统计情感分布
                        if label == 'positive':
                            batch_positive += 1
                        elif label == 'negative':
                            batch_negative += 1
                        else:
                            batch_neutral += 1

                        # 每100条输出一次进度
                        if i % 100 == 0:
                            progress = stats['total_processed'] + i
                            if total_limit:
                                percent = (progress / total_limit) * 100
                                logger.info(f"进度: {progress}/{total_limit} ({percent:.1f}%)")
                            else:
                                logger.info(f"进度: 第{batch_count}批 {i}/{current_batch_size}")
                    else:
                        batch_failed += 1

                    # 每commit_every条提交一次
                    if i % commit_every == 0:
                        conn.commit()
                        logger.info(f"已提交 {i} 条分析结果")

                except Exception as e:
                    batch_failed += 1
                    logger.error(f"处理评论 {comment.get('id', 'unknown')} 失败: {e}")
                    continue

            # 提交当前批次剩余的分析结果
            conn.commit()

            # 更新统计
            stats['total_processed'] += current_batch_size
            stats['success'] += batch_success
            stats['failed'] += batch_failed
            stats['positive'] += batch_positive
            stats['negative'] += batch_negative
            stats['neutral'] += batch_neutral

            # 计算批次处理时间
            batch_time = time.time() - batch_start_time
            batch_avg_time = batch_time / current_batch_size if current_batch_size > 0 else 0

            logger.info(f"第{batch_count}批完成: 成功 {batch_success}, 失败 {batch_failed}")
            logger.info(f"批次耗时: {batch_time:.1f}秒, 平均每条: {batch_avg_time:.3f}秒")

            # 如果获取的评论数小于请求数，说明没有更多数据了
            if len(comments) < batch_size:
                break

            # 批次间短暂延迟
            time.sleep(0.1)

        # 计算总处理时间
        stats['processing_time'] = time.time() - start_time
        if stats['total_processed'] > 0:
            stats['avg_time_per_comment'] = stats['processing_time'] / stats['total_processed']

        # 输出最终统计
        logger.info("=" * 60)
        logger.info(f"批量分析完成:")
        logger.info(f"  总耗时: {stats['processing_time']:.1f}秒")
        logger.info(f"  总处理评论: {stats['total_processed']}")
        logger.info(f"  成功分析: {stats['success']}")
        logger.info(f"  分析失败: {stats['failed']}")
        logger.info(f"  正面评论: {stats['positive']}")
        logger.info(f"  负面评论: {stats['negative']}")
        logger.info(f"  中性评论: {stats['neutral']}")
        if stats['total_processed'] > 0:
            logger.info(f"  平均每条处理时间: {stats['avg_time_per_comment']:.3f}秒")
        logger.info("=" * 60)

        return stats

    except Exception as e:
        logger.error(f"批量分析失败: {e}")
        conn.rollback()
        return stats
    finally:
        if cursor:
            cursor.close()


def summarize_event(conn, event_id: int) -> bool:
    """
    统计单个事件的情感分布

    Args:
        conn: 数据库连接对象
        event_id: 事件ID

    Returns:
        bool: 是否统计成功
    """
    cursor = None
    try:
        cursor = conn.cursor()

        # 统计情感分布
        sql_statistics = """
        SELECT 
            COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive_count,
            COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative_count,
            COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutral_count,
            COUNT(*) as total_count
        FROM comments 
        WHERE event_id = %s
        """

        cursor.execute(sql_statistics, (event_id,))
        result = cursor.fetchone()

        if not result:
            logger.warning(f"事件 {event_id} 没有评论数据")
            return False

        positive_count = result['positive_count'] or 0
        negative_count = result['negative_count'] or 0
        neutral_count = result['neutral_count'] or 0
        total_count = result['total_count'] or 0

        # 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 插入或更新情感统计结果
        sql_insert = """
        INSERT INTO sentiment_results 
            (event_id, positive_count, negative_count, neutral_count, total_count, analyzed_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            positive_count = VALUES(positive_count),
            negative_count = VALUES(negative_count),
            neutral_count = VALUES(neutral_count),
            total_count = VALUES(total_count),
            analyzed_at = VALUES(analyzed_at)
        """

        cursor.execute(sql_insert, (
            event_id,
            positive_count,
            negative_count,
            neutral_count,
            total_count,
            current_time
        ))

        logger.info(
            f"事件 {event_id} 情感统计: 正{positive_count} 负{negative_count} 中{neutral_count} 总{total_count}")

        return True

    except Exception as e:
        logger.error(f"统计事件 {event_id} 情感分布失败: {e}")
        return False
    finally:
        if cursor:
            cursor.close()


def summarize_all_events(conn) -> Dict[str, int]:
    """
    统计所有事件的情感分布

    Args:
        conn: 数据库连接对象

    Returns:
        Dict[str, int]: 统计信息
    """
    cursor = None
    stats = {
        'events_processed': 0,  # 处理的事件数
        'events_succeeded': 0,  # 统计成功的事件数
        'events_failed': 0,  # 统计失败的事件数
    }

    try:
        cursor = conn.cursor()

        # 获取有评论的事件
        sql = """
        SELECT DISTINCT c.event_id, e.title
        FROM comments c
        JOIN hot_events e ON c.event_id = e.id
        GROUP BY c.event_id
        HAVING COUNT(c.id) > 0
        ORDER BY MAX(e.hot_value) DESC
        """

        cursor.execute(sql)
        events = cursor.fetchall()

        if not events:
            logger.info("没有需要统计的事件")
            return stats

        logger.info(f"开始统计 {len(events)} 个事件的情感分布")

        for event in events:
            event_id = event['event_id']
            title = event['title'][:30] + "..." if len(event['title']) > 30 else event['title']

            try:
                if summarize_event(conn, event_id):
                    stats['events_succeeded'] += 1
                    logger.debug(f"事件统计完成: {title}")
                else:
                    stats['events_failed'] += 1
                    logger.warning(f"事件统计失败: {title}")

                stats['events_processed'] += 1

                # 短暂延迟，避免数据库压力
                time.sleep(0.01)

            except Exception as e:
                stats['events_failed'] += 1
                logger.error(f"处理事件 {event_id} 失败: {e}")
                continue

        logger.info(f"事件统计完成: 成功 {stats['events_succeeded']}, 失败 {stats['events_failed']}")

        return stats

    except Exception as e:
        logger.error(f"统计事件失败: {e}")
        return stats
    finally:
        if cursor:
            cursor.close()


def get_unanalyzed_count(conn) -> int:
    """
    获取未分析的评论数量

    Args:
        conn: 数据库连接对象

    Returns:
        int: 未分析评论数量
    """
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM comments WHERE sentiment_label IS NULL")
        result = cursor.fetchone()
        return result['count'] if result else 0
    except Exception as e:
        logger.error(f"获取未分析评论数失败: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()


def run_analyzer_auto() -> Dict[str, Any]:
    """
    自动运行情感分析（供定时任务调用）

    Returns:
        Dict[str, Any]: 分析统计结果
    """
    if not SNOW_NLP_AVAILABLE:
        logger.error("SnowNLP未安装")
        return {"success": False, "error": "SnowNLP未安装"}

    logger.info("🧠 启动自动情感分析")

    conn = None
    try:
        # 获取数据库连接
        conn = get_db_connection()

        # 获取未分析的评论数量
        unanalyzed_count = get_unanalyzed_count(conn)

        if unanalyzed_count == 0:
            logger.info("ℹ️ 没有需要分析的评论")
            return {"success": True, "no_data": True}

        logger.info(f"📊 发现 {unanalyzed_count} 条未分析评论")

        # 自动处理策略：最多处理2000条
        total_limit = min(unanalyzed_count, 2000)
        batch_size = 500
        commit_every = 100

        # 批量分析评论
        start_time = time.time()
        batch_stats = batch_analyze(conn,
                                    batch_size=batch_size,
                                    commit_every=commit_every,
                                    total_limit=total_limit)

        # 统计事件情感分布
        summary_stats = summarize_all_events(conn)

        elapsed_time = time.time() - start_time

        # 返回结果
        result = {
            "success": True,
            "processing_time": elapsed_time,
            "unanalyzed_count": unanalyzed_count,
            "processed_count": batch_stats['total_processed'],
            "analysis_stats": batch_stats,
            "summary_stats": summary_stats
        }

        return result

    except Exception as e:
        logger.error(f"自动情感分析失败: {e}")
        return {"success": False, "error": str(e)}
    finally:
        if conn:
            conn.close()


def run_analyzer() -> bool:
    """
    运行情感分析模块的主函数（供主菜单调用）

    这个函数将被main.py调用

    Returns:
        bool: 是否运行成功
    """
    if not SNOW_NLP_AVAILABLE:
        print("❌ SnowNLP未安装，请先运行: pip install snownlp")
        return False

    print("🧠 启动情感分析模块")
    print("=" * 60)

    # 先进行准确性检查
    print("🔍 检查情感分析模块...")
    test_texts = [
        "这个太好了，非常喜欢！",
        "太糟糕了，非常失望！",
        "一般般，没什么感觉。"
    ]

    test_results = []
    for text in test_texts:
        label, confidence = analyze_single(text)
        test_results.append({
            "text": text,
            "label": label,
            "confidence": confidence
        })

    print("✅ 情感分析模块检查通过")

    # 运行自动分析
    result = run_analyzer_auto()

    if result.get("success", False):
        if result.get("no_data", False):
            print("✅ 情感分析完成：没有需要分析的数据")
        else:
            stats = result.get("analysis_stats", {})
            print("✅ 情感分析完成！")
            print(f"📊 分析统计:")
            print(f"   处理评论: {stats.get('total_processed', 0)} 条")
            print(f"   成功分析: {stats.get('success', 0)} 条")
            print(f"   正面评论: {stats.get('positive', 0)} 条")
            print(f"   负面评论: {stats.get('negative', 0)} 条")
            print(f"   中性评论: {stats.get('neutral', 0)} 条")
            print(f"⏱️  耗时: {result.get('processing_time', 0):.1f}秒")

        return True
    else:
        print(f"❌ 情感分析失败: {result.get('error', '未知错误')}")
        return False


if __name__ == "__main__":
    """
    直接运行此模块时，执行情感分析
    """
    print("🧠 情感分析模块独立运行")
    print("=" * 60)

    success = run_analyzer()
    if success:
        print("✅ 情感分析模块执行完成！")
    else:
        print("❌ 情感分析模块执行失败！")