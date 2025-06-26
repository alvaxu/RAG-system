from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine

#目前采用可以调通的方法如下：
#1.创建cx_Oracle连接
import cx_Oracle
dsn = cx_Oracle.makedsn('192.168.43.11', 1521, service_name='FREEPDB1')  # 替换实际主机名
conn = cx_Oracle.connect(user="dbtest", password="test", dsn=dsn)

# print(conn.version)  # 输出版本号表示成功
# conn.close()

#2.转换为SQLDatabase实例
db = SQLDatabase.from_uri(f"oracle+cx_oracle://", engine_args={"creator": lambda: conn})

#3. 执行测试查询
result = db.run("SELECT count(*) FROM stock_data")
print(result)