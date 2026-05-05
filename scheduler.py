# -*- coding: utf-8 -*-
"""
定时任务模块
功能：每3小时自动运行完整的分析流程
作者：Python自动化导师
日期：2026-05-02
"""

import time
import datetime
import threading
import schedule
import os
import sys
from typing import Dict, Any, Optional
import signal

# 导入项目模块
import utils
import crawler
import analyzer
import visualizer
import reporter
from config import get_db_connection, test_connection

# 导入自动部署模块
try:
    from auto_update_and_deploy import commit_and_push

    DEPLOY_AVAILABLE = True
except ImportError:
    DEPLOY_AVAILABLE = False

# 获取日志记录器
logger = utils.get_logger(__name__)


class ScheduledAnalyzer:
    """
    定时分析器类
    功能：每3小时自动运行完整的分析流程
    """

    def __init__(self, interval_hours: int = 3):
        """
        初始化定时分析器

        Args:
            interval_hours: 执行间隔小时数，默认3小时
        """
        self.interval_hours = interval_hours
        self.is_running = False
        self.next_run_time = None
        self.run_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.last_run_time = None

        # 创建日志文件
        self.log_file = "scheduler.log"
        self._init_log_file()

    def _init_log_file(self):
        """初始化日志文件"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"定时任务启动时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"执行间隔: 每{self.interval_hours}小时\n")
            f.write(f"{'=' * 60}\n\n")

    def log_schedule_event(self, event: str, details: str = ""):
        """
        记录定时任务事件

        Args:
            event: 事件描述
            details: 详细信息
        """
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {event}\n"
        if details:
            log_entry += f"     详细信息: {details}\n"

        # 写入日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        # 同时输出到控制台
        print(log_entry)
        logger.info(event)

    def run_single_cycle(self) -> Dict[str, Any]:
        """
        运行单次完整的分析流程

        Returns:
            Dict[str, Any]: 运行结果统计
        """
        start_time = time.time()
        cycle_start = datetime.datetime.now()
        self.run_count += 1

        print("\n" + "=" * 60)
        print(f"⏰ 开始第 {self.run_count} 次定时分析")
        print(f"⏰ 开始时间: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        self.log_schedule_event(f"开始第 {self.run_count} 次定时分析")

        results = {
            "cycle": self.run_count,
            "start_time": cycle_start,
            "end_time": None,
            "steps": {
                "database_check": False,
                "crawler": False,
                "analyzer": False,
                "visualizer": False,
                "reporter": False
            },
            "success": False,
            "time_cost": 0
        }

        try:
            # 1. 检查数据库连接
            print("\n🔍 步骤1: 检查数据库连接...")
            if not test_connection():
                raise Exception("数据库连接失败")

            results["steps"]["database_check"] = True
            self.log_schedule_event("数据库连接检查", "成功")

            # 2. 运行爬虫模块
            print("\n🕷️ 步骤2: 运行爬虫模块...")
            crawler_success = crawler.run_crawler_auto()  # 改为调用自动版本
            results["steps"]["crawler"] = crawler_success
            if crawler_success:
                self.log_schedule_event("爬虫模块", "运行成功")
            else:
                self.log_schedule_event("爬虫模块", "运行失败")

            # 3. 运行情感分析模块
            print("\n🧠 步骤3: 运行情感分析模块...")
            analyzer_success = analyzer.run_analyzer()
            results["steps"]["analyzer"] = analyzer_success
            if analyzer_success:
                self.log_schedule_event("情感分析模块", "运行成功")
            else:
                self.log_schedule_event("情感分析模块", "运行失败")

            # 4. 运行可视化模块
            print("\n🎨 步骤4: 运行可视化模块...")
            visualizer_success = visualizer.run_visualizer()
            results["steps"]["visualizer"] = visualizer_success
            if visualizer_success:
                self.log_schedule_event("可视化模块", "运行成功")
            else:
                self.log_schedule_event("可视化模块", "运行失败")

            # 5. 运行报告生成模块
            print("\n📄 步骤5: 运行报告生成模块...")
            reporter_success = reporter.run_reporter()
            results["steps"]["reporter"] = reporter_success
            if reporter_success:
                self.log_schedule_event("报告生成模块", "运行成功")
            else:
                self.log_schedule_event("报告生成模块", "运行失败")

            # 计算总耗时
            end_time = time.time()
            time_cost = end_time - start_time

            # 判断是否成功
            all_success = all(results["steps"].values())
            results["success"] = all_success
            results["end_time"] = datetime.datetime.now()
            results["time_cost"] = time_cost

            if all_success:
                self.success_count += 1
                self.log_schedule_event(f"第 {self.run_count} 次分析", f"全部完成，耗时 {time_cost:.1f}秒")
                print(f"\n✅ 第 {self.run_count} 次定时分析全部完成！")

                # 自动部署到Netlify
                if DEPLOY_AVAILABLE:
                    print("\n🚀 正在自动部署网站到Netlify...")
                    try:
                        project_dir = os.path.dirname(os.path.abspath(__file__))
                        deploy_success = commit_and_push(project_dir, message=f"定时更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        if deploy_success:
                            self.log_schedule_event("自动部署", "部署成功")
                            print("✅ 自动部署成功！网站将在1-2分钟后更新")
                        else:
                            self.log_schedule_event("自动部署", "部署失败")
                            print("⚠️ 自动部署失败")
                    except Exception as deploy_error:
                        self.log_schedule_event("自动部署", f"部署异常: {str(deploy_error)}")
                        print(f"⚠️ 自动部署异常: {deploy_error}")
            else:
                self.fail_count += 1
                failed_steps = [step for step, success in results["steps"].items() if not success]
                self.log_schedule_event(f"第 {self.run_count} 次分析",
                                        f"部分失败，失败步骤: {', '.join(failed_steps)}")
                print(f"\n⚠️ 第 {self.run_count} 次定时分析部分步骤失败")

            # 打印摘要
            print("\n" + "=" * 60)
            print("📊 本次分析结果摘要")
            print("=" * 60)
            for step, success in results["steps"].items():
                status = "✅" if success else "❌"
                print(f"  {status} {step}: {'成功' if success else '失败'}")
            print(f"⏱️  总耗时: {time_cost:.1f}秒")
            print("=" * 60)

            return results

        except Exception as e:
            end_time = time.time()
            time_cost = end_time - start_time
            results["end_time"] = datetime.datetime.now()
            results["time_cost"] = time_cost
            results["error"] = str(e)

            self.fail_count += 1
            self.log_schedule_event(f"第 {self.run_count} 次分析", f"发生异常: {str(e)}")

            print(f"\n❌ 第 {self.run_count} 次定时分析发生异常: {e}")
            print(f"⏱️  耗时: {time_cost:.1f}秒")

            return results

    def run_continuously(self, interval_hours: Optional[int] = None):
        """
        连续运行定时任务

        Args:
            interval_hours: 执行间隔小时数，如果不指定则使用初始化时的间隔
        """
        if interval_hours is None:
            interval_hours = self.interval_hours

        self.is_running = True

        print("\n" + "=" * 60)
        print("🚀 启动定时任务系统")
        print("=" * 60)
        print(f"⏰ 执行间隔: 每 {interval_hours} 小时")
        print(f"📁 日志文件: {self.log_file}")
        print("💡 按 Ctrl+C 停止定时任务")
        print("=" * 60)

        self.log_schedule_event("启动定时任务系统", f"执行间隔: 每 {interval_hours} 小时")

        try:
            while self.is_running:
                # 计算下一次运行时间
                self.next_run_time = datetime.datetime.now() + datetime.timedelta(hours=interval_hours)
                self.last_run_time = datetime.datetime.now()

                # 运行单次分析
                self.run_single_cycle()

                if not self.is_running:
                    break

                # 计算并显示下一次运行时间
                self.next_run_time = datetime.datetime.now() + datetime.timedelta(hours=interval_hours)
                print(f"\n⏳ 下一次分析将在: {self.next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏳ 距离下次分析还有: {interval_hours} 小时")

                # 分割等待时间，每10分钟检查一次是否要停止
                wait_seconds = interval_hours * 3600
                check_interval = 600  # 每10分钟检查一次

                for _ in range(wait_seconds // check_interval):
                    if not self.is_running:
                        break
                    time.sleep(check_interval)

                # 等待剩余时间
                if self.is_running:
                    remaining = wait_seconds % check_interval
                    if remaining > 0:
                        time.sleep(remaining)

        except KeyboardInterrupt:
            self.stop()
            print("\n\n⚠️ 定时任务被用户中断")
        except Exception as e:
            self.log_schedule_event("定时任务异常", f"发生异常: {str(e)}")
            print(f"\n❌ 定时任务发生异常: {e}")
            self.stop()

    def run_single_time(self):
        """只运行一次完整流程"""
        self.run_single_cycle()

    def stop(self):
        """停止定时任务"""
        self.is_running = False
        self.log_schedule_event("停止定时任务",
                                f"总运行次数: {self.run_count}, 成功: {self.success_count}, 失败: {self.fail_count}")
        print("\n🛑 定时任务已停止")
        print(f"📊 统计: 总运行 {self.run_count} 次, 成功 {self.success_count} 次, 失败 {self.fail_count} 次")

    def get_status(self) -> Dict[str, Any]:
        """
        获取定时任务状态

        Returns:
            Dict[str, Any]: 状态信息
        """
        status = {
            "is_running": self.is_running,
            "interval_hours": self.interval_hours,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "last_run_time": self.last_run_time,
            "next_run_time": self.next_run_time
        }

        if self.last_run_time and self.next_run_time:
            time_until_next = (self.next_run_time - datetime.datetime.now()).total_seconds()
            status["time_until_next_minutes"] = int(time_until_next / 60)

        return status


def run_scheduler():
    """
    运行定时任务模块的主函数

    这个函数将被main.py调用
    """
    print("⏰ 启动定时任务模块")
    print("=" * 60)

    try:
        # 创建定时分析器，改为3小时
        scheduler = ScheduledAnalyzer(interval_hours=3)

        # 启动定时任务
        scheduler.run_continuously()

        return True

    except KeyboardInterrupt:
        print("\n\n⚠️ 定时任务被用户中断")
        return False
    except Exception as e:
        logger.error(f"定时任务模块运行失败: {e}")
        print(f"❌ 错误: {e}")
        return False


if __name__ == "__main__":
    """
    直接运行此模块时，启动定时任务
    """
    print("⏰ 定时任务模块独立运行")
    print("=" * 60)
    print("请选择运行模式:")
    print("1. 单次运行完整流程")
    print("2. 启动定时任务（每3小时运行一次）")
    print("0. 退出")
    print("-" * 60)

    choice = input("请选择 (0-2): ").strip()

    if choice == "1":
        print("\n🔧 单次运行完整流程")
        scheduler = ScheduledAnalyzer()
        scheduler.run_single_time()

    elif choice == "2":
        print("\n🚀 启动定时任务")
        success = run_scheduler()
        if success:
            print("✅ 定时任务模块执行完成！")
        else:
            print("❌ 定时任务模块执行失败！")

    else:
        print("❌ 用户取消运行")