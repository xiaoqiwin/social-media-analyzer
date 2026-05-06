"""
千问AI服务模块
提供图表数据分析和智能问答功能
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
import urllib.request
import urllib.error
from datetime import datetime

logger = logging.getLogger(__name__)

# 千问AI API配置 - 优先从环境变量读取，否则使用默认值
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "sk-0e169d97dfd0423d852c9351e52075a5")
QWEN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"


def get_current_time_info() -> str:
    """获取当前时间信息，用于传递给AI"""
    now = datetime.now()
    return f"""
【系统实时信息】
- 当前日期时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}
- 今天是：{now.strftime('%Y年%m月%d日')}
- 当前时间：{now.strftime('%H:%M:%S')}

注意：以上时间是系统的实时时间，请基于此时间回答用户关于时间的问题。
"""


def call_qwen_ai(messages: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
    """
    调用千问AI API

    Args:
        messages: 对话消息列表
        temperature: 温度参数，控制回复的创造性

    Returns:
        Optional[str]: AI回复内容
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {QWEN_API_KEY}"
        }

        data = {
            "model": "qwen-turbo",
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": temperature,
                "result_format": "message"
            }
        }

        req = urllib.request.Request(
            QWEN_API_URL,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'output' in result and 'choices' in result['output']:
                return result['output']['choices'][0]['message']['content']
            else:
                logger.error(f"千问AI返回异常: {result}")
                return None

    except urllib.error.HTTPError as e:
        logger.error(f"千问AI HTTP错误: {e.code} - {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        logger.error(f"调用千问AI失败: {e}")
        return None


def analyze_wordcloud(event_id: int, event_title: str, wordcloud_data: List[tuple], user_question: str) -> str:
    """
    分析词云图数据并回答用户问题

    Args:
        event_id: 事件ID
        event_title: 事件标题
        wordcloud_data: 词云数据 [(word, frequency), ...]
        user_question: 用户问题

    Returns:
        str: AI分析回复
    """
    # 构建词云数据文本
    words_text = ", ".join([f"{word}({freq}次)" for word, freq in wordcloud_data[:30]])

    # 获取实时时间信息
    time_info = get_current_time_info()
    
    system_prompt = f"""你是一位专业的社交媒体数据分析师，擅长从词云图中洞察热点话题的舆论趋势和用户关注点。

{time_info}

当前分析的事件：{event_title}
事件ID：{event_id}

该事件的词云图TOP30关键词及出现频次：
{words_text}

请基于以上词云数据，从多个角度进行分析：
1. 舆论焦点：用户最关注的核心话题是什么
2. 情感倾向：从关键词判断整体舆论的情感走向
3. 传播特征：话题传播的特点和关键节点
4. 关联话题：与主话题相关的衍生讨论
5. 潜在风险：可能存在的舆情风险点

回答要求：
- 多角度分析，不做限制
- 结合具体关键词进行论证
- 提供数据洞察而非泛泛而谈
- 如发现异常或有趣的模式，请特别指出
- 如果用户询问时间相关问题，请使用上面提供的系统实时信息回答"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]

    response = call_qwen_ai(messages)
    return response if response else "抱歉，AI分析服务暂时不可用，请稍后重试。"


def analyze_3d_chart(selected_events: List[Dict], user_question: str) -> str:
    """
    分析三维关联分析图表并回答用户问题

    Args:
        selected_events: 选中事件列表
        user_question: 用户问题

    Returns:
        str: AI分析回复
    """
    # 构建事件数据文本
    events_text = []
    for i, event in enumerate(selected_events, 1):
        events_text.append(
            f"{i}. {event['title']}\n"
            f"   - 热度值: {event['formatted_hot']}\n"
            f"   - 评论数: {event['comment_count']}\n"
            f"   - 正面情感: {event['positive_ratio']:.1f}%\n"
            f"   - 负面情感: {event['negative_ratio']:.1f}%\n"
            f"   - 中性情感: {event['neutral_ratio']:.1f}%\n"
            f"   - 主导情感: {event['dominant']}\n"
        )

    events_summary = "\n".join(events_text)

    # 计算统计数据
    total_events = len(selected_events)
    avg_hot = sum(e['hot_value'] for e in selected_events) / total_events if total_events > 0 else 0
    total_comments = sum(e['comment_count'] for e in selected_events)
    positive_events = sum(1 for e in selected_events if e['dominant'] == 'positive')
    negative_events = sum(1 for e in selected_events if e['dominant'] == 'negative')
    neutral_events = sum(1 for e in selected_events if e['dominant'] == 'neutral')

    # 获取实时时间信息
    time_info = get_current_time_info()
    
    system_prompt = f"""你是一位专业的社交媒体数据分析师，擅长从热度-传播-情感三维数据中洞察热点事件的传播规律和舆论特征。

{time_info}

当前分析的事件数量：{total_events}个
总评论数：{total_comments}
平均热度：{avg_hot:.0f}
情感分布：正面{positive_events}个、负面{negative_events}个、中性{neutral_events}个

选中事件的详细数据：
{events_summary}

请基于以上三维数据，从多个角度进行分析：
1. 热度-传播关系：热度与传播量之间的关联模式
2. 情感分布特征：整体舆论的情感倾向和分布规律
3. 事件对比：不同事件之间的差异和共性
4. 传播规律：高热度事件的传播特征
5. 舆情洞察：从数据中发现的特殊现象或趋势

回答要求：
- 多角度分析，不做限制
- 结合具体数据进行论证
- 提供数据洞察而非泛泛而谈
- 如发现异常或有趣的模式，请特别指出
- 如果用户询问时间相关问题，请使用上面提供的系统实时信息回答"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]

    response = call_qwen_ai(messages)
    return response if response else "抱歉，AI分析服务暂时不可用，请稍后重试。"


def generate_ai_html_interface() -> str:
    """
    生成AI聊天界面的HTML代码

    Returns:
        str: HTML代码
    """
    return '''
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
    '''


def generate_ai_css() -> str:
    """
    生成AI聊天界面的CSS代码

    Returns:
        str: CSS代码
    """
    return '''
        /* AI聊天面板 */
        .ai-chat-panel {
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
        }
        .ai-chat-panel.active {
            display: flex;
        }
        .ai-chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            font-size: 16px;
        }
        .ai-chat-close {
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
        }
        .ai-chat-close:hover {
            background: rgba(255,255,255,0.2);
        }
        .ai-chat-context {
            background: #f8f9fa;
            padding: 10px 15px;
            border-bottom: 1px solid #e8e8e8;
            font-size: 12px;
            color: #666;
        }
        .ai-context-info {
            margin-bottom: 4px;
        }
        .ai-context-info span {
            color: #1890ff;
            font-weight: 600;
        }
        .ai-chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .ai-message {
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.6;
            word-wrap: break-word;
        }
        .ai-message.user {
            align-self: flex-end;
            background: #1890ff;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .ai-message.ai {
            align-self: flex-start;
            background: #f0f0f0;
            color: #333;
            border-bottom-left-radius: 4px;
        }
        .ai-message.loading {
            align-self: flex-start;
            background: #f0f0f0;
            color: #666;
            font-style: italic;
        }
        .ai-message.error {
            align-self: flex-start;
            background: #fff2f0;
            color: #ff4d4f;
            border: 1px solid #ffccc7;
        }
        .ai-chat-input-area {
            padding: 15px;
            border-top: 1px solid #e8e8e8;
            display: flex;
            gap: 10px;
        }
        .ai-chat-input {
            flex: 1;
            padding: 10px 14px;
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
        }
        .ai-chat-input:focus {
            border-color: #1890ff;
        }
        .ai-chat-send {
            padding: 10px 20px;
            background: #1890ff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        .ai-chat-send:hover {
            background: #40a9ff;
        }
        .ai-chat-toggle {
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
        }
        .ai-chat-toggle:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        }
        @media (max-width: 768px) {
            .ai-chat-panel {
                width: calc(100% - 40px);
                height: calc(100% - 120px);
                bottom: 80px;
                right: 20px;
                left: 20px;
            }
        }
    '''


def generate_ai_js() -> str:
    """
    生成AI聊天界面的JavaScript代码

    Returns:
        str: JavaScript代码
    """
    return '''
        // ==================== AI聊天功能 ====================
        let aiChatOpen = false;
        let aiCurrentModule = '';
        let aiCurrentEventId = null;
        let aiCurrentEventTitle = '';
        let aiSelectedEvents = [];

        function toggleAIChat() {
            const panel = document.getElementById('aiChatPanel');
            aiChatOpen = !aiChatOpen;
            panel.classList.toggle('active', aiChatOpen);
        }

        function updateAIContext(module, data) {
            aiCurrentModule = module;
            document.getElementById('aiCurrentModule').textContent = module;
            document.getElementById('aiCurrentData').textContent = data;
        }

        function addAIMessage(content, type) {
            const container = document.getElementById('aiChatMessages');
            const msg = document.createElement('div');
            msg.className = 'ai-message ' + type;
            msg.innerHTML = content;
            container.appendChild(msg);
            container.scrollTop = container.scrollHeight;
        }

        async function sendAIQuestion() {
            const input = document.getElementById('aiChatInput');
            const question = input.value.trim();
            if (!question) return;

            input.value = '';
            addAIMessage(question, 'user');
            addAIMessage('正在分析数据并生成回复...', 'loading');

            try {
                let response;
                if (aiCurrentModule === '词云图' && aiCurrentEventId !== null) {
                    // 获取当前事件的词云数据
                    const wordcloudData = wordcloudData[aiCurrentEventId] || [];
                    response = await fetch('/api/ai/analyze-wordcloud', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            event_id: aiCurrentEventId,
                            event_title: aiCurrentEventTitle,
                            wordcloud_data: wordcloudData,
                            question: question
                        })
                    });
                } else if (aiCurrentModule === '三维分析' && aiSelectedEvents.length > 0) {
                    response = await fetch('/api/ai/analyze-3d', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            selected_events: aiSelectedEvents,
                            question: question
                        })
                    });
                } else {
                    // 通用问答
                    response = await fetch('/api/ai/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            question: question,
                            context: '当前在' + aiCurrentModule + '模块'
                        })
                    });
                }

                const result = await response.json();

                // 移除loading消息
                const loadingMsgs = document.querySelectorAll('.ai-message.loading');
                loadingMsgs.forEach(msg => msg.remove());

                if (result.success) {
                    addAIMessage(result.answer, 'ai');
                } else {
                    addAIMessage('抱歉，分析失败：' + (result.error || '未知错误'), 'error');
                }
            } catch (error) {
                const loadingMsgs = document.querySelectorAll('.ai-message.loading');
                loadingMsgs.forEach(msg => msg.remove());
                addAIMessage('网络错误，请检查连接后重试。', 'error');
            }
        }
    '''
