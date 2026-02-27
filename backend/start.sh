#!/bin/bash
# 同时运行 API 服务和定时任务调度器

python api.py &
python scheduler.py

wait
