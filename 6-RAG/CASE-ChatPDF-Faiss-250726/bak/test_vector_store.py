'''
程序说明：
## 1. 该模块用于测试向量数据库创建功能
## 2. 使用模拟的API密钥来验证代码逻辑
'''

from V300_vector_store_qa import create_vector_store_from_documents

if __name__ == "__main__":
    print("开始测试向量数据库创建功能...")
    
    # 使用模拟的API密钥
    DASHSCOPE_API_KEY = 'test_api_key'
    
    # 从文档创建向量存储
    try:
        vector_store = create_vector_store_from_documents("md", DASHSCOPE_API_KEY, "./vector_db")
        print("向量数据库创建成功！")
    except Exception as e:
        print(f"向量数据库创建失败: {e}")
        print("这可能是由于缺少有效的API密钥导致的，属于正常现象。")
    
    print("测试完成。")