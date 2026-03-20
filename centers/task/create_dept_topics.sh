#!/bin/bash
set -euo pipefail

XUZHI_HOME="$HOME/xuzhi_genesis"
CENTERS_DIR="$XUZHI_HOME/centers"

# 确保所有部门目录存在
mkdir -p "$CENTERS_DIR/mind"
mkdir -p "$CENTERS_DIR/science"
mkdir -p "$CENTERS_DIR/engineering"
mkdir -p "$CENTERS_DIR/philosophy"
mkdir -p "$CENTERS_DIR/intelligence"

# 心智部
cat > "$CENTERS_DIR/mind/topics.json" << 'EOF'
{
  "department": "心智部",
  "topics": [
    "学习科学",
    "认知科学",
    "神经科学",
    "社会科学",
    "增强Agent自主性、意向立场、差异化"
  ],
  "rss_feeds": []
}
EOF

# 科学部
cat > "$CENTERS_DIR/science/topics.json" << 'EOF'
{
  "department": "科学部",
  "topics": [
    "AI4S（全科）+开放式递归自我迭代",
    "复杂系统科学/混沌",
    "宇宙学+宇宙论",
    "可计算物质"
  ],
  "rss_feeds": []
}
EOF

# 工学部
cat > "$CENTERS_DIR/engineering/topics.json" << 'EOF'
{
  "department": "工学部",
  "topics": [
    "WSL-Ubuntu/Linux 系统+CLI，计算机架构",
    "计算机安全",
    "数据科学，智能体架构，上下文工程，Tokens效率",
    "可计算物质"
  ],
  "rss_feeds": []
}
EOF

# 哲学部
cat > "$CENTERS_DIR/philosophy/topics.json" << 'EOF'
{
  "department": "哲学部",
  "topics": [
    "加速主义",
    "人工智能研究/异种智能研究，技术哲学",
    "后人类议程",
    "思辨实在论",
    "心灵哲学/精神分析",
    "宇宙学+宇宙论"
  ],
  "rss_feeds": []
}
EOF

# 情报部
cat > "$CENTERS_DIR/intelligence/topics.json" << 'EOF'
{
  "department": "情报部",
  "topics": [
    "RSS每日前沿采集",
    "知识图谱构建",
    "信息摘要与提炼"
  ],
  "rss_feeds": [
    "https://arxiv.org/rss/cs.AI",
    "https://www.technologyreview.com/feed/"
  ]
}
EOF

echo "✅ 部门主题文件已创建。"
