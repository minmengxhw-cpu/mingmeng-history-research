#!/usr/bin/env python3
import sys
import json
import subprocess
from pathlib import Path

# 这里假设 OpenClaw 会将消息输出到 stdout 或通过 API 提供
# 我们将实现一个简单的消息监听循环
def process_message(sender, content):
    print(f"收到来自 {sender} 的消息: {content}")
    
    # 示例指令转发逻辑：
    # 如果消息包含“档案”，调用搜索脚本或返回检索结果
    if "档案" in content:
        # 直接调用您的索引构建或查询逻辑
        print("检测到档案查询请求...")
        # 此处可添加调用 app.py 或检索 sqlite 的逻辑
    
    # 如果有更多指令，可以在此处扩展

def main():
    print("桥接器已启动，等待微信消息...")
    # 假设我们通过标准输入监听 OpenClaw 的输出流
    for line in sys.stdin:
        try:
            msg = json.loads(line)
            process_message(msg.get("sender"), msg.get("content"))
        except:
            continue

if __name__ == "__main__":
    main()
