from app import app
import asyncio
import hypercorn.asyncio
import socket
import logging

# 禁用 Hypercorn 默认的访问日志
logging.getLogger('hypercorn.access').setLevel(logging.WARNING)

def get_local_ip():
    try:
        # 获取本机IP地址
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'localhost'

async def main():
    config = hypercorn.Config()
    config.bind = ["0.0.0.0:5001"]
    config.accesslog = None  # 禁用访问日志
    
    local_ip = get_local_ip()
    print(f"\n服务已启动，请通过以下地址访问：")
    print(f"- 本地访问: http://localhost:5001")
    print(f"- 局域网访问: http://{local_ip}:5001")
    print("\n按 CTRL+C 停止服务\n")
    
    await hypercorn.asyncio.serve(app, config)

if __name__ == "__main__":
    asyncio.run(main()) 