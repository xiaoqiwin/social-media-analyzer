# 社交媒体热点话题分析系统

## 项目简介

本系统是一个基于Python开发的社交媒体热点话题分析与可视化平台，能够自动爬取热点事件数据，进行情感分析，生成多维度的可视化图表，并集成千问AI提供智能数据分析功能。

## 系统架构

```
social_media_project/
├── main.py              # 主程序入口
├── config.py            # 数据库配置
├── db_init.py           # 数据库初始化模块
├── crawler.py           # 热点数据爬虫模块
├── analyzer.py          # 情感分析模块
├── visualizer.py        # 数据可视化模块
├── reporter.py          # 报告生成模块
├── scheduler.py         # 定时任务模块
├── stopwords.py         # 停用词管理模块
├── stats_query.py       # 统计查询模块
├── utils.py             # 工具函数模块
├── ai_service.py        # 千问AI服务模块
├── ai_server.py         # AI后端服务
├── run.py               # 启动脚本
└── requirements.txt     # 依赖清单
```

## 核心功能

### 1. 数据爬取（crawler.py）
- 自动爬取社交媒体热点事件
- 获取事件标题、热度值、来源、评论等信息
- 支持多平台数据整合

### 2. 情感分析（analyzer.py）
- 基于SnowNLP实现中文情感分析
- 将评论分类为正面、负面、中性
- 支持规则和词典的匹配算法

### 3. 数据可视化（visualizer.py）
生成5大核心图表模块：

#### 3.1 热点话题词云图
- 支持所有事件动态切换
- 词大小按出现频率比例缩放
- 6层严格过滤停用词
- 集成AI智能分析

#### 3.2 历史热点总热度趋势
- 支持选择任意历史日期
- 双Y轴展示热度值和事件数
- 按小时聚合展示完整趋势

#### 3.3 情感分布占比
- 基于规则和词典的匹配算法分类
- 展示正面、负面、中性评论的分布比例
- 玫瑰图饼图直观展示

#### 3.4 TOP10热点事件
- 热度排行榜单
- 横向柱状图展示
- 悬停显示详细信息

#### 3.5 热度-传播-情感三维关联分析
- 多事件对比分析
- 智能洞察面板
- 情感颜色标识
- 支持全选/取消全选/选中TOP10

### 4. 千问AI智能分析（ai_service.py + ai_server.py）
- 集成阿里云千问大模型API
- 支持词云图事件智能分析
- 支持三维关联分析智能解读
- 多角度数据洞察
- 独立进程运行，主程序关闭后仍可继续使用

### 5. 报告生成（reporter.py）
- 自动生成Word格式分析报告
- 包含图表和分析结论
- 支持自定义报告模板

### 6. 定时任务（scheduler.py）
- 每3小时自动运行数据爬取和分析
- 支持自定义调度周期
- 后台守护进程运行

### 7. 停用词管理（stopwords.py）
- 6层严格过滤机制
- 支持自定义停用词表
- 动态更新停用词库

## 技术栈

### 后端技术
- **Python 3.8+**: 核心开发语言
- **PyMySQL**: MySQL数据库连接
- **Flask + Flask-CORS**: AI服务Web框架
- **Schedule**: 定时任务调度

### 数据分析
- **SnowNLP**: 中文情感分析
- **Jieba**: 中文分词
- **Collections.Counter**: 词频统计

### 可视化
- **PyECharts**: 图表生成
- **ECharts 5.x**: 前端图表渲染
- **ECharts-WordCloud**: 词云图插件

### AI服务
- **阿里云千问API**: 大模型分析
- **HTTP/REST API**: 服务通信

### 数据库
- **MySQL 5.7+**: 数据存储
- **InnoDB**: 存储引擎

## 安装部署

### 环境要求
- Python 3.8+
- MySQL 5.7+
- Windows/Linux/MacOS

### 安装步骤

1. **克隆仓库**
```bash
git clone https://gitee.com/li-junqin123/xioaqi.git
cd xioaqi
```

2. **创建虚拟环境**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置数据库**
编辑 `config.py`，设置数据库连接信息：
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'your_password',
    'database': 'social_media',
    'charset': 'utf8mb4'
}
```

5. **初始化数据库**
运行系统，选择选项1初始化数据库

## 使用指南

### 启动系统

```bash
# 方式1：直接运行
python main.py

# 方式2：使用启动脚本（解决编码问题）
python run.py
```

### 主菜单功能

```
==================================================
      社交媒体热点话题分析系统
