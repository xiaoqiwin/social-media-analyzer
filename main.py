# -*- coding: utf-8 -*-
"""
社交媒体热点话题分析系统 - 主程序
功能：提供命令行交互菜单，协调各模块运行
作者：Python项目架构导师
日期：2026-05-02
"""

import os
import sys

# 修复Windows控制台UTF-8编码问题
if sys.platform == 'win32':
    import io
    import subprocess
    # 设置Windows代码页为UTF-8
    subprocess.run(['cmd', '/c', 'chcp', '65001'], capture_output=True)
    # 设置Python标准输出编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import time
import threading
import subprocess
from typing import Optional

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入工具模块
try:
    import utils
    from config import get_db_connection, test_connection

    print("✅ 基础模块导入成功")
except ImportError as e:
    print(f"❌ 基础模块导入失败: {e}")
    sys.exit(1)

# 导入各功能模块
try:
    import db_init
    import crawler
    import analyzer
    import visualizer

    import reporter

    MODULES_AVAILABLE = True
    print("✅ 功能模块导入成功")
except ImportError as e:
    print(f"⚠️ 功能模块导入失败: {e}")
    print("请确保所有模块文件都存在")
    MODULES_AVAILABLE = False

# 导入定时任务模块
try:
    import scheduler

    SCHEDULER_AVAILABLE = True
    print("✅ 定时任务模块导入成功")
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("⚠️ scheduler.py模块导入失败")

# 导入停用词模块
try:
    from stopwords import get_stopwords_manager, clean_text_with_stopwords

    STOPWORDS_AVAILABLE = True
    print("✅ 停用词模块导入成功")
except ImportError:
    STOPWORDS_AVAILABLE = False
    print("⚠️ stopwords模块导入失败")

# 导入统计查询模块
try:
    from stats_query import run_database_query, simple_query_total_data

    STATS_QUERY_AVAILABLE = True
    print("✅ 统计查询模块导入成功")
except ImportError as e:
    STATS_QUERY_AVAILABLE = False
    print(f"⚠️ stats_query模块导入失败: {e}")
    print("请确保 stats_query.py 文件存在")

# 导入AI服务模块
try:
    from ai_service import analyze_wordcloud, analyze_3d_chart, call_qwen_ai

    AI_SERVICE_AVAILABLE = True
    print("✅ AI服务模块导入成功")
except ImportError as e:
    AI_SERVICE_AVAILABLE = False
    print(f"⚠️ AI服务模块导入失败: {e}")

# 导入AI服务器模块
try:
    from ai_server import start_ai_server

    AI_SERVER_AVAILABLE = True
    print("✅ AI服务器模块导入成功")
except ImportError as e:
    AI_SERVER_AVAILABLE = False
    print(f"⚠️ AI服务器模块导入失败: {e}")

# 导入自动部署模块
try:
    from auto_update_and_deploy import commit_and_push, run_command

    DEPLOY_AVAILABLE = True
    print("✅ 自动部署模块导入成功")
except ImportError as e:
    DEPLOY_AVAILABLE = False
    print(f"⚠️ 自动部署模块导入失败: {e}")

