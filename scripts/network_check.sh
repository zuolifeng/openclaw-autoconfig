#!/usr/bin/env bash
# 网络检测：判断是否能访问国际源，返回 "global" 或 "cn"

TIMEOUT=5

check_url() {
    curl -s --connect-timeout "$TIMEOUT" -o /dev/null -w "%{http_code}" "$1" 2>/dev/null
}

# 检测是否能访问 npmjs.com（国际源）
STATUS=$(check_url "https://registry.npmjs.org/")

if [ "$STATUS" = "200" ] || [ "$STATUS" = "301" ] || [ "$STATUS" = "302" ]; then
    echo "global"
else
    echo "cn"
fi
