'''
程序说明：
## 1. 简单测试DashScope API调用
## 2. 验证API密钥和模型调用是否正常
## 3. 诊断大模型重排序失败的原因
'''

import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_dashscope_api():
    """测试DashScope API基本功能"""
    logger.info("=== 开始测试DashScope API ===")
    
    try:
        # 导入dashscope
        import dashscope
        from dashscope.rerank import text_rerank
        
        logger.info("✅ dashscope模块导入成功")
        
        # 获取API密钥
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            logger.error("❌ 环境变量DASHSCOPE_API_KEY未设置")
            return False
        
        logger.info("✅ API密钥获取成功")
        
        # 设置API密钥
        dashscope.api_key = api_key
        logger.info("✅ API密钥设置成功")
        
        # 测试简单的reranking调用
        query = "测试查询"
        documents = ["这是第一个测试文档", "这是第二个测试文档"]
        
        logger.info(f"查询: {query}")
        logger.info(f"文档数量: {len(documents)}")
        
        # 调用API
        logger.info("开始调用DashScope reranking API...")
        response = text_rerank.TextReRank.call(
            model="gte-rerank-v2",
            query=query,
            documents=documents,
            top_k=2
        )
        
        logger.info(f"API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ API调用成功")
            logger.info(f"响应结果: {response.output}")
            return True
        else:
            logger.error(f"❌ API调用失败: {response.message}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("开始DashScope API测试")
    
    success = test_dashscope_api()
    
    if success:
        logger.info("🎉 DashScope API测试成功")
    else:
        logger.error("💥 DashScope API测试失败")
    
    logger.info("测试完成")

if __name__ == "__main__":
    main()
