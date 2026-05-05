# -*- coding: utf-8 -*-
"""
微博热搜爬虫模块 - 增强版
功能：爬取微博热搜榜（30个热点）及高赞评论（每个热点50条）
作者：Python项目架构导师
日期：2026-05-02
增强版：增加爬取规模，优化反反爬策略
定时任务增强：支持自动使用已保存的Cookie
"""

import requests
import time
import random
import re
from datetime import datetime
from urllib.parse import quote
import json
from typing import List, Tuple, Optional, Dict, Any
import os
import warnings

warnings.filterwarnings("ignore")  # 忽略SSL警告

# 导入项目模块
from config import get_db_connection
import utils

# 获取日志记录器
logger = utils.get_logger(__name__)


class WeiboHotspotCrawler:
    """
    微博热搜爬虫类 - 增强版
    功能：爬取30个热点，每个热点50条高赞评论
    """

    def __init__(self, cookie: str):
        """
        初始化爬虫

        Args:
            cookie: 微博登录后的cookie字符串
        """
        self.cookie = cookie
        self.session = None
        self.request_count = 0

        # 微博热搜榜单URL（移动端接口）
        self.hot_list_url = "https://m.weibo.cn/api/container/getIndex"
        self.hot_list_params = {
            'containerid': '106003type=25&t=3&disable_hot=1&filter_type=realtimehot'
        }

        # 微博搜索接口
        self.search_url = "https://m.weibo.cn/api/container/getIndex"

        # 微博评论接口
        self.comments_url = "https://m.weibo.cn/comments/hotflow"

        # User-Agent列表，随机使用
        self.user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 12; SM-S9010) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1',
        ]

        # 统计变量
        self.stats = {
            'total_hotspots': 0,  # 总热点数
            'processed_hotspots': 0,  # 已处理热点数
            'new_events': 0,  # 新采集事件数
            'updated_events': 0,  # 更新事件数
            'new_comments': 0,  # 新入库评论数
            'duplicate_comments': 0,  # 重复评论数
            'failed_comments': 0,  # 获取评论失败数
            'retry_success': 0,  # 重试成功次数
        }

        # 初始化session
        self._init_session()

    def _init_session(self):
        """初始化requests session"""
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cookie': self.cookie,
            'Referer': 'https://m.weibo.cn/',
            'X-Requested-With': 'XMLHttpRequest',
        })

    def _random_delay(self, min_delay: float = 2.0, max_delay: float = 5.0):
        """
        随机延迟，避免请求过快

        考虑到要爬取大量数据，增加延迟时间
        """
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"等待 {delay:.1f} 秒...")
        time.sleep(delay)

    def _random_user_agent(self) -> str:
        """随机返回一个User-Agent"""
        return random.choice(self.user_agents)

    def _make_request(self, url: str, params: Optional[Dict] = None,
                      max_retries: int = 3) -> Optional[requests.Response]:
        """
        发送HTTP请求，带重试机制

        Args:
            url: 请求URL
            params: 请求参数
            max_retries: 最大重试次数

        Returns:
            Optional[requests.Response]: 响应对象，失败返回None
        """
        for attempt in range(max_retries):
            try:
                # 每次请求前随机延迟
                self._random_delay(1.0, 3.0)

                # 更新User-Agent
                headers = self.session.headers.copy()
                headers['User-Agent'] = self._random_user_agent()

                # 随机添加一些请求头
                if random.random() > 0.5:
                    headers['X-Forwarded-For'] = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"

                # 发送请求
                response = self.session.get(
                    url=url,
                    params=params,
                    headers=headers,
                    timeout=15 + attempt * 5,  # 重试时增加超时时间
                    verify=False
                )

                # 检查响应状态
                response.raise_for_status()

                # 检查响应内容
                if response.status_code == 200 and len(response.text) > 10:
                    if attempt > 0:
                        self.stats['retry_success'] += 1
                        logger.info(f"请求重试成功: {url} (第{attempt}次重试)")
                    return response
                else:
                    logger.warning(f"响应异常: 状态码={response.status_code}, 内容长度={len(response.text)}")
                    raise requests.exceptions.RequestException("响应异常")

            except requests.exceptions.Timeout:
                logger.warning(f"请求超时 ({attempt + 1}/{max_retries}): {url}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"连接错误 ({attempt + 1}/{max_retries}): {url}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 ({attempt + 1}/{max_retries}): {e}")

            # 重试前等待
            if attempt < max_retries - 1:
                retry_delay = (attempt + 1) * random.uniform(3, 8)
                logger.info(f"等待 {retry_delay:.1f} 秒后重试...")
                time.sleep(retry_delay)

        logger.error(f"请求失败，已达到最大重试次数: {url}")
        return None

    def fetch_hot_list(self) -> List[Tuple[str, int]]:
        """
        获取微博热搜榜单（30个热点）

        Returns:
            List[Tuple[str, int]]: 热搜列表，每个元素为(标题, 热度值)
        """
        hot_items = []

        try:
            logger.info("开始获取微博热搜榜（30个热点）...")

            # 发送请求
            response = self._make_request(
                url=self.hot_list_url,
                params=self.hot_list_params
            )

            if not response:
                logger.error("获取热搜榜失败：请求失败")
                return hot_items

            # 解析JSON响应
            data = response.json()

            # 检查返回状态
            if data.get('ok') != 1:
                logger.error(f"获取热搜榜失败：接口返回错误 {data.get('msg', '未知错误')}")
                return hot_items

            # 解析热搜数据
            cards = data.get('data', {}).get('cards', [])

            for card in cards:
                if 'card_group' in card:
                    for item in card['card_group']:
                        try:
                            # 提取标题和热度值
                            title = item.get('desc', '')
                            hot_value = item.get('desc_extr', '0')

                            # 清洗标题
                            cleaned_title = utils.clean_text(title)

                            # 跳过空标题
                            if not cleaned_title or len(cleaned_title) < 2:
                                continue

                            # 转换热度值为整数
                            try:
                                hot_value_str = str(hot_value).strip()
                                if '亿' in hot_value_str:
                                    hot_value_int = int(float(hot_value_str.replace('亿', '')) * 100000000)
                                elif '万' in hot_value_str:
                                    hot_value_int = int(float(hot_value_str.replace('万', '')) * 10000)
                                elif 'k' in hot_value_str.lower():
                                    hot_value_int = int(float(hot_value_str.lower().replace('k', '')) * 1000)
                                else:
                                    hot_value_int = int(hot_value_str)
                            except (ValueError, TypeError):
                                # 如果转换失败，给一个随机热度值
                                hot_value_int = random.randint(10000, 500000)

                            # 添加到列表
                            hot_items.append((cleaned_title, hot_value_int))

                        except Exception as e:
                            logger.warning(f"解析热搜条目失败: {e}")
                            continue

            # 获取30个热点
            hot_items = hot_items[:30]

            # 更新统计
            self.stats['total_hotspots'] = len(hot_items)
            logger.info(f"成功获取 {len(hot_items)} 条热搜")

            return hot_items

        except Exception as e:
            logger.error(f"获取热搜榜时发生未知错误: {e}")
            return []

    def fetch_comments_with_retry(self, event_title: str, max_comments: int = 50) -> List[Tuple[str, int]]:
        """
        获取评论，带有重试机制

        Args:
            event_title: 事件标题
            max_comments: 最大评论数（目标50条）

        Returns:
            List[Tuple[str, int]]: 评论列表
        """
        comments = []

        try:
            logger.info(f"开始获取事件 '{event_title[:20]}...' 的评论（目标{max_comments}条）...")

            # 1. 搜索微博，获取微博ID
            search_params = {
                'containerid': f'100103type=1&q={quote(event_title)}',
                'page_type': 'searchall'
            }

            # 发送搜索请求
            search_response = self._make_request(
                url=self.search_url,
                params=search_params
            )

            if not search_response:
                logger.warning(f"搜索事件 '{event_title}' 失败")
                return comments

            search_data = search_response.json()

            # 提取微博ID
            weibo_id = None
            if 'data' in search_data and 'cards' in search_data['data']:
                for card in search_data['data']['cards']:
                    if 'mblog' in card and 'id' in card['mblog']:
                        weibo_id = card['mblog']['id']
                        break
                    elif 'card_group' in card:
                        for sub_card in card['card_group']:
                            if 'mblog' in sub_card and 'id' in sub_card['mblog']:
                                weibo_id = sub_card['mblog']['id']
                                break
                        if weibo_id:
                            break

            # 如果没有找到微博ID，尝试备用方法
            if not weibo_id:
                # 尝试从其他字段获取
                for card in search_data.get('data', {}).get('cards', []):
                    for key, value in card.items():
                        if isinstance(value, dict) and 'id' in value:
                            weibo_id = value['id']
                            break
                    if weibo_id:
                        break

            if not weibo_id:
                logger.warning(f"未找到事件 '{event_title}' 对应的微博ID")
                return comments

            logger.info(f"找到微博ID: {weibo_id}")

            # 2. 获取评论（多页获取，直到达到max_comments）
            max_pages = 5  # 最多获取5页
            comments_collected = 0
            max_id = 0

            for page in range(max_pages):
                try:
                    # 评论请求参数
                    comment_params = {
                        'id': weibo_id,
                        'mid': weibo_id,
                        'max_id_type': 0
                    }

                    # 如果不是第一页，需要max_id
                    if page > 0 and max_id:
                        comment_params['max_id'] = max_id

                    # 发送评论请求
                    comment_response = self._make_request(
                        url=self.comments_url,
                        params=comment_params
                    )

                    if not comment_response:
                        logger.warning(f"获取第{page + 1}页评论失败")
                        break

                    comment_data = comment_response.json()

                    # 检查返回状态
                    if comment_data.get('ok') != 1:
                        logger.warning(f"获取第{page + 1}页评论失败: {comment_data.get('msg', '未知错误')}")
                        break

                    # 提取评论数据
                    data_list = comment_data.get('data', {}).get('data', [])

                    # 如果没有评论了，退出循环
                    if not data_list:
                        break

                    # 处理每条评论
                    page_comments = 0
                    for comment_item in data_list:
                        try:
                            # 提取评论内容
                            content = comment_item.get('text', '')

                            # 去除HTML标签
                            content = re.sub(r'<[^>]+>', '', content)

                            # 清理内容
                            content = self._clean_comment_content(content)

                            # 过滤短评论
                            if len(content.strip()) < 3:
                                continue

                            # 提取点赞数
                            like_count = comment_item.get('like_count', 0)

                            # 添加到列表
                            comments.append((content.strip(), like_count))
                            comments_collected += 1
                            page_comments += 1

                            # 达到目标数量则退出
                            if comments_collected >= max_comments:
                                break

                        except Exception as e:
                            logger.warning(f"解析评论失败: {e}")
                            continue

                    logger.info(
                        f"第{page + 1}页获取到 {page_comments} 条评论，累计 {comments_collected}/{max_comments} 条")

                    if comments_collected >= max_comments:
                        break

                    # 获取下一页的max_id
                    max_id = comment_data.get('data', {}).get('max_id', 0)

                    # 如果max_id为0，表示没有更多评论
                    if max_id == 0:
                        break

                    # 页面间延迟
                    self._random_delay(2.0, 4.0)

                except Exception as e:
                    logger.warning(f"获取第{page + 1}页评论失败: {e}")
                    break

            logger.info(f"成功获取 {len(comments)} 条评论（目标{max_comments}条）")
            return comments[:max_comments]  # 确保不超过目标数量

        except Exception as e:
            logger.error(f"获取评论时发生未知错误: {e}")
            return []

    def _clean_comment_content(self, content: str) -> str:
        """
        清理评论内容，处理编码问题

        Args:
            content: 原始评论内容

        Returns:
            str: 清理后的内容
        """
        if not content:
            return ""

        try:
            # 如果内容不是字符串，尝试转换
            if not isinstance(content, str):
                try:
                    # 尝试用utf-8解码
                    content = content.decode('utf-8', errors='ignore')
                except (UnicodeDecodeError, AttributeError):
                    # 尝试用gb18030解码
                    try:
                        content = content.decode('gb18030', errors='ignore')
                    except (UnicodeDecodeError, AttributeError):
                        # 最后尝试用系统默认编码
                        try:
                            content = str(content, errors='ignore')
                        except:
                            return ""

            # 移除控制字符
            content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)

            # 移除BOM
            content = content.replace('\ufeff', '').replace('\ufffe', '')

            # 移除多余的空白字符
            content = ' '.join(content.split())

            # 移除常见干扰字符
            content = re.sub(r'[\r\n\t]+', ' ', content)

            return content

        except Exception as e:
            logger.warning(f"清理评论内容失败: {e}")
            return ""

    def save_event(self, conn, cursor, title: str, hot_value: int) -> Optional[int]:
        """
        保存事件到数据库

        Args:
            conn: 数据库连接对象
            cursor: 数据库游标对象
            title: 事件标题
            hot_value: 热度值

        Returns:
            Optional[int]: 事件ID，失败返回None
        """
        try:
            # 计算标题的MD5哈希
            event_hash = utils.get_md5(title)

            # 获取当前日期
            current_date = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # SQL语句：如果存在则更新，不存在则插入
            sql = """
            INSERT INTO hot_events 
                (event_hash, title, hot_value, source, crawl_date, created_at, updated_at)
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                hot_value = VALUES(hot_value),
                updated_at = VALUES(updated_at)
            """

            # 执行SQL
            cursor.execute(sql, (
                event_hash,
                title,
                hot_value,
                '微博',
                current_date,
                current_time,
                current_time
            ))

            # 获取事件ID
            cursor.execute(
                "SELECT id FROM hot_events WHERE event_hash = %s",
                (event_hash,)
            )
            result = cursor.fetchone()

            if result:
                event_id = result['id']

                # 检查是新插入还是更新
                if cursor.rowcount == 1:
                    self.stats['new_events'] += 1
                    logger.info(f"新事件入库: {title[:30]}... (ID: {event_id})")
                else:
                    self.stats['updated_events'] += 1
                    logger.info(f"更新事件热度: {title[:30]}... (ID: {event_id})")

                return event_id

            return None

        except Exception as e:
            logger.error(f"保存事件失败: {e}")
            return None

    def save_comment(self, cursor, event_id: int, content: str, like_count: int) -> bool:
        """
        保存评论到数据库

        Args:
            cursor: 数据库游标对象
            event_id: 事件ID
            content: 评论内容
            like_count: 点赞数

        Returns:
            bool: 是否保存成功
        """
        try:
            # 进一步清理内容
            content = self._clean_comment_content(content)

            # 过滤短评论
            if len(content.strip()) < 3:
                return False

            # 计算评论内容的MD5哈希
            content_hash = utils.get_md5(content)

            # 获取当前时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # SQL语句：忽略重复插入
            sql = """
            INSERT IGNORE INTO comments 
                (event_id, content, like_count, content_hash, created_at)
            VALUES 
                (%s, %s, %s, %s, %s)
            """

            # 执行SQL
            cursor.execute(sql, (
                event_id,
                content,
                like_count,
                content_hash,
                current_time
            ))

            # 检查是否成功插入
            if cursor.rowcount > 0:
                self.stats['new_comments'] += 1
                return True
            else:
                self.stats['duplicate_comments'] += 1
                return False

        except Exception as e:
            logger.error(f"保存评论失败: {e}")
            return False

    def run(self) -> bool:
        """
        运行爬虫 - 爬取30个热点，每个热点50条评论

        Returns:
            bool: 是否运行成功
        """
        conn = None
        cursor = None

        try:
            logger.info("开始运行微博热搜爬虫（增强版）...")
            print("=" * 60)
            print("🚀 微博热搜爬虫 - 增强版")
            print(f"📊 目标: 30个热点，每个热点50条高赞评论")
            print("⏰ 预计耗时: 30-60分钟")
            print("=" * 60)

            # 1. 获取数据库连接
            conn = get_db_connection()
            cursor = conn.cursor()

            # 2. 获取热搜列表（30个）
            hot_items = self.fetch_hot_list()

            if not hot_items or len(hot_items) < 5:
                logger.error("获取到的热搜数据不足，程序退出")
                return False

            # 3. 遍历每个热搜事件
            for i, (title, hot_value) in enumerate(hot_items, 1):
                try:
                    logger.info(f"\n处理第 {i}/{len(hot_items)} 个热搜: {title[:40]}...")
                    self.stats['processed_hotspots'] += 1

                    # 保存事件
                    event_id = self.save_event(conn, cursor, title, hot_value)

                    if not event_id:
                        logger.warning(f"事件保存失败，跳过: {title[:30]}...")
                        self.stats['failed_comments'] += 1
                        continue

                    # 事件间延迟
                    self._random_delay(3.0, 6.0)

                    # 获取评论（目标50条）
                    comments = self.fetch_comments_with_retry(title, max_comments=50)

                    if not comments:
                        logger.info(f"未获取到评论: {title[:30]}...")
                        self.stats['failed_comments'] += 1
                        continue

                    # 保存评论
                    saved_count = 0
                    for content, like_count in comments:
                        if self.save_comment(cursor, event_id, content, like_count):
                            saved_count += 1

                    logger.info(f"成功保存 {saved_count}/{len(comments)} 条评论")

                    # 每处理5个热点，提交一次事务
                    if i % 5 == 0:
                        conn.commit()
                        logger.info(f"已提交前 {i} 个热点的数据")

                    # 热点间延迟
                    if i < len(hot_items):
                        delay = random.uniform(5, 10)
                        logger.info(f"等待 {delay:.1f} 秒后处理下一个热点...")
                        time.sleep(delay)

                except Exception as e:
                    logger.error(f"处理热搜 '{title[:30]}...' 时发生错误: {e}")
                    self.stats['failed_comments'] += 1
                    continue

            # 4. 提交剩余事务
            conn.commit()
            logger.info("所有数据已提交到数据库")

            # 5. 打印统计信息
            print("\n" + "=" * 60)
            print("📊 爬取统计报告")
            print("=" * 60)
            print(f"🔥 总热点数: {self.stats['total_hotspots']}")
            print(f"📋 已处理热点: {self.stats['processed_hotspots']}")
            print(f"🆕 新采集事件: {self.stats['new_events']}")
            print(f"🔄 更新事件: {self.stats['updated_events']}")
            print(f"💬 新入库评论: {self.stats['new_comments']}")
            print(f"🔁 跳过重复评论: {self.stats['duplicate_comments']}")
            print(f"❌ 获取评论失败: {self.stats['failed_comments']}")
            print(f"🔄 重试成功: {self.stats['retry_success']}")
            print("=" * 60)

            # 6. 输出总结
            print(f"\n🎯 本次爬取总结:")
            print(f"   新采集{self.stats['new_events']}个事件，"
                  f"更新{self.stats['updated_events']}个事件")
            print(f"   新入库{self.stats['new_comments']}条评论")
            print(f"   跳过{self.stats['duplicate_comments']}条重复评论")

            # 计算评论/热点比
            if self.stats['processed_hotspots'] > 0:
                avg_comments = self.stats['new_comments'] / self.stats['processed_hotspots']
                print(f"   平均每个热点获取{avg_comments:.1f}条评论")

            return True

        except Exception as e:
            logger.error(f"爬虫运行失败: {e}")
            if conn:
                conn.rollback()
                logger.info("已回滚未提交的事务")
            return False

        finally:
            # 关闭数据库连接
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            logger.info("数据库连接已关闭")


