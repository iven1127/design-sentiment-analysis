from flask import Flask, render_template_string, request, jsonify
import os

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>设计舆情分析</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Microsoft YaHei', 'PingFang SC', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
            font-size: 32px;
        }
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .input-group { margin-bottom: 20px; }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #333;
            font-size: 16px;
        }
        input, textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            transition: border-color 0.3s;
            font-family: inherit;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            min-height: 180px;
            resize: vertical;
            line-height: 1.6;
        }
        button {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        button:active {
            transform: translateY(-1px);
        }
        .result {
            margin-top: 30px;
            padding: 30px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            display: none;
            animation: fadeIn 0.5s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .result.show { display: block; }
        .result h3 {
            color: #333;
            margin-bottom: 20px;
            font-size: 20px;
        }
        .sentiment {
            font-size: 36px;
            font-weight: bold;
            margin: 20px 0;
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            background: white;
        }
        .positive { color: #4caf50; }
        .negative { color: #f44336; }
        .neutral { color: #ff9800; }
        .details {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-top: 15px;
        }
        .details p {
            margin: 10px 0;
            color: #555;
            line-height: 1.8;
        }
        .keywords {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }
        .keyword {
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
            background: #f0f0f0;
        }
        .keyword.positive { background: #e8f5e9; color: #2e7d32; }
        .keyword.negative { background: #ffebee; color: #c62828; }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #fff;
            font-size: 12px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 设计舆情分析</h1>
        <p class="subtitle">基于关键词的智能情感分析</p>

        <div class="input-group">
            <label>📝 标题（可选）</label>
            <input type="text" id="title" placeholder="请输入帖子标题...">
        </div>

        <div class="input-group">
            <label>💬 内容</label>
            <textarea id="content" placeholder="请输入需要分析的内容...&#10;&#10;例如：这个产品真的很好用，质量也不错，值得推荐给大家！"></textarea>
        </div>

        <button onclick="analyze()">🔍 开始分析</button>

        <div class="result" id="result">
            <h3>📈 分析结果</h3>
            <div class="sentiment" id="sentiment"></div>
            <div class="details">
                <p id="summary"></p>
                <div class="keywords" id="keywords"></div>
            </div>
        </div>
    </div>

    <div class="footer">
        © 2024 设计舆情分析 | Powered by AI
    </div>

    <script>
        function analyze() {
            const title = document.getElementById('title').value;
            const content = document.getElementById('content').value;

            if (!content.trim()) {
                alert('⚠️ 请输入内容！');
                return;
            }

            const text = (title + ' ' + content).toLowerCase();

            // 扩展的关键词库
            const positiveWords = {
                '好': 2, '棒': 2, '优秀': 3, '喜欢': 2, '推荐': 3, '完美': 3,
                '满意': 2, '赞': 2, '不错': 2, '厉害': 2, '优质': 2, '惊艳': 3,
                '值得': 2, '实用': 2, '方便': 2, '舒服': 2, '合适': 1, '漂亮': 2,
                '精致': 2, '超值': 2, '靠谱': 2, '给力': 2, '满分': 3, '爱了': 2
            };

            const negativeWords = {
                '差': 2, '烂': 3, '垃圾': 3, '失望': 2, '不好': 2, '难用': 2,
                '糟糕': 2, '后悔': 3, '坑': 2, '骗': 3, '退货': 2, '投诉': 2,
                '质量差': 3, '不值': 2, '浪费': 2, '掉色': 2, '破损': 2, '气': 2,
                '不满': 2, '问题': 1, '瑕疵': 1, '难看': 2, '丑': 2
            };

            let positiveScore = 0;
            let negativeScore = 0;
            const foundPositive = [];
            const foundNegative = [];

            Object.keys(positiveWords).forEach(word => {
                if (text.includes(word)) {
                    positiveScore += positiveWords[word];
                    foundPositive.push(word);
                }
            });

            Object.keys(negativeWords).forEach(word => {
                if (text.includes(word)) {
                    negativeScore += negativeWords[word];
                    foundNegative.push(word);
                }
            });

            const result = document.getElementById('result');
            const sentiment = document.getElementById('sentiment');
            const summary = document.getElementById('summary');
            const keywordsDiv = document.getElementById('keywords');

            let sentimentText, sentimentClass, summaryText;

            if (positiveScore > negativeScore * 1.5) {
                sentimentClass = 'positive';
                sentimentText = '😊 积极情感';
                summaryText = `这是一段积极正面的内容！检测到 <strong>${foundPositive.length}</strong> 个积极词汇，积极指数：<strong>${positiveScore}</strong>`;
            } else if (negativeScore > positiveScore * 1.5) {
                sentimentClass = 'negative';
                sentimentText = '😞 消极情感';
                summaryText = `这是一段消极负面的内容。检测到 <strong>${foundNegative.length}</strong> 个消极词汇，消极指数：<strong>${negativeScore}</strong>`;
            } else {
                sentimentClass = 'neutral';
                sentimentText = '😐 中性情感';
                summaryText = `这是一段中性内容。积极指数：<strong>${positiveScore}</strong>，消极指数：<strong>${negativeScore}</strong>`;
            }

            sentiment.className = `sentiment ${sentimentClass}`;
            sentiment.textContent = sentimentText;
            summary.innerHTML = summaryText;

            // 显示关键词
            keywordsDiv.innerHTML = '';
            if (foundPositive.length > 0) {
                foundPositive.forEach(word => {
                    const span = document.createElement('span');
                    span.className = 'keyword positive';
                    span.textContent = `✓ ${word}`;
                    keywordsDiv.appendChild(span);
                });
            }
            if (foundNegative.length > 0) {
                foundNegative.forEach(word => {
                    const span = document.createElement('span');
                    span.className = 'keyword negative';
                    span.textContent = `✗ ${word}`;
                    keywordsDiv.appendChild(span);
                });
            }

            result.classList.add('show');
            result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        // 回车键提交
        document.getElementById('content').addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                analyze();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
