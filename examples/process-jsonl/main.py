#!/usr/bin/env python3
"""子进程插件示例：每次收到 tick 就输出一条 JSONL 报文。

协议要点：
- stdout 每行一个 JSON 对象（顶层键按能力分区）
- stderr 每行会进插件日志面板
- 宿主每 intervalSeconds 往 stdin 写一行 {"type":"tick"}
- 也可以不等 tick，自己定时往 stdout 推
"""
import json
import math
import random
import sys
import time

n = 0
history = []


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main():
    global n
    emit({"type": "snapshot", "cards": [
        {"id": "about", "title": "子进程插件", "subtitle": "stdout JSONL",
         "body": "这一行来自 Python 子进程。"}
    ]})
    while True:
        line = sys.stdin.readline()
        if not line:
            time.sleep(0.5)
            continue
        n += 1
        value = 50 + 30 * math.sin(n / 6) + random.uniform(-3, 3)
        history.append(round(value, 1))
        history[:] = history[-24:]
        emit({
            "type": "patch",
            "metrics": [{"id": "wave", "label": "实时波形", "value": round(value, 1),
                         "unit": "", "min": 0, "max": 100, "history": history,
                         "color": "#44BB66"}],
            "cards": [{"id": "status", "title": "运行状态",
                       "rows": [{"label": "tick", "value": str(n)},
                                {"label": "时间", "value": time.strftime("%H:%M:%S")}]}],
        })
        if n % 12 == 0:
            emit({"type": "patch", "notifications": [
                {"id": "beat", "title": "插件心跳", "body": f"已运行 {n} 个周期", "level": "info"}
            ]})


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
