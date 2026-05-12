#!/bin/bash
# pdf-to-md.sh — PDF/图片转 Markdown（MinerU 免登录轻量接口）
# Usage: bash pdf-to-md.sh <input_file> <output_md>
# 限制：单文件 ≤10MB，≤20页，按 IP 限频

set -euo pipefail

INPUT="$1"
OUTPUT="$2"
API="https://mineru.net/api/v1/agent"
POLL_MAX=20
POLL_SLEEP=10

# 检查文件大小（≤10MB）
SIZE=$(stat -c%s "$INPUT" 2>/dev/null || stat -f%z "$INPUT" 2>/dev/null)
if [ "$SIZE" -gt 10485760 ]; then
  echo "ERROR: 文件超过 10MB 限制（当前 $(( SIZE / 1048576 )) MB），需要配置 MinerU Token" >&2
  exit 1
fi

FILENAME=$(basename "$INPUT")

# Step 1: 提交转换请求
SUBMIT_RESP=$(curl -s -X POST "$API/parse/file" \
  -H 'Content-Type: application/json' \
  --data-raw "{\"file_name\":\"$FILENAME\",\"language\":\"ch\",\"is_ocr\":true}")

# 用 Python 解析 JSON（正确处理 Unicode 转义如 &）
parse_json() {
  echo "$1" | /c/Users/Administrator/AppData/Local/Python/bin/python.exe -c "
import sys, json
data = json.load(sys.stdin)
keys = sys.argv[1].split('.')
val = data
for k in keys:
    if isinstance(val, dict):
        val = val.get(k, '')
    else:
        val = ''
        break
print(val)
" "$2"
}

TASK_ID=$(parse_json "$SUBMIT_RESP" "data.task_id")
UPLOAD_URL=$(parse_json "$SUBMIT_RESP" "data.file_url")

if [ -z "$TASK_ID" ] || [ -z "$UPLOAD_URL" ]; then
  echo "ERROR: 提交失败 - $SUBMIT_RESP" >&2
  exit 1
fi

# Step 2: 上传文件
UPLOAD_HTTP=$(curl -s -X PUT -T "$INPUT" "$UPLOAD_URL" -w '%{http_code}' 2>/dev/null | tail -1)
if [ "$UPLOAD_HTTP" != "200" ] && [ "$UPLOAD_HTTP" != "201" ]; then
  echo "ERROR: 上传失败 (HTTP $UPLOAD_HTTP)" >&2
  exit 1
fi

# Step 3: 轮询结果
for i in $(seq 1 $POLL_MAX); do
  sleep $POLL_SLEEP
  POLL_RESP=$(curl -s "$API/parse/$TASK_ID")

  STATE=$(parse_json "$POLL_RESP" "data.state")

  if [ "$STATE" = "done" ]; then
    MD_URL=$(parse_json "$POLL_RESP" "data.markdown_url")
    if [ -n "$MD_URL" ]; then
      curl -s -L "$MD_URL" -o "$OUTPUT"
      echo "OK: $OUTPUT"
      exit 0
    fi
  fi

  if [ "$STATE" = "failed" ]; then
    ERR=$(parse_json "$POLL_RESP" "data.err_msg")
    echo "ERROR: 转换失败 - $ERR" >&2
    exit 1
  fi

  echo "  轮询 $i/$POLL_MAX: $STATE" >&2
done

echo "ERROR: 轮询超时（${POLL_MAX}次）" >&2
exit 1
