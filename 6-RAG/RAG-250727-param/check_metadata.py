import pickle
import os

def check_metadata():
    """检查元数据文件中的图片数据"""
    metadata_file = "central/vector_db/metadata.pkl"
    
    if not os.path.exists(metadata_file):
        print("❌ 元数据文件不存在")
        return
    
    try:
        with open(metadata_file, 'rb') as f:
            data = pickle.load(f)
        
        print(f"📊 总记录数: {len(data)}")
        
        # 统计不同类型
        image_data = [item for item in data if item.get('chunk_type') == 'image']
        text_data = [item for item in data if item.get('chunk_type') == 'text']
        table_data = [item for item in data if item.get('chunk_type') == 'table']
        
        print(f"🖼️  图片记录数: {len(image_data)}")
        print(f"📄 文本记录数: {len(text_data)}")
        print(f"📊 表格记录数: {len(table_data)}")
        
        if image_data:
            print("\n🖼️  图片详情:")
            for i, item in enumerate(image_data[:5]):  # 只显示前5个
                print(f"  {i+1}. 图片ID: {item.get('image_id', 'No ID')}")
                print(f"     路径: {item.get('image_path', 'No path')}")
                print(f"     文档: {item.get('document_name', 'Unknown')}")
                print(f"     页码: {item.get('page_number', 'Unknown')}")
                print()
        else:
            print("\n❌ 没有找到图片记录")
        
        # 显示一些文本记录的示例
        if text_data:
            print("📄 文本记录示例:")
            for i, item in enumerate(text_data[:3]):
                print(f"  {i+1}. 文档: {item.get('document_name', 'Unknown')}")
                print(f"     页码: {item.get('page_number', 'Unknown')}")
                print(f"     内容: {item.get('content', 'No content')[:100]}...")
                print()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_metadata() 