def get_cookie_from_user() -> str:
    """
    从用户输入获取Cookie

    Returns:
        str: Cookie字符串
    """
    print("\n" + "=" * 60)
    print("微博Cookie获取说明")
    print("=" * 60)
    print("1. 登录微博手机版: https://m.weibo.cn/")
    print("2. 按F12打开开发者工具")
    print("3. 选择Network标签")
    print("4. 刷新页面，找到任意请求")
    print("5. 在Request Headers中找到Cookie字段")
    print("6. 复制整个Cookie字符串")
    print("7. 注意：Cookie通常会在几小时或几天后失效")
    print("-" * 60)

    while True:
        cookie = input("请输入Cookie: ").strip()

        if not cookie:
            print("❌ Cookie不能为空，请重新输入")
            continue

        # 简单验证Cookie格式
        if "SUB=" not in cookie and "SESSION=" not in cookie:
            confirm = input("⚠️ Cookie似乎不包含必要的SESSION或SUB字段，是否继续？(y/n): ").strip().lower()
            if confirm != 'y':
                continue

        # 保存Cookie
        try:
            with open("weibo_cookie.txt", 'w', encoding='utf-8') as f:
                f.write(cookie)
            print(f"✅ Cookie已保存到 weibo_cookie.txt")
        except Exception as e:
            print(f"⚠️ 保存Cookie失败: {e}")

        return cookie


