#!/bin/sh
# 자동 시험 전부 돌리기: sh tests/run.sh   (python3 + playwright 필요: pip install playwright && playwright install chromium)
cd "$(dirname "$0")/.." && python3 build.py >/dev/null && cd tests || exit 1
fail=0
for t in t22 t40 t41 t42 t43 t44 t46 t47 t49 t50 t51 t53 t60 t62 t64 t65 t66 t67 t68 t69; do
  out=$(timeout 400 python3 $t.py 2>&1)
  status=$?
  bad=$(printf "%s\n" "$out" | grep -E "FAIL|ERR \[.+\]|Traceback")
  if [ "$status" -ne 0 ] || [ -n "$bad" ]; then echo "✗ $t (exit $status)"; printf "%s\n" "$out" | tail -35; fail=1; else echo "✓ $t"; fi
done
exit $fail
