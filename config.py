import os

# 是否开启debug模式
DEBUG = True

# 读取数据库环境变量（这里是不完整的代码，完整版代码保存在config.json中了）
username = os.environ.get("MYSQL_USERNAME", 'root')
password = os.environ.get("MYSQL_PASSWORD", 'n')
db_address = os.environ.get("MYSQL_ADDRESS", 'sh')
amap_key = os.environ.get("AMAP_KEY", '7d0')

