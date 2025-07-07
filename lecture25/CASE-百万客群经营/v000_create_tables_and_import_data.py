"""
程序说明：

## 1. 执行SQL脚本创建数据库表
   - 创建customer_base表和customer_behavior_assets表
   - 创建相关索引和约束

## 2. 导入CSV数据到数据库
   - 读取customer_base.csv和customer_behavior_assets.csv
   - 将数据导入到对应的数据库表中
"""

import pandas as pd
import cx_Oracle
import os
from datetime import datetime
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Oracle数据库连接配置
ORACLE_DSN = cx_Oracle.makedsn('192.168.43.11', 1521, service_name='FREEPDB1')
ORACLE_USER = 'dbtest'
ORACLE_PWD = 'test'

class DatabaseManager:
    """
    数据库管理类
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
        执行SQL文件
        :param sql_file: SQL文件路径
        """
        print(f"\n执行SQL文件: {sql_file}")
        
        # 读取SQL文件内容
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句
        sql_statements = sql_content.split(';')
        
        # 执行每条SQL语句
        with self.get_connection() as connection:
            cursor = connection.cursor()
            for statement in sql_statements:
                if statement.strip():
                    try:
                        cursor.execute(statement)
                        connection.commit()
                    except cx_Oracle.Error as e:
                        if 'ORA-00942' in str(e):  # 表不存在的错误，可以忽略
                            continue
                        print(f"执行SQL语句时出错: {e}")
                        print(f"问题SQL语句: {statement}")
        
        print("SQL文件执行完成")

    def preprocess_data(self, df):
        """
        预处理数据，处理数据类型转换
        :param df: pandas DataFrame
        :return: 处理后的DataFrame
        """
        # 处理NaN值
        df = df.replace({np.nan: None})
        
        # 处理数值类型
        for col in df.select_dtypes(include=['int64', 'float64']).columns:
            df[col] = df[col].astype('float64')
        
        # 处理布尔类型
        for col in df.select_dtypes(include=['bool']).columns:
            df[col] = df[col].astype('int')
            
        return df

    def import_csv_data(self, table_name, csv_file):
        """
        将CSV数据导入到数据库表
        :param table_name: 表名
        :param csv_file: CSV文件路径
        """
        print(f"\n导入数据到表 {table_name}")
        
        try:
            # 读取CSV文件
            df = pd.read_csv(csv_file)
            
            # 处理日期时间列
            if table_name == 'customer_base':
                if 'open_account_date' in df.columns:
                    df['open_account_date'] = pd.to_datetime(df['open_account_date'])
            elif table_name == 'customer_behavior_assets':
                date_columns = ['last_app_login_time', 'last_contact_time', 'marketing_cool_period']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col])
            
            # 预处理数据
            df = self.preprocess_data(df)
            
            # 准备INSERT语句
            columns = df.columns.tolist()
            placeholders = ':' + ', :'.join(str(i+1) for i in range(len(columns)))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # 批量插入数据
            with self.get_connection() as connection:
                cursor = connection.cursor()
                batch_size = 1000
                
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    data = [tuple(x) for x in batch.values]
                    try:
                        cursor.executemany(insert_sql, data)
                        connection.commit()
                        print(f"已导入 {i + len(batch)} 条记录")
                    except Exception as e:
                        print(f"导入数据时出错: {e}")
                        connection.rollback()
            
            print(f"完成数据导入到表 {table_name}")
            
        except Exception as e:
            print(f"处理CSV文件时出错: {e}")
            raise

def main():
    """
    主函数
    """
    try:
        # 创建数据库管理器实例
        db_manager = DatabaseManager()
        
        # 执行建表SQL脚本
        db_manager.execute_sql_file('v000_create_tables.sql')
        
        # 导入数据
        db_manager.import_csv_data('customer_base', 'customer_base.csv')
        db_manager.import_csv_data('customer_behavior_assets', 'customer_behavior_assets.csv')
        
        print("\n所有操作已完成")
        
    except Exception as e:
        print(f"程序执行出错: {e}")

if __name__ == "__main__":
    main() 