class SocialMediaHotspotSystem:
    """社交媒体热点话题分析系统主类"""

    def __init__(self):
        """初始化系统"""
        self.logger = utils.get_logger(__name__)
        self.running = True
        self.stats = {}  # 运行统计
        self.scheduler = None  # 定时任务对象
        self.ai_process = None  # AI服务进程
        self.ai_server_running = False  # AI服务状态

    def print_header(self):
        """打印系统标题"""
        print("\n" + "=" * 50)
        print("      社交媒体热点话题分析系统")
        print("=" * 50)

    def print_menu(self):
        """打印主菜单"""
        self.print_header()
        print("1. 初始化数据库")
        print("2. 爬取热点数据")
        print("3. 执行情感分析")
        print("4. 生成可视化图表")
        print("5. 生成分析报告")
        print("6. 一键执行全部（按2→3→4→5顺序）")
        print("7. 启动定时任务（每3小时自动运行）")
        print("8. 查看系统信息")
        print("9. 停用词表管理")
        print("10. 查询数据库统计")
        print("11. 验证系统模块")
        print("12. 启动AI分析服务")
        print("13. 部署网站到Netlify")
        print("0. 退出系统")
        print("-" * 50)

        # 如果定时任务正在运行，显示状态
        if self.scheduler and self.scheduler.is_running:
            print(f"⏰ 定时任务状态: 正在运行")
            if self.scheduler.next_run_time:
                next_time = self.scheduler.next_run_time.strftime('%H:%M:%S')
                print(f"⏰ 下一次运行: 今天 {next_time}")

        # 显示AI服务状态
        if self.ai_server_running:
            print(f"🤖 AI服务状态: 正在运行 (http://localhost:5000)")

    def get_user_choice(self) -> str:
        """获取用户选择"""
        try:
            choice = input("请选择操作 (0-13): ").strip()
            return choice
        except (EOFError, KeyboardInterrupt):
            return "0"  # 用户按Ctrl+C或Ctrl+Z，选择退出

    def wait_for_enter(self, message: str = "按Enter键继续..."):
        """等待用户按Enter键"""
        try:
            input(message)
        except (EOFError, KeyboardInterrupt):
            pass

    def run_db_init(self) -> bool:
        """运行数据库初始化"""
        self.logger.info("开始初始化数据库...")
        start_time = time.time()

        try:
            # 检查数据库连接
            if not test_connection():
                print("❌ 数据库连接失败，请检查config.py配置")
                return False

            # 运行数据库初始化
            success = db_init.run_db_init()

            if success:
                elapsed = time.time() - start_time
                self.logger.info(f"数据库初始化完成，耗时: {elapsed:.2f}秒")
                print("✅ 数据库初始化成功！")
            else:
                print("❌ 数据库初始化失败")

            return success

        except Exception as e:
            self.logger.error(f"数据库初始化过程中出错: {e}")
            print(f"❌ 错误: {e}")
            return False

    def run_crawler(self) -> bool:
        """运行爬虫模块"""
        self.logger.info("开始爬取热点数据...")
        start_time = time.time()

        try:
            # 检查数据库连接
            if not test_connection():
                print("❌ 数据库连接失败，请检查config.py配置")
                return False

            # 运行爬虫
            success = crawler.run_crawler()

            if success:
                elapsed = time.time() - start_time
                self.logger.info(f"数据爬取完成，耗时: {elapsed:.2f}秒")
                print("✅ 数据爬取成功！")
            else:
                print("❌ 数据爬取失败")

            return success

        except Exception as e:
            self.logger.error(f"数据爬取过程中出错: {e}")
            print(f"❌ 错误: {e}")
            return False

    def run_analyzer(self) -> bool:
        """运行情感分析模块"""
        self.logger.info("开始执行情感分析...")
        start_time = time.time()

        try:
            # 检查数据库连接
            if not test_connection():
                print("❌ 数据库连接失败，请检查config.py配置")
                return False

            # 运行情感分析
            success = analyzer.run_analyzer()

            if success:
                elapsed = time.time() - start_time
                self.logger.info(f"情感分析完成，耗时: {elapsed:.2f}秒")
                print("✅ 情感分析成功！")
            else:
                print("❌ 情感分析失败")

            return success

        except Exception as e:
            self.logger.error(f"情感分析过程中出错: {e}")
            print(f"❌ 错误: {e}")
            return False

    def start_ai_server(self) -> bool:
        """启动AI分析服务（作为独立子进程）"""
        if not AI_SERVER_AVAILABLE:
            print("⚠️ AI服务器模块不可用，无法启动AI服务")
            return False

        if self.ai_server_running:
            print("✅ AI服务已经在运行中")
            return True

        try:
            print("🤖 正在启动AI分析服务...")

            # 使用子进程启动AI服务，这样即使主程序结束，AI服务也能继续运行
            import sys
            python_exe = sys.executable
            ai_server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_server.py')

            # 启动独立子进程
            self.ai_process = subprocess.Popen(
                [python_exe, ai_server_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )

            self.ai_server_running = True

            print("✅ AI分析服务已启动！")
            print("   服务地址: http://localhost:5000")
            print("   在可视化页面中可以使用AI分析功能")
            print("   💡 提示: AI服务作为独立进程运行，即使关闭主程序也能继续使用")
            return True

        except Exception as e:
            self.logger.error(f"启动AI服务失败: {e}")
            print(f"❌ 启动AI服务失败: {e}")
            return False

    def stop_ai_server(self):
        """停止AI服务"""
        if self.ai_server_running and hasattr(self, 'ai_process'):
            try:
                self.ai_process.terminate()
                self.ai_server_running = False
                print("🛑 AI分析服务已停止")
            except Exception as e:
                print(f"⚠️ 停止AI服务时出错: {e}")

    def deploy_website(self) -> bool:
        """部署网站到Netlify"""
        if not DEPLOY_AVAILABLE:
            print("❌ 自动部署模块不可用")
            return False

        print("\n" + "=" * 60)
        print("🚀 部署网站到Netlify")
        print("=" * 60)
        print("此操作将:")
        print("  1. 提交所有更改到Git")
        print("  2. 推送到GitHub仓库")
        print("  3. 触发Netlify自动部署")
        print("=" * 60)

        try:
            project_dir = os.path.dirname(os.path.abspath(__file__))
            success = commit_and_push(project_dir)

            if success:
                print("\n✅ 部署成功！")
                print("   网站将在1-2分钟后自动更新")
                print("   访问地址: https://social-mediaanalyzer.netlify.app/")
            else:
                print("\n❌ 部署失败，请检查错误信息")

            return success

        except Exception as e:
            self.logger.error(f"部署过程中出错: {e}")
            print(f"❌ 部署失败: {e}")
            return False

    def run_visualizer(self) -> bool:
        """运行可视化模块"""
        self.logger.info("开始生成可视化图表...")
        start_time = time.time()

        try:
            # 确保输出目录存在
            utils.ensure_output_dir(['charts'])

            # 检查数据库连接
            if not test_connection():
                print("❌ 数据库连接失败，请检查config.py配置")
                return False

            # 运行可视化
            success = visualizer.run_visualizer()

            if success:
                elapsed = time.time() - start_time
                self.logger.info(f"可视化图表生成完成，耗时: {elapsed:.2f}秒")
                print("✅ 可视化图表生成成功！")
                print(f"图表已保存到: {os.path.abspath('output/charts')}")

                # 自动生成可视化后启动AI服务
                if AI_SERVER_AVAILABLE:
                    print("\n🤖 正在启动AI分析服务...")
                    self.start_ai_server()
                    print("💡 提示: 在浏览器中打开图表页面，点击 '🤖 AI分析' 按钮即可使用AI功能")
                else:
                    print("⚠️ AI服务模块不可用，无法启动AI分析功能")

                # 询问是否部署到Netlify
                if DEPLOY_AVAILABLE:
                    print("\n🚀 是否立即部署网站到Netlify？")
                    confirm = input("   部署后其他用户可以看到最新数据 (y/n, 默认n): ").strip().lower()
                    if confirm == 'y':
                        self.deploy_website()
            else:
                print("❌ 可视化图表生成失败")

            return success

        except Exception as e:
            self.logger.error(f"可视化过程中出错: {e}")
            print(f"❌ 错误: {e}")
            return False

    def run_reporter(self) -> bool:
        """运行报告生成模块"""
        self.logger.info("开始生成分析报告...")
        start_time = time.time()

        try:
            # 确保输出目录存在
            utils.ensure_output_dir(['reports'])

            # 检查数据库连接
            if not test_connection():
                print("❌ 数据库连接失败，请检查config.py配置")
                return False

            # 运行报告生成
            success = reporter.run_reporter()

            if success:
                elapsed = time.time() - start_time
                self.logger.info(f"分析报告生成完成，耗时: {elapsed:.2f}秒")
                print("✅ 分析报告生成成功！")
                print(f"报告已保存到: {os.path.abspath('output/reports')}")
            else:
                print("❌ 分析报告生成失败")

            return success

        except Exception as e:
            self.logger.error(f"报告生成过程中出错: {e}")
            print(f"❌ 错误: {e}")
            return False

    def run_all(self) -> bool:
        """一键执行全部模块（2→3→4→5）"""
        self.logger.info("开始一键执行全部模块...")

        steps = [
            ("爬取热点数据", self.run_crawler),
            ("执行情感分析", self.run_analyzer),
            ("生成可视化图表", self.run_visualizer),
            ("生成分析报告", self.run_reporter)
        ]

        all_success = True

        for step_name, step_func in steps:
            print(f"\n{'=' * 30}")
            print(f"步骤: {step_name}")
            print(f"{'=' * 30}")

            # 询问用户是否继续
            if step_name != "爬取热点数据":  # 第一步自动执行
                confirm = input(f"是否执行 {step_name}？(y/n, 默认y): ").strip().lower()
                if confirm == 'n':
                    print(f"跳过 {step_name}")
                    continue

            # 执行步骤
            if not step_func():
                all_success = False
                print(f"⚠️ {step_name} 失败，是否继续？")
                confirm = input("继续执行后续步骤？(y/n, 默认y): ").strip().lower()
                if confirm == 'n':
                    break

            # 步骤间暂停
            if step_func != steps[-1][1]:  # 不是最后一步
                self.wait_for_enter("按Enter键继续下一步...")

        if all_success:
            print("\n🎉 所有模块执行完成！")
        else:
            print("\n⚠️ 部分模块执行失败")

        return all_success

    def run_scheduler(self) -> bool:
        """启动定时任务"""
        if not SCHEDULER_AVAILABLE:
            print("❌ 定时任务模块不可用")
            return False

        print("⏰ 启动定时任务系统")
        print("=" * 60)
        print("定时任务将每3小时自动运行一次完整流程:")
        print("  1. 爬取热点数据")
        print("  2. 执行情感分析")
        print("  3. 生成可视化图表")
        print("  4. 生成分析报告")
        print("=" * 60)

        # 创建定时分析器
        self.scheduler = scheduler.ScheduledAnalyzer(interval_hours=3)

        # 在后台线程中运行定时任务
        def run_in_background():
            self.scheduler.run_continuously()

        scheduler_thread = threading.Thread(target=run_in_background, daemon=True)
        scheduler_thread.start()

        print("✅ 定时任务已启动，正在后台运行...")
        print("💡 定时任务日志将保存到: scheduler.log")
        print("⚠️ 注意: 定时任务会在后台持续运行，直到退出程序")

        return True

    def show_scheduler_status(self):
        """显示定时任务状态"""
        if not self.scheduler:
            print("⏰ 定时任务: 未启动")
            return

        status = self.scheduler.get_status()

        print("\n" + "=" * 60)
        print("⏰ 定时任务状态")
        print("=" * 60)

        if status["is_running"]:
            print("✅ 状态: 正在运行")
        else:
            print("⏸️ 状态: 已停止")

        print(f"⏰ 执行间隔: 每 {status['interval_hours']} 小时")
        print(f"📊 运行统计: 总 {status['run_count']} 次")
        print(f"          成功 {status['success_count']} 次")
        print(f"          失败 {status['fail_count']} 次")

        if status["last_run_time"]:
            last_time = status["last_run_time"].strftime('%Y-%m-%d %H:%M:%S')
            print(f"⏰ 上次运行: {last_time}")

        if status["is_running"] and status["next_run_time"]:
            next_time = status["next_run_time"].strftime('%Y-%m-%d %H:%M:%S')
            print(f"⏰ 下次运行: {next_time}")

            if "time_until_next_minutes" in status:
                minutes = status["time_until_next_minutes"]
                hours = minutes // 60
                mins = minutes % 60
                print(f"⏰ 距离下次: {hours}小时 {mins}分钟")

        print("=" * 60)

        # 显示最近几次运行记录
        print("\n📋 最近运行记录:")
        print("-" * 40)
        try:
            with open("scheduler.log", "r", encoding="utf-8") as f:
                lines = f.readlines()[-20:]  # 读取最后20行
                for line in lines:
                    print(line.rstrip())
        except FileNotFoundError:
            print("暂无运行记录")

        self.wait_for_enter()

    def verify_all_modules(self):
        """验证所有系统模块"""
        print("\n" + "=" * 60)
        print("🔍 系统模块验证")
        print("=" * 60)

        # 基础模块
        print("\n📦 基础模块:")
        modules_base = {
            'utils': '工具模块',
            'config': '配置模块',
        }
        for module, desc in modules_base.items():
            try:
                __import__(module)
                print(f"  ✅ {module}.py - {desc}")
            except ImportError as e:
                print(f"  ❌ {module}.py - {desc}: {e}")

        # 功能模块
        print("\n🔧 功能模块:")
        modules_func = {
            'db_init': '数据库初始化',
            'crawler': '爬虫模块',
            'analyzer': '情感分析',
            'visualizer': '可视化图表',
            'reporter': '报告生成',
        }
        for module, desc in modules_func.items():
            try:
                __import__(module)
                print(f"  ✅ {module}.py - {desc}")
            except ImportError as e:
                print(f"  ❌ {module}.py - {desc}: {e}")

        # 扩展模块
        print("\n🚀 扩展模块:")
        modules_ext = {
            'scheduler': '定时任务',
            'stopwords': '停用词管理',
            'stats_query': '统计查询',
            'ai_service': 'AI服务',
            'ai_server': 'AI服务器',
        }
        for module, desc in modules_ext.items():
            try:
                __import__(module)
                print(f"  ✅ {module}.py - {desc}")
            except ImportError as e:
                print(f"  ❌ {module}.py - {desc}: {e}")

        # 第三方库
        print("\n📚 第三方库:")
        libraries = {
            'pymysql': 'MySQL数据库驱动',
            'requests': 'HTTP请求',
            'jieba': '中文分词',
            'snownlp': '情感分析',
            'pyecharts': '图表生成',
            'docx': 'Word文档',
            'flask': 'Web服务',
            'flask_cors': '跨域支持',
            'schedule': '定时调度',
        }
        for lib, desc in libraries.items():
            try:
                __import__(lib)
                print(f"  ✅ {lib} - {desc}")
            except ImportError:
                print(f"  ❌ {lib} - {desc}: 未安装")

        # 数据库连接
        print("\n🗄️ 数据库连接:")
        if test_connection():
            print("  ✅ 数据库连接: 正常")
        else:
            print("  ❌ 数据库连接: 失败")

        # AI服务状态
        print("\n🤖 AI服务状态:")
        if AI_SERVER_AVAILABLE:
            print("  ✅ AI服务器模块: 已加载")
            if self.ai_server_running:
                print("  ✅ AI服务: 正在运行 (http://localhost:5000)")
            else:
                print("  ⏸️ AI服务: 未启动")
        else:
            print("  ❌ AI服务器模块: 未加载")

        print("\n" + "=" * 60)
        self.wait_for_enter()

    def show_system_info(self):
        """显示系统信息"""
        self.print_header()
        print("系统信息:")
        print(f"  项目目录: {os.path.abspath('.')}")
        print(f"  Python版本: {sys.version.split()[0]}")
        print(f"  操作系统: {os.name}")
        print(f"  输出目录: {os.path.abspath('output')}")

        # 检查各模块
        print("\n模块状态:")
        modules = ['db_init', 'crawler', 'analyzer', 'visualizer', 'reporter']
        for module in modules:
            try:
                __import__(module)
                print(f"  ✅ {module}.py: 已加载")
            except ImportError:
                print(f"  ❌ {module}.py: 未找到")

        # 检查数据库连接
        print("\n数据库状态:")
        if test_connection():
            print("  ✅ 数据库连接: 正常")
        else:
            print("  ❌ 数据库连接: 失败")

        # 检查定时任务状态
        print("\n定时任务状态:")
        if SCHEDULER_AVAILABLE:
            print("  ✅ scheduler.py: 已加载")
        else:
            print("  ❌ scheduler.py: 未找到")

        if self.scheduler:
            status = self.scheduler.get_status()
            if status["is_running"]:
                print("  ✅ 定时任务: 正在运行")
            else:
                print("  ⏸️ 定时任务: 已停止")

        # AI服务状态
        print("\nAI服务状态:")
        if AI_SERVER_AVAILABLE:
            print("  ✅ AI服务器模块: 已加载")
            if self.ai_server_running:
                print("  ✅ AI服务: 正在运行 (http://localhost:5000)")
            else:
                print("  ⏸️ AI服务: 未启动")
        else:
            print("  ❌ AI服务器模块: 未加载")

        self.wait_for_enter()

    def show_stopwords_info(self):
        """显示停用词信息"""
        print("\n" + "=" * 60)
        print("📋 停用词表信息")
        print("=" * 60)

        if STOPWORDS_AVAILABLE:
            try:
                manager = get_stopwords_manager()
                domains = manager.get_domain_list()
                print(f"可用领域: {', '.join(domains)}")
                print()

                for domain in domains:
                    count = manager.get_domain_size(domain)
                    print(f"  {domain}: {count} 个停用词")

                total_count = manager.get_total_size()
                print(f"\n总停用词数（去重）: {total_count} 个")

                # 测试停用词功能
                test_text = "今天微博热搜上有个话题很有趣，网友们都在讨论#这个话题#，哈哈！"
                cleaned = clean_text_with_stopwords(test_text, ["common", "weibo"])
                print(f"\n测试文本: {test_text}")
                print(f"清洗后: {cleaned}")

            except Exception as e:
                print(f"获取停用词信息失败: {e}")
        else:
            print("❌ 停用词模块不可用")
            print("请确保stopwords.py文件存在")

        self.wait_for_enter()

    def run(self):
        """运行主系统"""
        if not MODULES_AVAILABLE:
            print("❌ 系统初始化失败，缺少必要模块")
            print("请确保以下文件存在:")
            print("  - db_init.py, crawler.py, analyzer.py")
            print("  - visualizer.py, reporter.py")
            return

        self.logger.info("社交媒体热点话题分析系统启动")

        while self.running:
            try:
                self.print_menu()
                choice = self.get_user_choice()

                if choice == "0":
                    # 停止定时任务
                    if self.scheduler and self.scheduler.is_running:
                        self.scheduler.stop()
                    self.running = False

                elif choice == "1":
                    self.run_db_init()
                    self.wait_for_enter()

                elif choice == "2":
                    self.run_crawler()
                    self.wait_for_enter()

                elif choice == "3":
                    self.run_analyzer()
                    self.wait_for_enter()

                elif choice == "4":
                    self.run_visualizer()
                    self.wait_for_enter()

                elif choice == "5":
                    self.run_reporter()
                    self.wait_for_enter()

                elif choice == "6":
                    self.run_all()
                    self.wait_for_enter()

                elif choice == "7":
                    if self.scheduler and self.scheduler.is_running:
                        print("⚠️ 定时任务已经在运行中")
                        self.show_scheduler_status()
                    else:
                        self.run_scheduler()
                        self.wait_for_enter("按Enter键返回主菜单，定时任务将在后台继续运行...")

                elif choice == "8":
                    self.show_system_info()

                elif choice == "9":  # 新增停用词管理
                    self.show_stopwords_info()

                elif choice == "10":  # 新增数据库查询选项
                    if STATS_QUERY_AVAILABLE:
                        # 询问查询方式
                        print("\n📊 数据库统计查询")
                        print("=" * 60)
                        print("请选择查询方式:")
                        print("  1. 快速查询（仅显示总量）")
                        print("  2. 详细统计报告（包含趋势和分布）")

                        query_choice = input("请选择 (1-2, 默认1): ").strip()

                        if query_choice == "2":
                            # 运行详细统计
                            run_database_query()
                        else:
                            # 运行快速查询
                            simple_query_total_data()

                        self.wait_for_enter()
                    else:
                        print("❌ 数据库统计查询模块不可用")
                        self.wait_for_enter()

                elif choice == "11":  # 验证系统模块
                    self.verify_all_modules()

                elif choice == "12":  # 启动AI分析服务
                    if AI_SERVER_AVAILABLE:
                        self.start_ai_server()
                    else:
                        print("❌ AI服务器模块不可用")
                    self.wait_for_enter()

                elif choice == "13":  # 部署网站到Netlify
                    self.deploy_website()
                    self.wait_for_enter()

                else:
                    print("❌ 无效选择，请重新输入")
                    self.wait_for_enter()

            except KeyboardInterrupt:
                print("\n检测到键盘中断 (Ctrl+C)，正在安全退出...")
                if self.scheduler and self.scheduler.is_running:
                    self.scheduler.stop()
                if self.ai_server_running:
                    self.stop_ai_server()
                self.running = False
            except Exception as e:
                self.logger.error(f"主循环发生未知错误: {e}")
                print(f"❌ 发生未知系统错误: {e}")
                self.wait_for_enter("按Enter键返回主菜单...")

        self.logger.info("社交媒体热点话题分析系统关闭")
        print("\n" + "=" * 50)
        print("      感谢使用，再见！")
        print("=" * 50)


def main():
    """主函数"""
    system = SocialMediaHotspotSystem()
    system.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断程序")
        print("感谢使用，再见！")
    except Exception as e:
        print(f"\n❌ 系统启动失败: {e}")
        print("请检查config.py配置和各模块文件")