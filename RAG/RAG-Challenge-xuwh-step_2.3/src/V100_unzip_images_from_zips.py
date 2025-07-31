'''
程序说明：
## 1. 批量解压指定目录下所有zip文件中的图片文件（如png、jpg、jpeg、gif、bmp、webp等）。
## 2. 支持调试模式（只处理前2个zip）和正式模式（处理全部zip），输出图片到image子目录，全部图片直接放在image下，文件名为原始图片名，不加前缀。
## 3. 不依赖minerU相关代码，独立运行，便于调试和正式执行切换。
'''
import os
import zipfile
import sys

# 支持的图片扩展名
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}

def is_image(filename):
    """
    :function: 判断文件名是否为图片文件
    :param filename: 文件名
    :return: True/False
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in IMAGE_EXTS

def extract_images_from_zip(zip_path, output_dir):
    """
    :function: 从zip文件中解压所有图片到指定目录，直接用原始文件名
    :param zip_path: zip文件路径
    :param output_dir: 输出目录
    :return: None
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            members = zip_ref.namelist()
            img_members = [m for m in members if is_image(m)]
            if not img_members:
                print(f"{os.path.basename(zip_path)} 没有图片文件")
                return
            os.makedirs(output_dir, exist_ok=True)
            for m in img_members:
                out_name = os.path.basename(m)
                out_path = os.path.join(output_dir, out_name)
                with zip_ref.open(m) as source, open(out_path, 'wb') as target:
                    target.write(source.read())
            print(f"已解压 {len(img_members)} 张图片到 {output_dir}")
    except Exception as e:
        print(f"解压失败: {zip_path}, 错误: {e}")

def main():
    """
    :function: 主函数，批量处理目录下所有zip文件
    :return: None
    """
    # 可根据需要修改
    zip_dir = os.path.join('data', 'test_set', 'debug_data', '03_reports_markdown')
    output_root = os.path.join(zip_dir, 'image')  # 统一输出到image目录
    debug = False  # 调试模式只处理前2个zip
    
    # 支持命令行参数切换模式
    if len(sys.argv) > 1 and sys.argv[1] == 'full':
        debug = False
    print(f"运行模式: {'调试(仅前2个zip)' if debug else '正式(全部zip)'}")
    
    zip_files = [f for f in os.listdir(zip_dir) if f.lower().endswith('.zip')]
    if debug:
        zip_files = zip_files[:2]
    if not zip_files:
        print("未找到zip文件")
        return
    print(f"共需处理 {len(zip_files)} 个zip文件")
    for idx, zip_name in enumerate(zip_files, 1):
        zip_path = os.path.join(zip_dir, zip_name)
        print(f"[{idx}/{len(zip_files)}] 处理: {zip_name}")
        extract_images_from_zip(zip_path, output_root)
    print("全部处理完成。图片已输出到:", output_root)

if __name__ == "__main__":
    main() 