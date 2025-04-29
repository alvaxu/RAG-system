
ALTER SESSION SET CONTAINER=FREEPDB1
DROP USER DBTEST CASCADE

DROP TABLESPACE testdbspace


-- 在PDB中创建表空间
CREATE TABLESPACE testdbspace
DATAFILE '/opt/oracle/oradata/FREE/test01.dbf'
SIZE 100M
REUSE  
AUTOEXTEND ON
NEXT 10M
MAXSIZE UNLIMITED
EXTENT MANAGEMENT LOCAL
SEGMENT SPACE MANAGEMENT AUTO;


CREATE USER dbtest IDENTIFIED BY test
DEFAULT TABLESPACE testdbspace
TEMPORARY TABLESPACE temp
QUOTA UNLIMITED ON testdbspace;

-- 授予连接权限
GRANT CREATE SESSION TO dbtest;

-- 授予在表空间上创建表的权限
GRANT CREATE TABLE TO dbtest;

-- 授予创建序列的权限(可选)
GRANT CREATE SEQUENCE TO dbtest;

-- 授予创建视图的权限(可选)
GRANT CREATE VIEW TO dbtest;

-- 授予创建过程的权限(可选)
GRANT CREATE PROCEDURE TO dbtest;

-- 检查用户默认表空间
SELECT username, default_tablespace, temporary_tablespace 
FROM dba_users 
WHERE username = 'DBTEST';

-- 检查用户表空间配额
SELECT tablespace_name, bytes/1024/1024 "USED(MB)", max_bytes/1024/1024 "MAX(MB)" 
FROM dba_ts_quotas 
WHERE username = 'DBTEST';

-- 检查用户系统权限
SELECT * FROM dba_sys_privs WHERE grantee = 'DBTEST';

-- 检查用户角色权限
SELECT * FROM dba_role_privs WHERE grantee = 'DBTEST';





-- 授予资源角色(包含CREATE TABLE, CREATE SEQUENCE等权限)
GRANT RESOURCE TO dbtest;
