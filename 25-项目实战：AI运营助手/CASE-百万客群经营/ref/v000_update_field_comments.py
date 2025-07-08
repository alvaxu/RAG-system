"""
程序说明：

## 1. 本程序用于更新Oracle数据库中的字段注释
## 2. 执行v000_update_field_comments.sql文件中的SQL语句
## 3. 更新完成后验证字段注释的更新结果
"""

import cx_Oracle
import pandas as pd
import os

# Oracle数据库连接配置
ORACLE_DSN = cx_Oracle.makedsn('192.168.43.11', 1521, service_name='FREEPDB1')
ORACLE_USER = 'dbtest'
ORACLE_PWD = 'test'

class CommentUpdater:
    """
    数据库字段注释更新类
    """
    def __init__(self, encoding='UTF-8'):
        """
        初始化数据库连接
        :param encoding: 字符编码
        """
        self.encoding = encoding
        
    def get_connection(self):
        """
        获取数据库连接
        :return: 数据库连接对象
        """
        return cx_Oracle.connect(
            user=ORACLE_USER,
            password=ORACLE_PWD,
            dsn=ORACLE_DSN,
            encoding=self.encoding
        )

    def execute_sql_file(self, sql_file):
        """
        执行SQL文件中的语句
        :param sql_file: SQL文件路径
        """
        print(f"\n执行SQL文件: {sql_file}")
        
        # 读取SQL文件内容
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        # 执行每条SQL语句
        with self.get_connection() as connection:
            cursor = connection.cursor()
            for statement in sql_statements:
                try:
                    cursor.execute(statement)
                    connection.commit()
                except cx_Oracle.Error as e:
                    print(f"执行SQL语句时出错: {e}")
                    print(f"问题SQL语句: {statement}")
        
        print("SQL文件执行完成")

    def verify_comments(self):
        """
        验证字段注释的更新结果
        :return: None
        """
        print("\n验证字段注释更新结果:")
        
        # 查询字段注释的SQL
        sql = """
        SELECT table_name, column_name, comments 
        FROM user_col_comments 
        WHERE table_name IN ('CUSTOMER_BASE', 'CUSTOMER_BEHAVIOR_ASSETS')
        AND column_name IN (
            'GENDER', 'LIFECYCLE_STAGE', 'MARRIAGE_STATUS', 'CITY_LEVEL',
            'DEPOSIT_FLAG', 'FINANCIAL_FLAG', 'FUND_FLAG', 'INSURANCE_FLAG',
            'ASSET_LEVEL', 'CONTACT_RESULT'
        )
        ORDER BY table_name, column_name
        """
        
        try:
            with self.get_connection() as connection:
                # 使用pandas读取查询结果
                df = pd.read_sql(sql, connection)
                
                # 打印结果
                print("\n更新后的字段注释:")
                print(df.to_string(index=False))
                
        except Exception as e:
            print(f"验证注释时出错: {e}")

def main():
    """
    主函数
    """
    try:
        # 创建CommentUpdater实例
        updater = CommentUpdater()
        
        # 执行SQL文件
        updater.execute_sql_file('v000_update_field_comments.sql')
        
        # 验证更新结果
        updater.verify_comments()
        
        print("\n所有操作已完成")
        
    except Exception as e:
        print(f"程序执行出错: {e}")

if __name__ == "__main__":
    main() 