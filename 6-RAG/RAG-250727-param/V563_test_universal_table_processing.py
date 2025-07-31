'''
程序说明：
## 1. 测试通用表格处理方法
## 2. 验证表格语义理解和结构化表示
## 3. 检查LLM对表格数据的理解能力
'''

import logging
from config.config_manager import ConfigManager
from document_processing.table_processor import ConfigurableTableProcessor, ConfigurableTableChunkGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_universal_table_processing():
    """
    测试通用表格处理方法
    """
    try:
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.settings.to_dict()
        
        # 初始化表格处理器
        processor = ConfigurableTableProcessor(config)
        
        # 测试表格HTML内容
        test_table_html = """
        <html><body><table><tr><td></td><td>2023A</td><td>2024A</td><td>2025E</td><td>2026E</td><td>2027E</td></tr>
        <tr><td>营业收入 (百万元)</td><td>45,250</td><td>57,796</td><td>68,204</td><td>79,507</td><td>91,110</td></tr>
        <tr><td>增长比率 (%)</td><td>-8.61</td><td>27.72</td><td>18.01</td><td>16.57</td><td>14.59</td></tr>
        <tr><td>净利润 (百万元)</td><td>4,823</td><td>3,699</td><td>5,075</td><td>6,228</td><td>7,542</td></tr>
        <tr><td>增长比率 (%)</td><td>-60.25</td><td>-23.31</td><td>37.20</td><td>22.73</td><td>21.10</td></tr>
        <tr><td>每股收益(元)</td><td>0.60</td><td>0.46</td><td>0.64</td><td>0.78</td><td>0.94</td></tr>
        <tr><td>市盈率(倍)</td><td>139.79</td><td>182.27</td><td>132.85</td><td>108.24</td><td>89.38</td></tr></table></body></html>
        """
        
        logger.info("=== 测试通用表格处理方法 ===")
        
        # 解析表格
        table_info = processor.parse_html_table(test_table_html, "财务数据表格")
        
        logger.info(f"表格解析结果:")
        logger.info(f"  表格ID: {table_info.table_id}")
        logger.info(f"  表格类型: {table_info.table_type}")
        logger.info(f"  行数: {table_info.row_count}, 列数: {table_info.column_count}")
        logger.info(f"  表头: {table_info.headers}")
        logger.info("")
        
        # 生成结构化文本
        chunk_generator = ConfigurableTableChunkGenerator(config)
        structured_text = chunk_generator._table_to_structured_text(table_info)
        
        logger.info("=== 结构化文本输出 ===")
        print(structured_text)
        logger.info("")
        

        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    test_universal_table_processing() 