==================================================
1. 初始化数据库
2. 爬取热点数据
3. 执行情感分析
4. 生成可视化图表
5. 生成分析报告
6. 一键执行全部（按2→3→4→5顺序）
7. 启动定时任务（每3小时自动运行）
8. 查看系统信息
9. 停用词表管理
10. 查询数据库统计
11. 验证系统模块
12. 启动AI分析服务
0. 退出系统
```

### 标准工作流程

1. **首次使用**：运行选项1初始化数据库
2. **数据爬取**：运行选项2获取热点数据
3. **情感分析**：运行选项3分析评论情感
4. **生成图表**：运行选项4生成可视化
5. **查看图表**：打开 `output/charts/index.html`
6. **AI分析**：点击"🤖 AI分析"按钮进行智能问答

### AI功能使用

1. 生成可视化图表后，AI服务自动启动
2. 在浏览器中打开图表页面
3. 选择词云图事件或三维分析事件
4. 点击"🤖 AI分析"按钮
5. 输入问题，AI基于图表数据回答

**示例问题：**
- "这个事件的舆论焦点是什么？"
- "从关键词看，用户的情感倾向如何？"
- "有哪些潜在的舆情风险？"
- "这些事件的热度与传播量有什么关系？"

## 系统验证

运行选项11验证所有模块：
- 基础模块（utils, config）
- 功能模块（db_init, crawler, analyzer, visualizer, reporter）
- 扩展模块（scheduler, stopwords, stats_query, ai_service, ai_server）
- 第三方库（pymysql, requests, jieba, snownlp, pyecharts等）
- 数据库连接状态
- AI服务状态

## 可视化图表说明

### 统一仪表板（index.html）

所有图表集成于单一HTML文件，包含：

#### 词云图模块
- 搜索框实时筛选事件
- 支持按热度/评论数排序
- 点击任意事件即时切换词云图
- 词大小按最小最大词频比例缩放

#### 历史趋势模块
- 日期选择器选择任意历史日期
- 双Y轴折线图（总热度+事件数）
- 支持缩放查看

#### 情感分布模块
- 基于规则和词典的匹配算法分类
- 玫瑰图饼图展示
- 显示总评论数

#### TOP10榜单模块
- 横向柱状图
- 悬停显示完整标题、来源、日期

#### 三维分析模块
- 事件多选卡片（带情感颜色标识）
- 全选/取消全选/选中TOP10
- 智能洞察面板
- 支持按热度或评论数排序

## 数据流程

```
[数据爬取] → [数据存储] → [情感分析] → [数据可视化] → [AI分析]
     ↑                                              ↓
     └──────────── [定时任务] ←─────────────────────┘
```

## 数据库结构

### 核心表
- **hot_events**: 热点事件表
- **comments**: 评论表
- **sentiment_results**: 情感分析结果表

### 字段说明
- **hot_events**: id, title, hot_value, source, crawl_date, created_at
- **comments**: id, event_id, content, sentiment_label, like_count, created_at
- **sentiment_results**: id, event_id, positive_count, negative_count, neutral_count, total_count

## 配置说明

### 数据库配置（config.py）
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'your_password',
    'database': 'social_media',
    'charset': 'utf8mb4'
}
```

### AI服务配置（ai_service.py）
```python
QWEN_API_KEY = "sk-0e169d97dfd0423d852c9351e52075a5"
QWEN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
```

## 常见问题

### Q1: 系统无法启动
**A**: 检查Python版本（需3.8+），安装所有依赖：`pip install -r requirements.txt`

### Q2: 数据库连接失败
**A**: 检查config.py中的数据库配置，确保MySQL服务已启动

### Q3: 三维分析没有数据
**A**: 需要先运行选项2（爬取数据）和选项3（情感分析），确保数据库中有评论数据

### Q4: AI功能无法使用
**A**: 
1. 确保已生成可视化图表（选项4）
2. AI服务作为独立进程运行，检查是否启动
3. 查看浏览器控制台是否有错误信息

### Q5: 终端显示乱码
**A**: Windows系统编码问题，使用 `python run.py` 启动，或在CMD中先执行 `chcp 65001`

## 版本历史

### v5.0 (当前版本)
- 统一仪表板，单HTML文件包含所有图表
- 历史趋势支持选择任意日期
- 词云图支持所有事件动态切换
- 集成千问AI智能分析
- AI服务作为独立进程运行

### v4.0
- 交互式三维关联分析
- 智能洞察面板
- 图表集成查看器

### v3.0
- 增强停用词过滤
- 情感分析优化
- 多维度可视化

## 作者信息

- **作者**: Python项目架构导师
- **日期**: 2026-05-05
- **仓库**: https://gitee.com/li-junqin123/xioaqi.git

## 许可证

MIT License

## 致谢

- 阿里云千问大模型API
- PyECharts团队
- SnowNLP中文情感分析库
- Jieba中文分词库
