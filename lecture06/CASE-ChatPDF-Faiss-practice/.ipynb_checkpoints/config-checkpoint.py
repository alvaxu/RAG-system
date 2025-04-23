"""
配置文件
"""
import os

# 检查环境变量
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
if not DASHSCOPE_API_KEY:
    raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")

# 模型配置
EMBEDDING_MODEL = "text-embedding-v1"
LLM_MODEL = "qwen-turbo"  # 可以根据需要调整模型

# 文本分块配置
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200 

# LangChain配置
TEXT_SPLITTER_CONFIG = {
    "chunk_size": CHUNK_SIZE,
    "chunk_overlap": CHUNK_OVERLAP
}

# 向量存储配置
VECTOR_STORE_CONFIG =  {
    "dimension": 1536,  # text-embedding-v1的维度
    "similarity_search_k": 3
} 