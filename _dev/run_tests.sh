#!/bin/bash
# Runs the main checks on both versions of the guide. Usage (from the repo root): bash _dev/run_tests.sh
# Needs: python3, playwright (chromium). Uses http://localhost:8765 serving /tmp.
R=$(cd "$(dirname "$0")" && pwd)
cp "$R/src/guide_claude.html" /tmp/ix.html
cp "$R/src/guide_github.html" /tmp/gh.html
python3 "$R/build_gh.py" /tmp/gh.html /tmp/ghsplit >/dev/null || exit 1
curl -s -o /dev/null localhost:8765/ix.html || { (setsid nohup python3 -m http.server 8765 -d /tmp >/dev/null 2>&1 </dev/null &); sleep 1; }
cd "$R/tests"; fail=0
for t in test29.py test30.py test31.py test32.py test33.py test34.py test23.py test26.py; do
  r=$(timeout 400 python3 $t 2>&1 | grep -E "^FAILS" | tail -1); echo "claude  $t: ${r:-no result}"; [ "$r" = "FAILS: []" ] || fail=1; done
for t in test27.py test31.py test32.py test33.py; do
  r=$(timeout 400 python3 $t http://localhost:8765/ghsplit/index.html 2>&1 | grep -E "^FAILS" | tail -1); echo "github  $t: ${r:-no result}"; [ "$r" = "FAILS: []" ] || fail=1; done
[ $fail = 0 ] && echo "ALL GREEN" || echo "SOME CHECKS FAILED"; exit $fail
