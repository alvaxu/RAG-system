(function() {
    'use strict';

    // 初始化配置
    const config = window.dingtalkAgentConfig || {};

    // 创建悬浮球元素
    const orb = document.createElement('div');
    orb.className = 'magic-orb';
    orb.style.position = 'fixed';
    orb.style.bottom = '20px';
    orb.style.right = '20px';
    orb.style.width = '48px';
    orb.style.height = '48px';
    orb.style.borderRadius = '50%';
    orb.style.backgroundColor = '#ffffff';
    orb.style.cursor = 'pointer';
    orb.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    orb.style.zIndex = '1000';
    orb.style.backgroundImage = 'url("https://vl-image.oss-cn-shanghai.aliyuncs.com/ai_assistant.png")';
    orb.style.backgroundSize = 'contain';
    orb.style.backgroundPosition = 'center';
    orb.style.backgroundRepeat = 'no-repeat';
    orb.style.transition = 'all 0.3s ease';
    orb.style.border = 'none';
    orb.innerHTML = '';

    // 添加图片加载错误处理
    const img = new Image();
    img.onload = function() {
        console.log('图片加载成功');
    };
    img.onerror = function() {
        console.error('图片加载失败');
        // 图片加载失败时使用纯色背景作为后备方案
        orb.style.backgroundColor = '#4c9bfd';
    };
    img.src = 'https://vl-image.oss-cn-shanghai.aliyuncs.com/ai_assistant.png';

    document.body.appendChild(orb);

    // 添加悬浮效果
    orb.addEventListener('mouseover', function() {
        orb.style.transform = 'scale(1.1)';
        orb.style.boxShadow = '0 4px 15px rgba(0,0,0,0.15)';
    });

    orb.addEventListener('mouseout', function() {
        orb.style.transform = 'scale(1)';
        orb.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    });

    // 创建聊天框HTML
    function createChatHTML() {
        return `
            <div id="chat-container" style="display: none; position: fixed; right: 20px; top: 0; bottom: 0; width: 450px; background: #fff; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); z-index: 1000;">
                <div style="height: 60px; background: #4c9bfd; color: #fff; line-height: 60px; padding: 0 20px; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 18px;">OA流程助手</span>
                    <span id="close-chat" style="cursor: pointer; font-size: 24px;">×</span>
                </div>
                <div id="chat-messages" style="position: absolute; top: 60px; bottom: 70px; left: 0; right: 0; overflow-y: auto; padding: 20px; background: #f5f5f5;">
                    <div class="message bot" style="margin-bottom: 15px; display: flex; justify-content: flex-start;">
                        <div style="background: #ffffff; color: #333333; padding: 10px; border-radius: 10px; font-size: 13px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-family: sans-serif; display: inline-block; word-break: break-word;">
                            您好！我是OA流程助手，请问有什么可以帮您？
                        </div>
                    </div>
                </div>
                <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 70px; padding: 15px; display: flex; background: #f5f5f5; border-radius: 0 0 10px 10px;">
                    <input id="chat-input" type="text" placeholder="请输入您的问题..." style="flex: 1; border: 1px solid #ddd; border-radius: 5px; padding: 0 10px; margin-right: 10px; font-size: 16px;">
                    <button id="send-message" style="background: #4c9bfd; color: #fff; border: none; padding: 0 20px; border-radius: 5px; cursor: pointer; font-size: 16px;">发送</button>
                </div>
            </div>
        `;
    }

    // 初始化聊天功能
    function initChat() {
        // 添加聊天框到页面
        document.body.insertAdjacentHTML('beforeend', createChatHTML());

        const chatContainer = document.getElementById('chat-container');
        const closeChat = document.getElementById('close-chat');
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-message');
        const chatMessages = document.getElementById('chat-messages');

        // 悬浮球点击事件
        orb.addEventListener('click', function() {
            chatContainer.style.display = 'block';
            orb.style.display = 'none';
        });

        // 关闭聊天框
        closeChat.addEventListener('click', function() {
            chatContainer.style.display = 'none';
            orb.style.display = 'block';
        });

        // 添加等待动画函数
        function createLoadingDots() {
            const dots = document.createElement('span');
            dots.textContent = '';
            dots.style.display = 'inline-block';
            
            let count = 0;
            const interval = setInterval(() => {
                dots.textContent = '.'.repeat(count + 1);
                count = (count + 1) % 3;
            }, 500);

            return { element: dots, stop: () => clearInterval(interval) };
        }

        // 发送消息
        function sendMessage() {
            const message = chatInput.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            chatInput.value = '';

            // 构建请求数据
            const currentTime = new Date().toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            }).replace(/\//g, '/');

            const requestData = {
                'model': 'OA流程助手',
                'messages': [
                    {
                        'role': 'system',
                        'content': `\nYou are a helpful assistant.\nCurrent model: OA流程助手\nCurrent time: ${currentTime}\n`
                    },
                    {
                        'role': 'system',
                        'content': '欢迎使用流程分析AI助手！\n\n我是您的智能流程助手...'
                    },
                    {
                        'role': 'user',
                        'content': message
                    }
                ]
            };

            // 创建一个新的消息容器用于流式显示
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot';
            messageDiv.style.marginBottom = '15px';
            messageDiv.style.display = 'flex';
            messageDiv.style.justifyContent = 'flex-start';

            const bubble = document.createElement('div');
            bubble.style.padding = '10px';
            bubble.style.borderRadius = '10px';
            bubble.style.fontSize = '13px';
            bubble.style.background = '#ffffff';
            bubble.style.color = '#333333';
            bubble.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
            bubble.style.fontFamily = 'sans-serif';
            bubble.style.display = 'inline-block';
            bubble.style.wordBreak = 'break-word';
            bubble.style.fontWeight = 'normal';
            bubble.style.textAlign = 'left';
            
            // 添加加载动画
            const loading = createLoadingDots();
            bubble.textContent = '正在思考中';
            bubble.appendChild(loading.element);

            messageDiv.appendChild(bubble);
            chatMessages.appendChild(messageDiv);

            // 发送请求并处理流式响应
            fetch('http://127.0.0.1:5000/v1/chat/completions', {
                    method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            })
            .then(response => {
                console.log('Fetch response received:', response);
                // 检查响应是否成功
                if (!response.ok) {
                    console.error('HTTP error! status:', response.status);
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                // 检查是否为stream
                if (!response.body) {
                    console.error('No response body (stream) found!');
                    throw new Error('No response body (stream) found!');
                }
                // 获取响应的文本流
                const reader = response.body.getReader();
                let buffer = '';
                let decoder = new TextDecoder();

                // 修改 Markdown 解析函数
                function parseMarkdown(text) {
                    // 处理加粗 **text**
                    text = text.replace(/\*\*(.*?)\*\*/g, '<strong style="font-weight: bold;">$1</strong>');
                    
                    // 处理列表项
                    text = text.replace(/^- (.*)$/gm, '• $1');
                    
                    // 处理换行
                    text = text.replace(/\n/g, '<br>');
                    
                    return text;
                }

                // 修改流式响应处理部分
                function processStream({ done, value }) {
                    if (done) {
                        console.log('Stream complete');
                        return;
                    }

                    const chunk = decoder.decode(value, { stream: true });
                    
                    // 如果是第一次收到数据，清除加载动画和文本
                    if (bubble.textContent.startsWith('正在思考中')) {
                        loading.stop();
                        bubble.innerHTML = '';
                    }

                    buffer += chunk;

                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.trim() === '') continue;
                        if (!line.startsWith('data: ')) continue;

                        try {
                            const jsonStr = line.slice(5).trim();
                            const data = JSON.parse(jsonStr);
                            if (data.choices && 
                                data.choices[0] && 
                                data.choices[0].delta && 
                                data.choices[0].delta.content) {
                                const content = data.choices[0].delta.content;
                                
                                // 解析 Markdown 并添加到气泡中
                                const parsedContent = parseMarkdown(content);
                                bubble.innerHTML = bubble.innerHTML + parsedContent;
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                        } catch (e) {
                            console.error('Error parsing JSON:', e, 'Line:', line);
                        }
                    }

                    return reader.read().then(processStream);
                }

                return reader.read().then(processStream);
            })
            .catch(error => {
                loading.stop();  // 出错时也要停止加载动画
                console.error('Error:', error);
                bubble.textContent = '抱歉，出现了一些问题，请稍后再试。';
                chatMessages.scrollTop = chatMessages.scrollHeight;
            });
        }

        // 添加消息到聊天框
        function addMessage(text, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.style.marginBottom = '15px';
            messageDiv.style.display = 'flex';
            messageDiv.style.justifyContent = type === 'user' ? 'flex-end' : 'flex-start';

            const bubble = document.createElement('div');
            bubble.style.padding = '10px';
            bubble.style.borderRadius = '10px';
            bubble.style.maxWidth = '95%';
            bubble.style.fontSize = '13px';
            bubble.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
            bubble.style.fontFamily = 'sans-serif';
            bubble.style.display = 'inline-block';
            bubble.style.wordBreak = 'break-word';

            if (type === 'user') {
                bubble.style.background = '#e6f3ff';
                bubble.style.color = '#333';
                bubble.style.textAlign = 'right';
            } else {
                bubble.style.background = '#ffffff';
                bubble.style.color = '#333333';
                bubble.style.textAlign = 'left';
            }

            bubble.textContent = text;
            messageDiv.appendChild(bubble);
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // 发送按钮点击事件
        sendButton.addEventListener('click', sendMessage);

        // 回车发送
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    // 初始化
    document.addEventListener('DOMContentLoaded', function() {
        initChat();
    });
})();