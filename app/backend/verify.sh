#!/bin/bash
set +e
cd /opt/visual-agent/app/backend
export PATH=.venv/bin:$PATH

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0

check() {
  if eval "$2" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ $1${NC}"; ((PASS++))
  else
    echo -e "${RED}❌ $1${NC}"; ((FAIL++))
  fi
}
warn_check() {
  if eval "$2" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ $1${NC}"; ((PASS++))
  else
    echo -e "${YELLOW}⚠️  $1${NC}"; ((WARN++))
  fi
}

echo "======================================="
echo "  视觉Agent 交付验证"
echo "  $(date)"
echo "======================================="
echo ""

echo "--- 第1层：文件存在性 ---"
check "visual_assets.py" "[ -s app/schemas/visual_assets.py ]"
check "llm_client.py" "[ -s app/services/llm_client.py ]"
check "prompt_loader.py" "[ -s app/services/prompt_loader.py ]"
check "visual_agent.py" "[ -s app/services/visual_agent.py ]"
check "brief_parser.py" "[ -s app/services/brief_parser.py ]"
check "markdown_exporter.py" "[ -s app/services/markdown_exporter.py ]"
check "visual_tasks.py" "[ -s app/api/visual_tasks.py ]"
check "main_image.j2" "[ -s app/prompts/main_image.j2 ]"
check "system.j2" "[ -s app/prompts/system.j2 ]"
warn_check ".env" "[ -s .env ]"
echo ""

echo "--- 第2层：编译 ---"
for f in app/schemas/visual_assets.py app/services/llm_client.py app/services/prompt_loader.py app/services/visual_agent.py app/services/brief_parser.py app/services/markdown_exporter.py app/api/visual_tasks.py; do
  [ -f "$f" ] && check "$f" ".venv/bin/python -m py_compile $f"
done
echo ""

echo "--- 第3层：导入链 ---"
for mod in app.schemas.visual_assets app.services.llm_client app.services.prompt_loader app.services.visual_agent app.services.brief_parser app.services.markdown_exporter; do
  check "$mod" ".venv/bin/python -c 'import sys; sys.path.insert(0,\".\"); __import__(\"$mod\")'"
done
echo ""

echo "--- 第4层：测试 ---"
if pytest tests/unit/ --tb=no -q > /tmp/test_out.txt 2>&1; then
  echo -e "${GREEN}✅ 单元测试全部通过${NC}"; ((PASS++))
else
  echo -e "${RED}❌ 有失败${NC}"; ((FAIL++))
fi
cat /tmp/test_out.txt | tail -1
echo ""

echo "======================================="
echo -e "  结果: ${GREEN}$PASS 通过${NC}  ${RED}$FAIL 失败${NC}  ${YELLOW}$WARN 警告${NC}"
echo "======================================="
[ $FAIL -gt 0 ] && exit 1 || echo -e "${GREEN}所有检查通过${NC}"
