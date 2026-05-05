"""
AI分析服务后端
提供千问AI API的代理服务，避免前端暴露API密钥
"""

import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from ai_service import analyze_wordcloud, analyze_3d_chart, call_qwen_ai

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


@app.route('/api/ai/analyze-wordcloud', methods=['POST'])
def api_analyze_wordcloud():
    """分析词云图"""
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        event_title = data.get('event_title', '')
        wordcloud_data = data.get('wordcloud_data', [])
        question = data.get('question', '')

        answer = analyze_wordcloud(event_id, event_title, wordcloud_data, question)
        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        logger.error(f"词云图分析失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/ai/analyze-3d', methods=['POST'])
def api_analyze_3d():
    """分析三维图表"""
    try:
        data = request.get_json()
        selected_events = data.get('selected_events', [])
        question = data.get('question', '')

        answer = analyze_3d_chart(selected_events, question)
        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        logger.error(f"三维分析失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/ai/chat', methods=['POST'])
def api_chat():
    """通用聊天"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        context = data.get('context', '')

        messages = [
            {"role": "system", "content": f"你是一位专业的社交媒体数据分析师。{context}"},
            {"role": "user", "content": question}
        ]

        answer = call_qwen_ai(messages)
        if answer:
            return jsonify({'success': True, 'answer': answer})
        else:
            return jsonify({'success': False, 'error': 'AI服务暂时不可用'})
    except Exception as e:
        logger.error(f"聊天失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok'})


def start_ai_server(port=5000):
    """启动AI服务"""
    print(f"🤖 AI分析服务启动中...")
    print(f"   服务地址: http://localhost:{port}")
    print(f"   API端点:")
    print(f"     - POST /api/ai/analyze-wordcloud")
    print(f"     - POST /api/ai/analyze-3d")
    print(f"     - POST /api/ai/chat")
    print(f"     - GET  /api/health")
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    start_ai_server()
