# -*- coding: utf-8 -*-
"""
自动更新数据并部署脚本
功能：
1. 运行数据爬取和分析
2. 生成新的HTML报告
3. 自动提交到Git并推送到GitHub
4. 触发Netlify自动部署

用法：
    python auto_update_and_deploy.py

前置要求：
    1. 安装Git: https://git-scm.com/download/win
    2. 创建GitHub仓库
    3. 配置GitHub仓库地址到 GITHUB_REPO_URL
    4. Netlify已连接GitHub仓库
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# ==================== 配置区域 ====================
# 请修改为你的GitHub仓库地址
GITHUB_REPO_URL = "https://github.com/xiaoqiwin/social-media-analyzer.git"
BRANCH = "main"

# 是否自动运行数据更新（爬取+分析）
AUTO_UPDATE_DATA = True

# 数据更新后要运行的主程序选项
# 选项说明（来自main.py）：
# 1. 初始化数据库
# 2. 爬取热点数据
# 3. 情感分析
# 4. 生成可视化图表
# 5. 生成报告
# 6. 启动AI服务
# 7. 设置定时任务
# 8. 退出
UPDATE_OPTIONS = ['2', '3', '4', '5']  # 爬取、分析、可视化、报告
# =================================================


def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_git_installed():
    """检查Git是否安装"""
    success, stdout, stderr = run_command("git --version")
    if success:
        print(f"✅ Git已安装: {stdout.strip()}")
        return True
    else:
        print("❌ Git未安装，请先安装Git: https://git-scm.com/download/win")
        print("   安装后请重启终端或IDE")
        return False


def init_git_repo(project_dir):
    """初始化Git仓库"""
    git_dir = os.path.join(project_dir, ".git")
    if os.path.exists(git_dir):
        print("✅ Git仓库已存在")
        return True

    print("📝 初始化Git仓库...")
    success, stdout, stderr = run_command("git init", cwd=project_dir)
    if success:
        print("✅ Git仓库初始化成功")
        # 配置Git用户信息（如果未配置）
        run_command('git config user.email "auto-deploy@example.com"', cwd=project_dir)
        run_command('git config user.name "Auto Deploy"', cwd=project_dir)
        return True
    else:
        print(f"❌ 初始化失败: {stderr}")
        return False


def setup_remote(project_dir, repo_url):
    """设置远程仓库"""
    success, stdout, stderr = run_command("git remote -v", cwd=project_dir)
    if "origin" in stdout:
        print("✅ 远程仓库已配置")
        return True

    print(f"📝 添加远程仓库...")
    success, stdout, stderr = run_command(
        f"git remote add origin {repo_url}",
        cwd=project_dir
    )
    if success:
        print("✅ 远程仓库添加成功")
        return True
    else:
        print(f"❌ 添加远程仓库失败: {stderr}")
        return False


def ensure_branch_exists(project_dir, branch_name):
    """确保分支存在，如果不存在则创建"""
    # 检查当前分支
    success, stdout, _ = run_command("git branch --show-current", cwd=project_dir)
    current_branch = stdout.strip() if success else ""
    
    if not current_branch:
        # 没有分支，需要先创建初始提交，然后创建分支
        print(f"📝 首次提交，创建 {branch_name} 分支...")
        
        # 先创建一个空的初始提交（如果还没有提交）
        success, stdout, stderr = run_command("git log --oneline -1", cwd=project_dir)
        if not success:
            print("📝 创建初始提交...")
            run_command("git add .", cwd=project_dir)
            run_command('git commit -m "Initial commit"', cwd=project_dir)
        
        # 创建并切换到目标分支
        success, _, stderr = run_command(
            f"git checkout -b {branch_name}",
            cwd=project_dir
        )
        if success:
            print(f"✅ 分支 {branch_name} 创建成功")
            return True
        else:
            print(f"❌ 创建分支失败: {stderr}")
            return False
    elif current_branch != branch_name:
        # 切换到目标分支
        print(f"📝 切换到 {branch_name} 分支...")
        success, _, stderr = run_command(
            f"git checkout -b {branch_name}",
            cwd=project_dir
        )
        if success:
            print(f"✅ 已切换到 {branch_name} 分支")
            return True
        else:
            print(f"❌ 切换分支失败: {stderr}")
            return False
    else:
        print(f"✅ 当前已在 {branch_name} 分支")
        return True


def commit_and_push(project_dir, message=None):
    """提交并推送代码到GitHub"""
    if message is None:
        message = f"更新数据: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # 确保分支存在
    if not ensure_branch_exists(project_dir, BRANCH):
        return False

    # 添加所有更改
    print("📝 添加更改到暂存区...")
    success, _, stderr = run_command("git add .", cwd=project_dir)
    if not success:
        print(f"❌ git add 失败: {stderr}")
        return False

    # 检查是否有更改要提交
    success, stdout, _ = run_command("git status --porcelain", cwd=project_dir)
    if not stdout.strip():
        print("ℹ️ 没有需要提交的更改")
        return True

    # 提交更改
    print(f"📝 提交更改: {message}")
    success, _, stderr = run_command(
        f'git commit -m "{message}"',
        cwd=project_dir
    )
    if not success:
        # 可能是没有配置用户信息
        if "user.name" in stderr or "user.email" in stderr:
            print("📝 配置Git用户信息...")
            run_command('git config user.email "auto-deploy@example.com"', cwd=project_dir)
            run_command('git config user.name "Auto Deploy"', cwd=project_dir)
            # 重新提交
            success, _, stderr = run_command(
                f'git commit -m "{message}"',
                cwd=project_dir
            )
        if not success:
            print(f"❌ git commit 失败: {stderr}")
            return False

    print("✅ 提交成功")

    # 推送到远程
    print(f"📝 推送到远程仓库 ({BRANCH}分支)...")
    success, _, stderr = run_command(
        f"git push -u origin {BRANCH}",
        cwd=project_dir
    )
    if success:
        print("✅ 推送成功！")
        return True
    else:
        print(f"❌ 推送失败: {stderr}")
        # 尝试强制推送（仅首次）
        print("📝 尝试强制推送...")
        success, _, stderr = run_command(
            f"git push -u origin {BRANCH} --force",
            cwd=project_dir
        )
        if success:
            print("✅ 强制推送成功！")
            return True
        else:
            print(f"❌ 强制推送也失败: {stderr}")
            return False


def deploy():
    """主部署函数"""
    print("=" * 60)
    print("🚀 社交媒体热点分析系统 - 自动更新与部署")
    print("=" * 60)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📁 项目目录: {project_dir}")
    print(f"🔗 GitHub仓库: {GITHUB_REPO_URL}")
    print(f"🌐 Netlify网站: https://social-mediaanalyzer.netlify.app/")
    print("=" * 60)

    # 检查Git
    if not check_git_installed():
        print("\n❌ 请先安装Git后再运行此脚本")
        print("   下载地址: https://git-scm.com/download/win")
        return False

    # 初始化仓库
    if not init_git_repo(project_dir):
        return False

    # 设置远程仓库
    if not setup_remote(project_dir, GITHUB_REPO_URL):
        return False

    # 提示用户手动更新数据
    print("\n" + "=" * 60)
    print("📊 数据更新")
    print("=" * 60)
    print("⚠️  自动数据更新需要手动配置")
    print("   建议步骤：")
    print("   1. 运行 main.py 更新数据")
    print("   2. 确认 output/index.html 已更新")
    print("   3. 然后运行此脚本进行部署")
    print("=" * 60)

    # 询问是否继续部署
    try:
        response = input("\n是否继续部署? (y/n): ").strip().lower()
        if response != 'y':
            print("已取消部署")
            return False
    except KeyboardInterrupt:
        print("\n已取消部署")
        return False

    # 提交并推送
    if commit_and_push(project_dir):
        print("\n" + "=" * 60)
        print("🎉 部署完成！")
        print(f"🌐 网站地址: https://social-mediaanalyzer.netlify.app/")
        print("⏱️  Netlify部署通常需要1-2分钟")
        print("=" * 60)
        return True
    else:
        print("\n❌ 部署失败，请检查错误信息")
        return False


if __name__ == "__main__":
    deploy()
