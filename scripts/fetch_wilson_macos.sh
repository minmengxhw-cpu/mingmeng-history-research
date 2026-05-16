#!/bin/bash
# Wilson Center 1941-1951 民盟相关档案批量下载（Mac 端）
# 用法：在项目根目录跑 bash scripts/fetch_wilson_macos.sh
# 完成后会在项目根目录生成 wilson_v1.zip，拖到 Mattermost 给小C

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 工作目录
OUTDIR="data/wilson_center/documents"
mkdir -p "$OUTDIR"
ZIP_FILE="wilson_v1.zip"

# 25 篇 1941-1951 民盟相关档案
URLS=(
  # 民盟直接相关 ⭐⭐⭐
  "https://digitalarchive.wilsoncenter.org/document/democratic-parties-and-groups-preparatory-committee-convene-political-consultative"
  "https://digitalarchive.wilsoncenter.org/document/communist-party-china-over-last-10-years-secret-brochure-gmd-issued-1-may-1945"

  # 苏联使馆视角下中共-民盟（1945-1948）
  "https://digitalarchive.wilsoncenter.org/document/record-conversation-between-soviet-ambassador-china-apollon-petrov-and-zhou-enlai-and-wang"
  "https://digitalarchive.wilsoncenter.org/document/record-conversation-between-soviet-ambassador-china-apollon-petrov-and-mao-zedong-zhou-0"
  "https://digitalarchive.wilsoncenter.org/document/record-conversation-between-soviet-ambassador-china-apollon-petrov-and-zhou-enlai"
  "https://digitalarchive.wilsoncenter.org/document/record-conversation-between-soviet-ambassador-china-petrov-and-general-zhang-zhizhong-7"
  "https://digitalarchive.wilsoncenter.org/document/cable-no-832-petrov-chongqing-anti-soviet-campaign-manchuria"
  "https://digitalarchive.wilsoncenter.org/document/cable-no-825826-petrov-chongqing-anti-soviet-campaign-manchuria"
  "https://digitalarchive.wilsoncenter.org/document/memorandum-conversation-soviet-ambassador-china-n-v-roshchin-president-chinese-republic"

  # 1949 关键节点（米高扬西柏坡密访 + 刘少奇访苏）⭐⭐⭐⭐
  "https://digitalarchive.wilsoncenter.org/document/anastas-mikoyans-recollections-his-trip-china"
  "https://digitalarchive.wilsoncenter.org/document/113318"
  "https://digitalarchive.wilsoncenter.org/document/memorandum-conversation-between-anastas-mikoyan-and-mao-zedong-1"
  "https://digitalarchive.wilsoncenter.org/document/memorandum-conversation-between-liu-shaoqi-and-stalin"
  "https://digitalarchive.wilsoncenter.org/document/cable-mao-zedong-kovalev-stalin"
  "https://digitalarchive.wilsoncenter.org/document/cable-filippov-stalin-mao-zedong-kovalev"
  "https://digitalarchive.wilsoncenter.org/document/113382"
  "https://digitalarchive.wilsoncenter.org/document/cable-liu-shaoqi-mao-zedong"
  "https://digitalarchive.wilsoncenter.org/document/113353"
  "https://digitalarchive.wilsoncenter.org/document/110393"
  "https://digitalarchive.wilsoncenter.org/document/111240"

  # 罗申大使 1949-50
  "https://digitalarchive.wilsoncenter.org/document/diary-nv-roshchin-memorandum-conversation-prime-minister-zhou-enlai-10-november-1949"
)

TOTAL=${#URLS[@]}
echo -e "${GREEN}== Wilson Center 民盟相关档案下载 ==${NC}"
echo -e "共 ${TOTAL} 篇文档，预计 5-10 分钟"
echo -e "保存到: $OUTDIR"
echo ""

cd "$OUTDIR"

DONE=0
SKIP=0
FAIL=0

for url in "${URLS[@]}"; do
  slug=$(basename "$url")
  outfile="${slug}.html"

  if [ -f "$outfile" ] && [ -s "$outfile" ]; then
    echo -e "${YELLOW}[skip]${NC} $outfile (已下载)"
    SKIP=$((SKIP+1))
    continue
  fi

  echo -n "[抓取] $slug ... "

  # 用浏览器 UA + 完整 headers 避免被反爬
  if curl -sL --max-time 30 \
    -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
    -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
    -H "Accept-Language: en-US,en;q=0.9,zh-CN;q=0.8" \
    -o "$outfile" \
    "$url"; then
    size=$(stat -f%z "$outfile" 2>/dev/null || stat -c%s "$outfile" 2>/dev/null)
    if [ "$size" -gt 5000 ]; then
      echo -e "${GREEN}OK${NC} (${size} bytes)"
      DONE=$((DONE+1))
    else
      echo -e "${RED}FAIL${NC} (响应过小: ${size} bytes，可能被反爬)"
      FAIL=$((FAIL+1))
      rm -f "$outfile"
    fi
  else
    echo -e "${RED}FAIL${NC} (网络错误)"
    FAIL=$((FAIL+1))
    rm -f "$outfile"
  fi

  # 礼貌停顿，避免触发反爬
  sleep 2
done

cd - > /dev/null
cd data
zip -rq "../$ZIP_FILE" wilson_center/
cd ..

echo ""
echo -e "${GREEN}== 完成 ==${NC}"
echo -e "成功: $DONE / 跳过: $SKIP / 失败: $FAIL"
echo -e "打包: $(pwd)/$ZIP_FILE"
ZIP_SIZE=$(stat -f%z "$ZIP_FILE" 2>/dev/null || stat -c%s "$ZIP_FILE" 2>/dev/null)
ZIP_KB=$((ZIP_SIZE / 1024))
echo -e "大小: ${ZIP_KB} KB"
echo ""
echo -e "${YELLOW}下一步：${NC}"
echo -e "  1. 打开 Finder，在项目根目录找到 ${GREEN}${ZIP_FILE}${NC}"
echo -e "  2. 把这个 zip 文件拖到 Mattermost 跟小C 的频道里"
echo -e "  3. 小C 会自动解析 → 翻译 → 入库 → 上线 /sources/wilson 栏目"
