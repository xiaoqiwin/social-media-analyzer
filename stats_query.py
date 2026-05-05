# -*- coding: utf-8 -*-
"""
数据库统计查询工具
功能：查询数据库中存储的数据总量和详细统计
作者：Python数据分析导师
日期：2026-05-02
"""

import pymysql
from datetime import datetime, timedelta
import time
import os
from typing import Dict, List, Tuple, Any, Optional
import json
from config import get_db_connection
import utils

# 获取日志记录器
logger = utils.get_logger(__name__)


def ensure_output_dir() -> str:
    """确保输出目录存在"""
    return utils.ensure_output_dir(['reports'])


def format_number(num: int) -> str:
    """格式化数字，添加千位分隔符"""
    return f"{num:,}"


def format_size(size_mb: float) -> str:
    """格式化文件大小"""
    if size_mb >= 1024:
        return f"{size_mb / 1024:.2f} GB"
    else:
        return f"{size_mb:.2f} MB"


def query_database_stats(conn) -> Dict[str, Any]:
    """
    查询数据库整体统计信息

    Args:
        conn: 数据库连接对象

    Returns:
        Dict[str, Any]: 统计信息字典
    """
    cursor = None
    try:
        cursor = conn.cursor()

        print("\n📊 正在查询数据库统计信息...")
        print("=" * 60)

        stats = {}

        # 1. 查询数据库信息
        cursor.execute("SELECT DATABASE() as db_name")
        db_info = cursor.fetchone()
        stats['database_name'] = db_info['db_name'] if db_info else '未知'

        # 2. 查询表结构信息
        cursor.execute("""
        SELECT 
            TABLE_NAME as table_name,
            TABLE_ROWS as row_count,
            DATA_LENGTH as data_size,
            INDEX_LENGTH as index_size,
            CREATE_TIME as create_time,
            UPDATE_TIME as update_time
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = DATABASE()
        ORDER BY TABLE_NAME
        """)

        tables_info = cursor.fetchall()

        if not tables_info:
            print("⚠️ 数据库中没有找到表")
            return stats

        # 处理表信息
        stats['tables'] = []
        total_rows = 0
        total_size_mb = 0

        for table in tables_info:
            table_name = table['table_name']
            row_count = int(table['row_count'] or 0)
            data_size = int(table['data_size'] or 0)
            index_size = int(table['index_size'] or 0)
            table_size_mb = (data_size + index_size) / (1024 * 1024)

            total_rows += row_count
            total_size_mb += table_size_mb

            table_info = {
                'name': table_name,
                'rows': row_count,
                'size_mb': round(table_size_mb, 2),
                'create_time': table['create_time'],
                'update_time': table['update_time']
            }
            stats['tables'].append(table_info)

        stats['total_rows'] = total_rows
        stats['total_size_mb'] = round(total_size_mb, 2)

        # 3. 检查特定表是否存在并查询统计
        tables_to_check = ['hot_events', 'comments', 'sentiment_results']
        for table in tables_to_check:
            cursor.execute(f"""
            SELECT COUNT(*) as table_exists 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = %s
            """, (table,))
            exists_result = cursor.fetchone()
            exists = exists_result['table_exists'] > 0 if exists_result else False

            if exists:
                # 查询表统计
                if table == 'hot_events':
                    cursor.execute("""
                    SELECT 
                        COUNT(*) as total_events,
                        COUNT(DISTINCT DATE(created_at)) as days_with_data,
                        MIN(created_at) as earliest_event,
                        MAX(created_at) as latest_event,
                        AVG(hot_value) as avg_hot_value,
                        SUM(hot_value) as total_hot_value,
                        COUNT(DISTINCT source) as source_count
                    FROM hot_events
                    """)
                    events_stats = cursor.fetchone()
                    stats['hot_events'] = events_stats

                elif table == 'comments':
                    cursor.execute("""
                    SELECT 
                        COUNT(*) as total_comments,
                        COUNT(DISTINCT event_id) as events_with_comments,
                        AVG(LENGTH(content)) as avg_comment_length,
                        MAX(like_count) as max_likes,
                        AVG(like_count) as avg_likes
                    FROM comments
                    """)
                    comments_stats = cursor.fetchone()
                    stats['comments'] = comments_stats

                elif table == 'sentiment_results':
                    cursor.execute("""
                    SELECT 
                        COUNT(*) as total_results,
                        SUM(positive_count) as total_positive,
                        SUM(negative_count) as total_negative,
                        SUM(neutral_count) as total_neutral,
                        SUM(total_count) as total_comments_analyzed
                    FROM sentiment_results
                    WHERE total_count > 0
                    """)
                    sentiment_stats = cursor.fetchone()
                    stats['sentiment_results'] = sentiment_stats

        # 4. 查询情感标签分布（如果comments表存在且有sentiment_label字段）
        cursor.execute("""
        SELECT 
            COUNT(*) as has_sentiment_column
        FROM information_schema.columns 
        WHERE table_schema = DATABASE() 
        AND table_name = 'comments' 
        AND column_name = 'sentiment_label'
        """)
        has_sentiment_column = cursor.fetchone()['has_sentiment_column'] > 0 if cursor.fetchone() else False

        if has_sentiment_column:
            cursor.execute("""
            SELECT 
                sentiment_label,
                COUNT(*) as count
            FROM comments
            WHERE sentiment_label IS NOT NULL
            GROUP BY sentiment_label
            ORDER BY count DESC
            """)
            sentiment_dist = cursor.fetchall()
            stats['sentiment_distribution'] = sentiment_dist

        # 5. 查询近7天数据趋势
        try:
            cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as daily_events,
                SUM(hot_value) as daily_hot_value
            FROM hot_events
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date
            """)
            daily_events = cursor.fetchall()
            stats['daily_events'] = daily_events
        except Exception as e:
            logger.warning(f"查询每日趋势失败: {e}")
            stats['daily_events'] = []

        # 6. 查询数据来源分布
        try:
            cursor.execute("""
            SELECT 
                source,
                COUNT(*) as event_count,
                SUM(hot_value) as total_hot_value,
                AVG(hot_value) as avg_hot_value
            FROM hot_events
            WHERE source IS NOT NULL AND source != ''
            GROUP BY source
            ORDER BY event_count DESC
            LIMIT 10
            """)
            source_dist = cursor.fetchall()
            stats['source_distribution'] = source_dist
        except Exception as e:
            logger.warning(f"查询来源分布失败: {e}")
            stats['source_distribution'] = []

        return stats

    except Exception as e:
        logger.error(f"查询数据库统计信息失败: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()


def print_database_stats(stats: Dict[str, Any]):
    """
    打印数据库统计信息

    Args:
        stats: 统计信息字典
    """
    if not stats:
        print("❌ 没有获取到统计信息")
        return

    print("\n" + "=" * 60)
    print("📊 数据库统计报告")
    print("=" * 60)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if 'database_name' in stats:
        print(f"数据库名称: {stats['database_name']}")
    print()

    # 1. 数据库概览
    print("🏢 数据库概览:")
    print("-" * 40)
    print(f"  总表数: {len(stats.get('tables', []))}")
    print(f"  总行数: {format_number(stats.get('total_rows', 0))}")
    print(f"  总大小: {format_size(stats.get('total_size_mb', 0))}")
    print()

    # 2. 表详细信息
    if 'tables' in stats and stats['tables']:
        print("📁 表详细信息:")
        print("-" * 40)
        for table in stats['tables']:
            table_name = table['name']
            rows = table['rows']
            size = table['size_mb']
            print(f"  {table_name:20s} | 行数: {format_number(rows):>10s} | 大小: {size:6.2f} MB")
        print()

    # 3. hot_events 表统计
    if 'hot_events' in stats and stats['hot_events']:
        events = stats['hot_events']
        print("🔥 热点事件统计:")
        print("-" * 40)
        print(f"  事件总数: {format_number(events.get('total_events', 0))}")
        print(f"  数据天数: {events.get('days_with_data', 0)} 天")
        if events.get('earliest_event'):
            print(f"  最早事件: {events.get('earliest_event')}")
        if events.get('latest_event'):
            print(f"  最新事件: {events.get('latest_event')}")
        if events.get('avg_hot_value'):
            print(f"  平均热度: {events.get('avg_hot_value', 0):.0f}")
        if events.get('total_hot_value'):
            print(f"  总热度值: {format_number(int(events.get('total_hot_value', 0)))}")
        if events.get('source_count'):
            print(f"  数据来源: {events.get('source_count', 0)} 个")
        print()

    # 4. comments 表统计
    if 'comments' in stats and stats['comments']:
        comments = stats['comments']
        print("💬 评论统计:")
        print("-" * 40)
        print(f"  评论总数: {format_number(comments.get('total_comments', 0))}")
        print(f"  有评论的事件数: {format_number(comments.get('events_with_comments', 0))}")
        if comments.get('avg_comment_length'):
            print(f"  平均评论长度: {comments.get('avg_comment_length', 0):.0f} 字符")
        if comments.get('max_likes'):
            print(f"  最高点赞数: {format_number(comments.get('max_likes', 0))}")
        if comments.get('avg_likes'):
            print(f"  平均点赞数: {comments.get('avg_likes', 0):.1f}")
        print()

    # 5. sentiment_results 表统计
    if 'sentiment_results' in stats and stats['sentiment_results']:
        sentiment = stats['sentiment_results']
        print("📈 情感分析统计:")
        print("-" * 40)
        print(f"  分析结果数: {format_number(sentiment.get('total_results', 0))}")
        if sentiment.get('total_comments_analyzed'):
            print(f"  已分析评论数: {format_number(sentiment.get('total_comments_analyzed', 0))}")
        if sentiment.get('total_positive'):
            print(f"  正面评论: {format_number(sentiment.get('total_positive', 0))}")
        if sentiment.get('total_negative'):
            print(f"  负面评论: {format_number(sentiment.get('total_negative', 0))}")
        if sentiment.get('total_neutral'):
            print(f"  中性评论: {format_number(sentiment.get('total_neutral', 0))}")
        print()

    # 6. 数据来源分布
    if 'source_distribution' in stats and stats['source_distribution']:
        print("🌐 数据来源分布 (TOP10):")
        print("-" * 40)
        for source in stats['source_distribution']:
            source_name = source['source'][:15] if source['source'] else '未知'
            count = source['event_count']
            avg_hot = source.get('avg_hot_value', 0)
            print(f"  {source_name:15s} | 事件数: {count:5d} | 平均热度: {avg_hot:.0f}")
        print()

    # 7. 情感标签分布
    if 'sentiment_distribution' in stats and stats['sentiment_distribution']:
        print("😊 情感标签分布:")
        print("-" * 40)
        total_sentiment = sum(s['count'] for s in stats['sentiment_distribution'])
        for sent in stats['sentiment_distribution']:
            label = sent['sentiment_label']
            count = sent['count']
            percentage = (count / total_sentiment * 100) if total_sentiment > 0 else 0

            # 情感标签翻译
            if label == 'positive':
                label_zh = '正面'
            elif label == 'negative':
                label_zh = '负面'
            elif label == 'neutral':
                label_zh = '中性'
            else:
                label_zh = label

            print(f"  {label_zh:4s} ({label:8s}): {format_number(count):>10s} ({percentage:5.1f}%)")
        print()

    # 8. 近7天数据趋势
    if 'daily_events' in stats and stats['daily_events']:
        print("📅 近7天数据趋势:")
        print("-" * 40)
        for day in stats['daily_events']:
            date_str = day['date'].strftime('%Y-%m-%d')
            events_count = day['daily_events']
            hot_value = day.get('daily_hot_value', 0)
            print(f"  {date_str}: {events_count:3d} 个事件 | 热度: {int(hot_value):,}")

        if len(stats['daily_events']) > 1:
            first_day = stats['daily_events'][0]['daily_events']
            last_day = stats['daily_events'][-1]['daily_events']
            if first_day > 0:
                growth = (last_day - first_day) / first_day * 100
                print(f"  趋势: 从 {first_day} 到 {last_day} 个事件 ({growth:+.1f}%)")
        print()

    print("=" * 60)


def save_stats_to_file(stats: Dict[str, Any], file_path: str) -> bool:
    """
    保存统计信息到文件

    Args:
        stats: 统计信息字典
        file_path: 文件路径

    Returns:
        bool: 是否保存成功
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("📊 数据库统计报告\n")
            f.write("=" * 60 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            if 'database_name' in stats:
                f.write(f"数据库名称: {stats['database_name']}\n")

            f.write("🏢 数据库概览:\n")
            f.write("-" * 40 + "\n")
            f.write(f"总表数: {len(stats.get('tables', []))}\n")
            f.write(f"总行数: {format_number(stats.get('total_rows', 0))}\n")
            f.write(f"总大小: {format_size(stats.get('total_size_mb', 0))}\n\n")

            # 表详细信息
            if 'tables' in stats and stats['tables']:
                f.write("📁 表详细信息:\n")
                f.write("-" * 40 + "\n")
                for table in stats['tables']:
                    f.write(
                        f"{table['name']:20s} | 行数: {format_number(table['rows']):>10s} | 大小: {table['size_mb']:6.2f} MB\n")
                f.write("\n")

            # hot_events 统计
            if 'hot_events' in stats and stats['hot_events']:
                events = stats['hot_events']
                f.write("🔥 热点事件统计:\n")
                f.write("-" * 40 + "\n")
                f.write(f"事件总数: {format_number(events.get('total_events', 0))}\n")
                f.write(f"数据天数: {events.get('days_with_data', 0)} 天\n")
                if events.get('earliest_event'):
                    f.write(f"最早事件: {events.get('earliest_event')}\n")
                if events.get('latest_event'):
                    f.write(f"最新事件: {events.get('latest_event')}\n")
                if events.get('avg_hot_value'):
                    f.write(f"平均热度: {events.get('avg_hot_value', 0):.0f}\n")
                if events.get('total_hot_value'):
                    f.write(f"总热度值: {format_number(int(events.get('total_hot_value', 0)))}\n")
                if events.get('source_count'):
                    f.write(f"数据来源: {events.get('source_count', 0)} 个\n")
                f.write("\n")

            # comments 统计
            if 'comments' in stats and stats['comments']:
                comments = stats['comments']
                f.write("💬 评论统计:\n")
                f.write("-" * 40 + "\n")
                f.write(f"评论总数: {format_number(comments.get('total_comments', 0))}\n")
                f.write(f"有评论的事件数: {format_number(comments.get('events_with_comments', 0))}\n")
                if comments.get('avg_comment_length'):
                    f.write(f"平均评论长度: {comments.get('avg_comment_length', 0):.0f} 字符\n")
                if comments.get('max_likes'):
                    f.write(f"最高点赞数: {format_number(comments.get('max_likes', 0))}\n")
                if comments.get('avg_likes'):
                    f.write(f"平均点赞数: {comments.get('avg_likes', 0):.1f}\n")
                f.write("\n")

            # 近7天趋势
            if 'daily_events' in stats and stats['daily_events']:
                f.write("📅 近7天数据趋势:\n")
                f.write("-" * 40 + "\n")
                for day in stats['daily_events']:
                    date_str = day['date'].strftime('%Y-%m-%d')
                    f.write(
                        f"{date_str}: {day['daily_events']:3d} 个事件 | 热度: {int(day.get('daily_hot_value', 0)):,}\n")
                f.write("\n")

            f.write("=" * 60 + "\n")
            f.write("报告生成完成。\n")
            f.write("=" * 60 + "\n")

        logger.info(f"统计报告已保存到: {file_path}")
        return True

    except Exception as e:
        logger.error(f"保存统计报告失败: {e}")
        return False


def query_sample_data(conn, table_name: str, limit: int = 5) -> List[Dict]:
    """
    查询示例数据

    Args:
        conn: 数据库连接对象
        table_name: 表名
        limit: 查询条数

    Returns:
        List[Dict]: 示例数据列表
    """
    cursor = None
    try:
        cursor = conn.cursor()

        # 安全检查表名
        valid_tables = ['hot_events', 'comments', 'sentiment_results']
        if table_name not in valid_tables:
            print(f"⚠️ 警告: 表名 {table_name} 无效")
            return []

        sql = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT %s"
        cursor.execute(sql, (limit,))
        results = cursor.fetchall()

        return results

    except Exception as e:
        logger.error(f"查询示例数据失败: {e}")
        return []
    finally:
        if cursor:
            cursor.close()


def run_database_query() -> bool:
    """
    运行数据库查询主函数

    Returns:
        bool: 是否运行成功
    """
    print("\n🔍 启动数据库统计查询工具")
    print("=" * 60)

    # 检查数据库连接
    try:
        from config import test_connection
        if not test_connection():
            print("❌ 数据库连接失败，请检查配置")
            return False
    except Exception as e:
        print(f"❌ 数据库连接检查失败: {e}")
        return False

    conn = None
    try:
        # 获取数据库连接
        conn = get_db_connection()

        if not conn:
            print("❌ 无法连接到数据库")
            return False

        # 查询统计信息
        stats = query_database_stats(conn)

        if not stats:
            print("❌ 没有获取到统计数据")
            return False

        # 打印统计信息
        print_database_stats(stats)

        # 询问是否保存到文件
        save_to_file = input("\n💾 是否保存统计报告到文件？(y/n, 默认y): ").strip().lower()
        if save_to_file != 'n':
            output_dir = ensure_output_dir()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(output_dir, f"database_stats_{timestamp}.txt")

            if save_stats_to_file(stats, file_path):
                print(f"✅ 统计报告已保存: {file_path}")
            else:
                print("❌ 保存报告失败")

        # 询问是否查看示例数据
        view_samples = input("\n👀 是否查看示例数据？(y/n, 默认n): ").strip().lower()
        if view_samples == 'y':
            print("\n📋 选择要查看的表:")
            print("  1. hot_events (热点事件)")
            print("  2. comments (评论)")
            print("  3. sentiment_results (情感分析结果)")

            try:
                choice = input("请选择 (1-3, 默认1): ").strip()
                table_map = {'1': 'hot_events', '2': 'comments', '3': 'sentiment_results'}
                table_name = table_map.get(choice, 'hot_events')

                limit_input = input("显示多少条记录？(默认5): ").strip()
                limit = int(limit_input) if limit_input else 5
                limit = min(max(limit, 1), 20)  # 限制1-20条

                samples = query_sample_data(conn, table_name, limit)

                if samples:
                    print(f"\n📄 {table_name} 表示例数据 (最近{len(samples)}条):")
                    print("-" * 60)
                    for i, row in enumerate(samples, 1):
                        print(f"\n第 {i} 条记录:")
                        for key, value in row.items():
                            # 截断过长的值
                            if isinstance(value, str) and len(value) > 100:
                                value = value[:100] + "..."
                            print(f"  {key}: {value}")
                else:
                    print(f"❌ 表 {table_name} 中没有数据")

            except ValueError:
                print("⚠️ 输入格式错误")
            except Exception as e:
                logger.error(f"查看示例数据失败: {e}")

        return True

    except Exception as e:
        logger.error(f"数据库查询工具运行失败: {e}")
        print(f"❌ 错误: {e}")
        return False
    finally:
        if conn:
            conn.close()


def simple_query_total_data() -> None:
    """
    简单查询数据库总量（快速版）
    可以直接在main.py中调用的简单版本
    """
    print("\n📊 数据库数据总量查询")
    print("=" * 40)

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ 无法连接到数据库")
            return

        cursor = conn.cursor()

        # 查询各表数据量
        tables = ['hot_events', 'comments', 'sentiment_results']

        for table in tables:
            try:
                # 检查表是否存在
                cursor.execute("""
                SELECT COUNT(*) as table_exists 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = %s
                """, (table,))
                result = cursor.fetchone()
                exists = result['table_exists'] > 0 if result else False

                if exists:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    count = result['count'] if result else 0
                    print(f"  {table:20s}: {format_number(count):>10s} 条记录")
                else:
                    print(f"  {table:20s}: 表不存在")
            except Exception as e:
                print(f"  {table:20s}: 查询失败 ({e})")

        # 查询数据库总大小
        try:
            cursor.execute("""
            SELECT 
                ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as total_mb
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = DATABASE()
            """)
            size_result = cursor.fetchone()
            total_mb = size_result['total_mb'] if size_result else 0
            print(f"\n  数据库总大小: {format_size(total_mb)}")
        except Exception as e:
            print(f"\n  数据库大小查询失败: {e}")

        # 查询最近更新时间
        try:
            cursor.execute("""
            SELECT MAX(updated_at) as last_update
            FROM (
                SELECT MAX(updated_at) as updated_at FROM hot_events
                UNION ALL
                SELECT MAX(updated_at) as updated_at FROM comments
                UNION ALL
                SELECT MAX(updated_at) as updated_at FROM sentiment_results
            ) as all_updates
            """)
            update_result = cursor.fetchone()
            last_update = update_result['last_update'] if update_result else '未知'
            print(f"  最近更新时间: {last_update}")
        except Exception as e:
            print(f"  最近更新时间查询失败: {e}")

        print("=" * 40)

    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    """
    独立运行数据库统计查询
    """
    print("🔍 数据库统计查询工具 - 独立运行")
    print("=" * 60)

    success = run_database_query()
    if success:
        print("\n✅ 数据库统计查询完成！")
    else:
        print("\n❌ 数据库统计查询失败！")