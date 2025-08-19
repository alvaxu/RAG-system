import sys
sys.path.append('.')
from config.settings import Settings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.api_key_manager import get_dashscope_api_key

# 加载配置
config = Settings.load_from_file('config.json')

# 获取API密钥
config_key = config.dashscope_api_key
api_key = get_dashscope_api_key(config_key)

if not api_key:
    print('❌ 未找到有效的DashScope API密钥')
    exit()

# 初始化embeddings
embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
vector_db_path = config.vector_db_dir
vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)

print('🔍 检查FAISS的搜索方法')
print('=' * 50)

# 检查可用的方法
methods = [attr for attr in dir(vector_store) if 'search' in attr.lower() and callable(getattr(vector_store, attr))]
print(f'可用的搜索方法: {methods}')

# 检查是否有similarity_search_with_score
if hasattr(vector_store, 'similarity_search_with_score'):
    print('✅ 支持similarity_search_with_score')
else:
    print('❌ 不支持similarity_search_with_score')

# 测试查询
test_query = '图4：中芯国际归母净利润情况概览'

print(f'\\n🔍 测试查询: {test_query}')

# 方法1: similarity_search
print('\\n📋 方法1: similarity_search')
try:
    candidates = vector_store.similarity_search(test_query, k=5, filter={'chunk_type': 'image_text'})
    print(f'返回 {len(candidates)} 个结果')
    
    if candidates:
        first_doc = candidates[0]
        print(f'第一个文档类型: {type(first_doc)}')
        print(f'是否有score属性: {hasattr(first_doc, \"score\")}')
        print(f'所有属性: {[attr for attr in dir(first_doc) if not attr.startswith(\"_\")]}')
        
        # 尝试获取score
        score = getattr(first_doc, 'score', None)
        print(f'getattr(doc, \"score\", None): {score}')
        
        if hasattr(first_doc, 'metadata'):
            print(f'metadata keys: {list(first_doc.metadata.keys())}')
            if 'score' in first_doc.metadata:
                print(f'metadata.score: {first_doc.metadata[\"score\"]}')
        
except Exception as e:
    print(f'❌ 失败: {e}')

# 方法2: similarity_search_with_score
print('\\n📋 方法2: similarity_search_with_score')
try:
    if hasattr(vector_store, 'similarity_search_with_score'):
        docs_and_scores = vector_store.similarity_search_with_score(test_query, k=5, filter={'chunk_type': 'image_text'})
        print(f'返回 {len(docs_and_scores)} 个结果')
        
        if docs_and_scores:
            first_result = docs_and_scores[0]
            print(f'第一个结果类型: {type(first_result)}')
            print(f'第一个结果长度: {len(first_result)}')
            print(f'第一个结果内容: {first_result}')
            
            if len(first_result) == 2:
                doc, score = first_result
                print(f'文档类型: {type(doc)}')
                print(f'分数类型: {type(score)}')
                print(f'分数值: {score}')
                print(f'doc.score: {getattr(doc, \"score\", \"不存在\")}')
    else:
        print('❌ 不支持此方法')
        
except Exception as e:
    print(f'❌ 失败: {e}')

# 方法3: 直接检查FAISS索引
print('\\n📋 方法3: 直接检查FAISS索引')
try:
    if hasattr(vector_store, 'index'):
        index = vector_store.index
        print(f'索引类型: {type(index)}')
        print(f'索引属性: {[attr for attr in dir(index) if not attr.startswith(\"_\")]}')
        
        if hasattr(index, 'search'):
            print('✅ 索引支持search方法')
        else:
            print('❌ 索引不支持search方法')
            
        if hasattr(index, 'metric_type'):
            metric_type = index.metric_type
            print(f'距离度量类型: {metric_type}')
            
            # 常见的度量类型
            metric_names = {
                0: 'L2 (欧几里得距离)',
                1: 'IP (内积)',
                2: 'L1 (曼哈顿距离)',
                3: 'Linf (切比雪夫距离)'
            }
            
            if metric_type in metric_names:
                print(f'度量类型说明: {metric_names[metric_type]}')
                
    else:
        print('❌ 没有索引属性')
        
except Exception as e:
    print(f'❌ 失败: {e}')

print('\\n🎯 诊断完成')