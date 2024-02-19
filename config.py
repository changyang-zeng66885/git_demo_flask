import os

# 是否开启debug模式
DEBUG = True

# 读取数据库环境变量
username = os.environ.get("MYSQL_USERNAME", 'root')
password = os.environ.get("MYSQL_PASSWORD", 'nqD5phNV')
db_address = os.environ.get("MYSQL_ADDRESS", 'sh-cynosdbmysql-grp-psweq7r0.sql.tencentcdb.com:29185')
amap_key = os.environ.get("AMAP_KEY", '7d0c9dc99c8b03db5e7e280c1340b406')

