import React, { useState, useEffect } from 'react';
import { Layout, Input, Button, List, Typography, Card, Spin, message, Empty } from 'antd';
import axios from 'axios';

const { Sider, Content } = Layout;
const { Title, Text } = Typography;

function App_annual() {
  const [question, setQuestion] = useState('');
  const [presetQuestions, setPresetQuestions] = useState([]);
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);

  // 直接从public/questions.json读取预设问题
  useEffect(() => {
    fetch('/questions_annual.json')
      .then(res => res.json())
      .then(setPresetQuestions)
      .catch(() => message.error('无法获取预设问题'));
  }, []);

  // 提交问题
  const handleAsk = () => {
    if (!question.trim()) {
      message.warning('请输入问题');
      return;
    }
    setLoading(true);
    setAnswer(null);
    axios.post('http://localhost:5000/ask', { question })
      .then(res => setAnswer(res.data))
      .catch(() => message.error('查询失败'))
      .finally(() => setLoading(false));
  };

  // 解析final_answer为json（如果是json字符串）
  let parsedAnswer = answer;
  if (answer && typeof answer.final_answer === 'string') {
    try {
      const obj = JSON.parse(answer.final_answer);
      // 如果解析出来有step_by_step_analysis等字段，说明是json
      if (obj && (obj.step_by_step_analysis || obj.reasoning_summary || obj.relevant_pages)) {
        parsedAnswer = { ...answer, ...obj };
      }
    } catch (e) {
      // 不是json字符串，忽略
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={320} style={{ background: '#fff', padding: 24, borderRight: '1px solid #eee' }}>
        <Title level={4}>查询设置</Title>
        <Input.TextArea
          rows={3}
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="请输入问题"
          style={{ marginBottom: 16 }}
        />
        <Button type="primary" block onClick={handleAsk} loading={loading}>
          生成答案
        </Button>
        <div style={{ marginTop: 32 }}>
          <Title level={5}>预设问题</Title>
          <List
            bordered
            dataSource={presetQuestions}
            locale={{ emptyText: <Empty description="暂无预设问题" /> }}
            renderItem={item => (
              <List.Item
                onClick={() => setQuestion(item.text)}
                style={{ cursor: 'pointer' }}
              >
                {item.text}
              </List.Item>
            )}
            style={{ maxHeight: 300, overflow: 'auto' }}
          />
        </div>
      </Sider>
      <Layout>
        <Content style={{ padding: 40, background: '#f7f8fa' }}>
          <Card>
            <Title style={{ marginBottom: 0 }}>公司年报查询RAG系统</Title>
            <Text type="secondary" style={{ fontSize: 16 }}>
              基于向量检索、LLM推理、采用Qwen大模型，基于对存于本地的公司年报的分析，实现精准信息反馈。
            </Text>
            <div style={{ marginTop: 32, minHeight: 300, position: 'relative' }}>
              {loading && <Spin tip="正在检索与推理..." />}
              {!loading && (
                answer ? (
                  <>
                    <Title level={4}>检索结果</Title>
                    <div style={{ marginBottom: 16 }}>
                      <b>分步推理：</b>
                      <ul style={{ background: '#f6f6f6', padding: 12, listStyle: 'none', margin: 0 }}>
                        {(parsedAnswer.step_by_step_analysis || '').split('\n').filter(line => line.trim() !== '').map((line, idx) => (
                          <li key={idx}>{line}</li>
                        ))}
                      </ul>
                    </div>
                    <div style={{ marginBottom: 16 }}>
                      <b>推理摘要：</b>
                      <pre style={{ background: '#f6f6f6', padding: 12 }}>{parsedAnswer.reasoning_summary}</pre>
                    </div>
                    <div style={{ marginBottom: 16 }}>
                      <b>最终答案：</b>
                      <div style={{ background: '#e6ffed', padding: 12, whiteSpace: 'pre-wrap', minHeight: '2em' }}>{parsedAnswer.final_answer}</div>
                    </div>
                    <div style={{ marginBottom: 16 }}>
                      <b>相关文件及页码：</b>
                      <pre style={{ background: '#f6f6f6', padding: 12 }}>
                        {
                          Array.isArray(parsedAnswer.relevant_pages) && parsedAnswer.relevant_pages.length > 0 && typeof parsedAnswer.relevant_pages[0] === 'object'
                            ? Object.entries(
                                parsedAnswer.relevant_pages.reduce((acc, cur) => {
                                  if (cur.file_name) {
                                    acc[cur.file_name] = acc[cur.file_name] || [];
                                    if (cur.page || cur.page_index) {
                                      acc[cur.file_name].push(cur.page || cur.page_index);
                                    }
                                  }
                                  return acc;
                                }, {})
                              ).map(([fname, pages]) =>
                                `${fname}：${[...new Set(pages)].sort((a, b) => a - b).join(', ')}`
                              ).join('\n')
                            : (parsedAnswer.relevant_pages || '无')
                        }
                      </pre>
                    </div>
                    {/* 公司所有文档列表，流式布局放在检索结果底部 */}
                    <div style={{
                      marginTop: 32,
                      background: '#fff',
                      border: '1px solid #eee',
                      borderRadius: 6,
                      boxShadow: '0 2px 8px #eee',
                      padding: 16,
                      minWidth: 220,
                      zIndex: 10
                    }}>
                      <b>公司所有文档：</b>
                      <ul style={{ margin: '8px 0 0 0', padding: 0, listStyle: 'disc inside' }}>
                        {Array.isArray(answer.company_files) && answer.company_files.length > 0
                          ? answer.company_files.map((fname, idx) => (
                              <li key={idx} style={{ wordBreak: 'break-all' }}>{fname}</li>
                            ))
                          : <li style={{ color: '#aaa' }}>无</li>}
                      </ul>
                    </div>
                  </>
                ) : (
                  <Empty description="请在左侧输入问题并点击生成答案" />
                )
              )}
            </div>
          </Card>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App_annual;