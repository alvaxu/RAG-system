'''
程序说明：
## 1. 简单的配置编辑器
## 2. 提供交互式配置修改界面
## 3. 支持查看、修改、保存配置
## 4. 提供配置验证功能
'''

import os
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager


class ConfigEditor:
    """
    配置编辑器
    """
    
    def __init__(self, config_file: str = 'config.json'):
        """
        初始化配置编辑器
        :param config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config_manager = ConfigManager(config_file)
    
    def show_menu(self):
        """
        显示菜单
        """
        print("\n" + "="*50)
        print("RAG系统配置编辑器")
        print("="*50)
        print("1. 查看当前配置")
        print("2. 修改路径配置")
        print("3. 修改处理配置")
        print("4. 修改向量存储配置")
        print("5. 修改问答系统配置")
        print("6. 修改记忆配置")
        print("7. 修改API配置")
        print("8. 验证配置")
        print("9. 保存配置")
        print("0. 退出")
        print("="*50)
    
    def show_current_config(self):
        """
        显示当前配置
        """
        print("\n当前配置:")
        self.config_manager.print_config_summary()
    
    def edit_paths(self):
        """
        修改路径配置
        """
        print("\n修改路径配置:")
        print("当前路径配置:")
        
        # 显示Settings中的路径（与配置文件一致）
        print(f"  pdf_dir: {self.config_manager.settings.pdf_dir}")
        print(f"  md_dir: {self.config_manager.settings.md_dir}")
        print(f"  output_dir: {self.config_manager.settings.output_dir}")
        print(f"  vector_db_dir: {self.config_manager.settings.vector_db_dir}")
        print(f"  memory_db_dir: {self.config_manager.settings.memory_db_dir}")
        print(f"  central_images_dir: {self.config_manager.settings.central_images_dir}")
        print(f"  web_app_dir: {self.config_manager.settings.web_app_dir}")
        
        print("\n可修改的路径:")
        print("1. pdf_dir - PDF文件目录")
        print("2. md_dir - Markdown文件目录")
        print("3. output_dir - 输出目录")
        print("4. vector_db_dir - 向量数据库目录")
        print("5. memory_db_dir - 记忆数据库目录")
        print("6. central_images_dir - 统一图片目录")
        print("7. web_app_dir - Web应用目录")
        
        choice = input("\n请选择要修改的路径 (1-7, 0返回): ").strip()
        
        if choice == '0':
            return
        
        path_map = {
            '1': 'pdf_dir',
            '2': 'md_dir', 
            '3': 'output_dir',
            '4': 'vector_db_dir',
            '5': 'memory_db_dir',
            '6': 'central_images_dir',
            '7': 'web_app_dir'
        }
        
        if choice in path_map:
            path_name = path_map[choice]
            current_path = getattr(self.config_manager.settings, path_name)
            print(f"\n当前 {path_name}: {current_path}")
            
            new_path = input(f"请输入新的 {path_name} 路径: ").strip()
            if new_path:
                setattr(self.config_manager.settings, path_name, new_path)
                print(f"已更新 {path_name} 为: {new_path}")
        
        input("\n按回车键继续...")
    
    def edit_processing(self):
        """
        修改处理配置
        """
        print("\n修改处理配置:")
        print(f"当前分块大小: {self.config_manager.settings.chunk_size}")
        print(f"当前分块重叠: {self.config_manager.settings.chunk_overlap}")
        print(f"当前最大表格行数: {self.config_manager.settings.max_table_rows}")
        
        print(f"当前日志启用: {'是' if self.config_manager.settings.enable_logging else '否'}")
        
        print("\n可修改的处理参数:")
        print("1. chunk_size - 文档分块大小")
        print("2. chunk_overlap - 文档分块重叠大小")
        print("3. max_table_rows - 最大表格行数")
        print("4. enable_logging - 启用日志")
        
        choice = input("\n请选择要修改的参数 (1-4, 0返回): ").strip()
        
        if choice == '0':
            return
        
        param_map = {
            '1': ('chunk_size', '文档分块大小'),
            '2': ('chunk_overlap', '文档分块重叠大小'),
            '3': ('max_table_rows', '最大表格行数'),
            '4': ('enable_logging', '启用日志')
        }
        
        if choice in param_map:
            param_name, param_desc = param_map[choice]
            current_value = getattr(self.config_manager.settings, param_name)
            print(f"\n当前 {param_desc}: {current_value}")
            
            if param_name == 'enable_logging':
                new_value = input(f"请输入新的 {param_desc} (true/false): ").strip().lower()
                if new_value in ['true', '1', 'yes', 'y']:
                    setattr(self.config_manager.settings, param_name, True)
                    print(f"已更新 {param_desc} 为: 启用")
                elif new_value in ['false', '0', 'no', 'n']:
                    setattr(self.config_manager.settings, param_name, False)
                    print(f"已更新 {param_desc} 为: 禁用")
                else:
                    print("输入无效，请输入 true 或 false")
            else:
                try:
                    new_value = int(input(f"请输入新的 {param_desc}: ").strip())
                    setattr(self.config_manager.settings, param_name, new_value)
                    print(f"已更新 {param_desc} 为: {new_value}")
                except ValueError:
                    print("输入无效，请输入数字")
        
        input("\n按回车键继续...")
    
    def edit_vector_store(self):
        """
        修改向量存储配置
        """
        print("\n修改向量存储配置:")
        print(f"当前向量维度: {self.config_manager.settings.vector_dimension}")
        print(f"当前相似度Top-K: {self.config_manager.settings.similarity_top_k}")
        
        print("\n可修改的向量存储参数:")
        print("1. vector_dimension - 向量维度")
        print("2. similarity_top_k - 相似度Top-K")
        
        choice = input("\n请选择要修改的参数 (1-2, 0返回): ").strip()
        
        if choice == '0':
            return
        
        param_map = {
            '1': ('vector_dimension', '向量维度'),
            '2': ('similarity_top_k', '相似度Top-K')
        }
        
        if choice in param_map:
            param_name, param_desc = param_map[choice]
            current_value = getattr(self.config_manager.settings, param_name)
            print(f"\n当前 {param_desc}: {current_value}")
            
            try:
                new_value = int(input(f"请输入新的 {param_desc}: ").strip())
                setattr(self.config_manager.settings, param_name, new_value)
                print(f"已更新 {param_desc} 为: {new_value}")
            except ValueError:
                print("输入无效，请输入数字")
        
        input("\n按回车键继续...")
    
    def edit_memory(self):
        """
        修改记忆配置
        """
        print("\n修改记忆配置:")
        print(f"当前记忆功能: {'启用' if self.config_manager.settings.memory_enabled else '禁用'}")
        print(f"当前最大记忆大小: {self.config_manager.settings.memory_max_size}")
        
        print("\n可修改的记忆参数:")
        print("1. memory_enabled - 记忆功能开关")
        print("2. memory_max_size - 最大记忆大小")
        
        choice = input("\n请选择要修改的参数 (1-2, 0返回): ").strip()
        
        if choice == '0':
            return
        
        param_map = {
            '1': ('memory_enabled', '记忆功能开关'),
            '2': ('memory_max_size', '最大记忆大小')
        }
        
        if choice in param_map:
            param_name, param_desc = param_map[choice]
            current_value = getattr(self.config_manager.settings, param_name)
            print(f"\n当前 {param_desc}: {current_value}")
            
            if param_name == 'memory_enabled':
                new_value = input(f"请输入新的 {param_desc} (true/false): ").strip().lower()
                if new_value in ['true', '1', 'yes', 'y']:
                    setattr(self.config_manager.settings, param_name, True)
                    print(f"已更新 {param_desc} 为: 启用")
                elif new_value in ['false', '0', 'no', 'n']:
                    setattr(self.config_manager.settings, param_name, False)
                    print(f"已更新 {param_desc} 为: 禁用")
                else:
                    print("输入无效，请输入 true 或 false")
            else:
                try:
                    new_value = int(input(f"请输入新的 {param_desc}: ").strip())
                    setattr(self.config_manager.settings, param_name, new_value)
                    print(f"已更新 {param_desc} 为: {new_value}")
                except ValueError:
                    print("输入无效，请输入数字")
        
        input("\n按回车键继续...")
    
    def edit_api(self):
        """
        修改API配置
        """
        print("\n修改API配置:")
        print("注意: API密钥建议通过环境变量设置，而不是直接修改配置文件")
        print(f"当前DashScope API密钥: {'已配置' if self.config_manager.settings.dashscope_api_key else '未配置'}")
        print(f"当前minerU API密钥: {'已配置' if self.config_manager.settings.mineru_api_key else '未配置'}")
        
        print("\n建议通过以下方式设置API密钥:")
        print("1. 设置环境变量 MY_DASHSCOPE_API_KEY")
        print("2. 设置环境变量 MINERU_API_KEY")
        print("3. 或者在 .env 文件中配置")
        
        input("\n按回车键继续...")
    
    def edit_qa_system(self):
        """
        修改问答系统配置
        """
        print("\n修改问答系统配置:")
        print(f"当前模型名称: {self.config_manager.settings.model_name}")
        print(f"当前温度: {self.config_manager.settings.temperature}")
        print(f"当前最大令牌数: {self.config_manager.settings.max_tokens}")
        
        print("\n可修改的问答系统参数:")
        print("1. model_name - 模型名称")
        print("2. temperature - 温度参数")
        print("3. max_tokens - 最大令牌数")
        
        choice = input("\n请选择要修改的参数 (1-3, 0返回): ").strip()
        
        if choice == '0':
            return
        
        param_map = {
            '1': ('model_name', '模型名称'),
            '2': ('temperature', '温度参数'),
            '3': ('max_tokens', '最大令牌数')
        }
        
        if choice in param_map:
            param_name, param_desc = param_map[choice]
            current_value = getattr(self.config_manager.settings, param_name)
            print(f"\n当前 {param_desc}: {current_value}")
            
            if param_name == 'temperature':
                try:
                    new_value = float(input(f"请输入新的 {param_desc} (0.0-1.0): ").strip())
                    if 0.0 <= new_value <= 1.0:
                        setattr(self.config_manager.settings, param_name, new_value)
                        print(f"已更新 {param_desc} 为: {new_value}")
                    else:
                        print("温度参数应在0.0到1.0之间")
                except ValueError:
                    print("输入无效，请输入数字")
            else:
                new_value = input(f"请输入新的 {param_desc}: ").strip()
                if new_value:
                    if param_name == 'max_tokens':
                        try:
                            new_value = int(new_value)
                        except ValueError:
                            print("最大令牌数应为数字")
                            return
                    setattr(self.config_manager.settings, param_name, new_value)
                    print(f"已更新 {param_desc} 为: {new_value}")
        
        input("\n按回车键继续...")
    
    def validate_config(self):
        """
        验证配置
        """
        print("\n验证配置...")
        validation_results = self.config_manager.validate_config()
        
        print("\n配置验证结果:")
        for key, result in validation_results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {key}: {'通过' if result else '失败'}")
        
        input("\n按回车键继续...")
    
    def save_config(self):
        """
        保存配置
        """
        print("\n保存配置...")
        self.config_manager.save_config()
        print("配置已保存")
        
        input("\n按回车键继续...")
    
    def run(self):
        """
        运行配置编辑器
        """
        while True:
            self.show_menu()
            choice = input("请选择操作 (0-9): ").strip()
            
            if choice == '1':
                self.show_current_config()
            elif choice == '2':
                self.edit_paths()
            elif choice == '3':
                self.edit_processing()
            elif choice == '4':
                self.edit_vector_store()
            elif choice == '5':
                self.edit_qa_system()
            elif choice == '6':
                self.edit_memory()
            elif choice == '7':
                self.edit_api()
            elif choice == '8':
                self.validate_config()
            elif choice == '9':
                self.save_config()
            elif choice == '0':
                print("\n退出配置编辑器")
                break
            else:
                print("无效选择，请重新输入")


def main():
    """
    主函数
    """
    config_file = 'config.json'
    
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    
    editor = ConfigEditor(config_file)
    editor.run()


if __name__ == "__main__":
    main() 