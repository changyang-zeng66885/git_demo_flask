# 创建应用实例
import sys

from wxcloudrun import app

# 启动Flask Web服务
if __name__ == '__main__':
    #app.run(host=sys.argv[1], port=sys.argv[2]) # 提交云开发
    app.run(host = '127.0.0.1',port = '5000') # 本地调试