def load_saved_cookie() -> Optional[str]:
    """
    加载已保存的Cookie文件

    Returns:
        Optional[str]: Cookie字符串，如果文件不存在或无效则返回None
    """
    cookie_file = "weibo_cookie.txt"

    if not os.path.exists(cookie_file):
        return None

    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookie = f.read().strip()

        if cookie and len(cookie) > 20:
            return cookie
        else:
            return None
    except Exception as e:
        logger.warning(f"读取Cookie文件失败: {e}")
        return None


def test_cookie_validity(cookie: str) -> bool:
    """
    测试Cookie是否有效

    Args:
        cookie: Cookie字符串

    Returns:
        bool: Cookie是否有效
    """
    print("\n🔍 测试Cookie有效性...")

    try:
        # 尝试获取热搜榜测试Cookie
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Cookie': cookie,
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://m.weibo.cn/',
        }

        response = requests.get(
            url='https://m.weibo.cn/api/container/getIndex',
            params={'containerid': '106003type=25&t=3&disable_hot=1&filter_type=realtimehot'},
            headers=headers,
            timeout=10,
            verify=False
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('ok') == 1:
                print("✅ Cookie有效，可以正常访问微博")
                return True
            else:
                print(f"❌ Cookie可能无效，接口返回: {data.get('msg', '未知错误')}")
                return False
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 测试Cookie时出错: {e}")
        return False


def run_crawler_auto() -> bool:
    """
    自动运行爬虫（用于定时任务）
    不进行交互，直接使用已保存的Cookie

    Returns:
        bool: 是否运行成功
    """
    print("🚀 自动运行微博热搜爬虫（定时任务模式）")
    print("=" * 60)
    print("🔧 模式: 定时任务自动运行")
    print("🔍 自动加载已保存的Cookie")
    print("=" * 60)

    try:
        # 1. 加载已保存的Cookie
        cookie = load_saved_cookie()

        if not cookie:
            print("❌ 未找到已保存的Cookie文件")
            print("请先手动运行一次爬虫以保存Cookie")
            return False

        print(f"✅ 已加载Cookie ({len(cookie)} 字符)")

        # 2. 测试Cookie有效性
        if not test_cookie_validity(cookie):
            print("❌ Cookie已失效，请重新获取")
            print("请在主系统中手动运行爬虫模块更新Cookie")
            return False

        # 3. 创建爬虫实例
        crawler = WeiboHotspotCrawler(cookie)

        # 4. 运行爬虫
        success = crawler.run()

        if success:
            print("✅ 爬虫模块运行完成！")
        else:
            print("❌ 爬虫模块运行失败！")

        return success

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序")
        return False
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        return False


def run_crawler() -> bool:
    """
    手动运行爬虫模块的主函数
    支持交互式Cookie获取

    Returns:
        bool: 是否运行成功
    """
    print("🚀 启动微博热搜爬虫模块 - 增强版")
    print("=" * 60)
    print("🔧 模式: 手动交互运行")
    print("=" * 60)

    try:
        # 1. 检查是否有已保存的Cookie
        saved_cookie = load_saved_cookie()

        if saved_cookie:
            print(f"检测到已保存的Cookie ({len(saved_cookie)} 字符)")
            print("1. 使用已保存的Cookie")
            print("2. 输入新的Cookie")
            print("3. 退出")

            choice = input("请选择 (1-3, 默认1): ").strip()

            if choice == "2":
                cookie = get_cookie_from_user()
            elif choice == "3":
                return False
            else:
                cookie = saved_cookie
                print(f"✅ 使用已保存的Cookie")

                # 测试Cookie有效性
                if not test_cookie_validity(cookie):
                    print("❌ Cookie已失效，需要重新获取")
                    cookie = get_cookie_from_user()
        else:
            # 2. 获取Cookie
            cookie = get_cookie_from_user()

        # 3. 测试Cookie有效性
        if not test_cookie_validity(cookie):
            print("⚠️ Cookie可能已失效，请重新获取")
            confirm = input("是否继续运行？(y/n): ").strip().lower()
            if confirm != 'y':
                return False

        # 4. 创建爬虫实例
        crawler = WeiboHotspotCrawler(cookie)

        # 5. 运行爬虫
        success = crawler.run()

        if success:
            print("✅ 爬虫模块运行完成！")
        else:
            print("❌ 爬虫模块运行失败！")

        return success

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序")
        return False
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        return False


if __name__ == "__main__":
    """
    直接运行此模块时，执行爬虫
    """
    print("请选择运行模式:")
    print("1. 手动交互模式")
    print("2. 自动模式（使用已保存的Cookie）")

    choice = input("请选择 (1-2, 默认1): ").strip()

    if choice == "2":
        success = run_crawler_auto()
    else:
        success = run_crawler()

    if success:
        print("✅ 爬虫模块执行完成！")
    else:
        print("❌ 爬虫模块执行失败！")