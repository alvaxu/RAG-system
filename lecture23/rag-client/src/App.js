// src/App.js
import React from 'react';
import App_1_doc from './App_1_doc';
import App_stock from './App_stock';
import App_annual from './App_annual';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import { Card, Button, Typography, Row, Col } from 'antd';

const { Title } = Typography;

function Home() {
  const navigate = useNavigate();
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f7f8fa' }}>
      <Card style={{ minWidth: 400, padding: 32, boxShadow: '0 2px 8px #eee' }}>
        <Title level={3} style={{ textAlign: 'center', marginBottom: 32 }}>请选择入口</Title>
        <Row gutter={[0, 16]}>
          <Col span={24}>
            <Button type="primary" block size="large" onClick={() => navigate('/App_1_doc')}>
              上市公司信息查询RAG系统
            </Button>
          </Col>
          <Col span={24}>
            <Button type="primary" block size="large" onClick={() => navigate('/App_stock')}>
              上市公司多文档RAG分析
            </Button>
          </Col>
          <Col span={24}>
            <Button type="primary" block size="large" onClick={() => navigate('/App_annual')}>
              公司年报查询RAG系统
            </Button>
          </Col>
        </Row>
      </Card>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/App_1_doc" element={<App_1_doc />} />
        <Route path="/App_stock" element={<App_stock />} />
        <Route path="/App_annual" element={<App_annual />} />
      </Routes>
    </BrowserRouter>
  );
}
export default App;