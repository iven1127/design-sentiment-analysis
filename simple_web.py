"""超简化版本 - 只包含基本功能"""
from flask import Flask, render_template_string, request, jsonify
import sys

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>小红书情感分析工具</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 { color: #667eea; text-align: center; margin-bottom: 30px; }
        .input-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; color: #333; }
        input, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        textarea { min-height: 150px; resize: vertical; }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 8px;
            display: none;
        }
        .result.show { display: block; }
        .sentiment { font-size: 24px; font-weight: bold; margin: 10px 0; }
        .positive { color: #4caf50; }
        .negative { color: #f44336; }
        .neutral { color: #ff9800; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 小红书情感分析工具</h1>

        <div class="input-group">
            <label>标题（可选）</label>
            <input type="text" id="title" placeholder="输入标题...">
        </div>

        <div class="input-group">
            <label>内容</label>
            <textarea id="content" placeholder="输入需要分析的内容..."></textarea>
        </div>

        <button onclick="analyze()">🔍 开始分析</button>

        <div class="result" id="result">
            <h3>分析结果：</h3>
            <div class="sentiment" id="sentiment"></div>
            <p id="details"></p>
        </div>
    </div>

    <script>
        function analyze() {
            const title = document.getElementById('title').value;
            const content = document.getElementById('content').value;

            if (!content.trim()) {
                alert('请输入内容！');
                return;
            }

            // 简单的关键词分析
            const text = (title + ' ' + content).toLowerCase();

            const positiveWords = ['好', '棒', '优秀', '喜欢', '推荐', '完美', '满意', '赞', '不错', '厉害', '优质'];
            const negativeWords = ['差', '烂', '垃圾', '失望', '不好', '难用', '糟糕', '后悔', '坑', '骗'];

            let positiveCount = 0;
            let negativeCount = 0;

            positiveWords.forEach(word => {
                if (text.includes(word)) positiveCount++;
            });

            negativeWords.forEach(word => {
                if (text.includes(word)) negativeCount++;
            });

            const result = document.getElementById('result');
            const sentiment = document.getElementById('sentiment');
            const details = document.getElementById('details');

            if (positiveCount > negativeCount) {
                sentiment.className = 'sentiment positive';
                sentiment.textContent = '😊 积极情感';
                details.textContent = `检测到 ${positiveCount} 个积极词汇，${negativeCount} 个消极词汇`;
            } else if (negativeCount > positiveCount) {
                sentiment.className = 'sentiment negative';
                sentiment.textContent = '😞 消极情感';
                details.textContent = `检测到 ${negativeCount} 个消极词汇，${positiveCount} 个积极词汇`;
            } else {
                sentiment.className = 'sentiment neutral';
                sentiment.textContent = '😐 中性情感';
                details.textContent = `检测到 ${positiveCount} 个积极词汇，${negativeCount} 个消极词汇`;
            }

            result.classList.add('show');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

if __name__ == '__main__':
    print("=" * 50)
    print("  🚀 设计舆情分析工具")
    print("  📱 请在浏览器打开: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
