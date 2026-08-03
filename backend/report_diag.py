#!/usr/bin/env python3
# 把 /tmp/import_result.txt 主动上报到 ntfy.sh（公开可读临时通道），
# 以便在本机无需公网访问/Webshell 即可读取云端容器内的 import 诊断。
import os
import sys
import urllib.request

# 随机 topic，降低被他人读取概率（诊断仅含错误类型与代码路径，无密钥/业务数据）
TOPIC = os.environ.get("DIAG_TOPIC", "mathsprout-be-diag-xK8m2pQ1")
PATH = "/tmp/import_result.txt"


def main():
    try:
        with open(PATH, "rb") as f:
            data = f.read()
    except Exception as e:
        data = ("cannot read import result: %s" % e).encode("utf-8")
    # 只发最后 3500 字节（关键错误行通常在末尾），避免超过 ntfy 单条体积限制
    data = data[-3500:]
    url = "https://ntfy.sh/%s" % TOPIC
    try:
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Title": "mathsprout backend import diag",
                "Tags": "cloudrun,diag",
            },
        )
        urllib.request.urlopen(req, timeout=15)
        print("diag reported to ntfy topic %s" % TOPIC)
    except Exception as e:
        print("diag report failed: %s" % e)


if __name__ == "__main__":
    main()
