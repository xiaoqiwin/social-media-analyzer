# -*- coding: utf-8 -*-
"""
自动部署脚本
功能：生成HTML后自动提交到Git并推送到GitHub，触发Netlify自动部署
用法：python deploy.py
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# 配置
GITHUB_REPO_URL = "https://github.com/xiaoqiwin/social-media-analyzer.git"  # 请修改为你的GitHub仓库地址
BRANCH = "main"


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
        return True
    else:
        print(f"❌ 初始化失败: {stderr}")
        return False


def setup_remote(project_dir, repo_url):
    """设置远程仓库"""
    # 检查是否已有远程仓库
    success, stdout, stderr = run_command("git remote -v", cwd=project_dir)
    if "origin" in stdout:
        print("✅ 远程仓库已配置")
        return True

    print(f"📝 添加远程仓库: {repo_url}")
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


def commit_and_push(project_dir, message=None):
    """提交并推送代码"""
    if message is None:
        message = f"更新数据: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

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
        print("✅ 推送成功！Netlify将自动部署最新版本。")
        return True
    else:
        print(f"❌ 推送失败: {stderr}")
        print("💡 提示: 如果是第一次推送，可能需要先设置分支:")
        print(f"   git branch -M {BRANCH}")
        print(f"   git push -u origin {BRANCH}")
        return False


def deploy():
    """主部署函数"""
    print("=" * 60)
    print("🚀 社交媒体热点分析系统 - 自动部署工具")
    print("=" * 60)

    # 获取项目目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📁 项目目录: {project_dir}")

    # 检查Git
    if not check_git_installed():
        return False

    # 初始化仓库
    if not init_git_repo(project_dir):
        return False

    # 设置远程仓库
    if not setup_remote(project_dir, GITHUB_REPO_URL):
        return False

    # 提交并推送
    if commit_and_push(project_dir):
        print("\n" + "=" * 60)
        print("🎉 部署完成！")
        print(f"🌐 网站地址: https://deluxe-zabaione-3721cb.netlify.app/")
        print("⏱️  Netlify部署通常需要1-2分钟")
        print("=" * 60)
        return True
    else:
        print("\n❌ 部署失败，请检查错误信息")
        return False


if __name__ == "__main__":
    deploy()
