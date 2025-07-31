import os
import re
import zipfile
from pathlib import Path

def extract_images_from_md(md_dir):
    """
    遍历指定目录中的MD文件，对于包含图片引用的，
    从同名的ZIP文件中的images目录解压相应图片到当前目录的images子目录下
    """
    # 确保images目录存在
    images_output_dir = Path(md_dir) / "images"
    images_output_dir.mkdir(exist_ok=True)
    
    print(f"开始处理目录: {md_dir}")
    print(f"图片将保存到: {images_output_dir}")
    
    # 检查目录中是否有ZIP文件
    zip_files = list(Path(md_dir).glob("*.zip"))
    if not zip_files:
        print("警告: 在目录中未找到任何ZIP文件")
        print("请确保ZIP文件与MD文件同名并位于同一目录中")
    else:
        print(f"找到 {len(zip_files)} 个ZIP文件")
    
    # 遍历目录中的所有MD文件
    md_files = list(Path(md_dir).glob("*.md"))
    print(f"找到 {len(md_files)} 个MD文件")
    
    for md_file in md_files:
        print(f"\n处理文件: {md_file.name}")
        
        # 检查是否存在同名的ZIP文件（两种可能的命名方式）
        zip_file = md_file.with_suffix('.zip')
        pdf_zip_file = Path(str(md_file).replace('.md', '.pdf.zip'))
        
        if zip_file.exists():
            target_zip = zip_file
        elif pdf_zip_file.exists():
            target_zip = pdf_zip_file
        else:
            print(f"  跳过: 未找到同名ZIP文件 {zip_file.name} 或 {pdf_zip_file.name}")
            continue
        
        # 读取MD文件内容
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  错误: 无法读取MD文件 {md_file.name}: {str(e)}")
            continue
        
        # 查找图片引用
        image_pattern = r'!\[.*?\]\((images/[^)]+\.\w+)\)'
        image_matches = re.findall(image_pattern, content)
        
        if not image_matches:
            print(f"  跳过: MD文件中未找到图片引用")
            continue
        
        print(f"  发现 {len(image_matches)} 个图片引用")
        
        # 从ZIP文件中解压图片
        try:
            with zipfile.ZipFile(target_zip, 'r') as zip_ref:
                for image_path in image_matches:
                    try:
                        # 从ZIP文件中读取图片数据
                        image_data = zip_ref.read(image_path)
                        
                        # 确定输出路径
                        output_path = images_output_dir / Path(image_path).name
                        
                        # 写入图片文件
                        with open(output_path, 'wb') as img_file:
                            img_file.write(image_data)
                        
                        print(f"    已解压: {image_path} -> {output_path}")
                    except KeyError:
                        print(f"    警告: 在ZIP文件中未找到 {image_path}")
        except Exception as e:
            print(f"  错误: 无法处理ZIP文件 {target_zip.name}: {str(e)}")

if __name__ == "__main__":
    # 指定MD文件目录
    md_directory = r"d:\cursorprj\6-RAG\RAG-250727-param\md_zxgj"
    
    # 执行图片提取
    extract_images_from_md(md_directory)
    
    print("\n处理完成")