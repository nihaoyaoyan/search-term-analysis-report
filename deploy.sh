#!/bin/bash
# ============================================================
# 搜索词分析报告 - GitHub 一键部署脚本
# ============================================================
# 使用方法：在 GitHub 先手动创建空仓库（不要添加 README），然后运行：
#   bash deploy.sh https://github.com/nihaoyaoyan/search-term-analysis-report.git

set -e

REPO_URL="${1:-}"
if [ -z "$REPO_URL" ]; then
    echo "Usage: bash deploy.sh <你的GitHub仓库URL>"
    echo "Example: bash deploy.sh https://github.com/nihaoyaoyan/search-term-analysis-report.git"
    exit 1
fi

echo "=== 搜索词分析报告 - GitHub 部署 ==="
echo "目标仓库: $REPO_URL"
echo ""

# 1. Commit all files
echo "[1/3] 提交所有文件..."
git add index.html analysis.py analysis_deep.py build_report.py deploy.sh
git commit -m "feat: 生鲜电商搜索词分析报告 (2025.12-2026.05)

- 6个月搜索词趋势分析，含5张交互式Chart.js可视化图表
- 分层负面关键词架构（账户级/广告系列级/广告组级）
- 品类季节性分析 & 意图分类（商业型/信息型/交易型/竞品型）
- 45个高潜力长尾关键词机会
- 8项优先级优化策略路线图
- N-gram浪费信号分析

数据来源: 搜索词数据(2025年12月-2026年5月) 共2,282条搜索词" || echo "Nothing to commit"

# 2. Set remote and push
echo ""
echo "[2/3] 推送至 GitHub..."
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
git push -u origin main --force

# 3. Done
echo ""
echo "[3/3] 部署完成!"
echo ""
echo "============================================"
echo "  报告地址: ${REPO_URL%.git}"
echo "  在线预览: https://nihaoyaoyan.github.io/$(basename "$REPO_URL" .git)/"
echo ""
echo "  如需启用 GitHub Pages:"
echo "  1. 打开仓库 Settings > Pages"
echo "  2. Source: Deploy from a branch"
echo "  3. Branch: main, folder: / (root)"
echo "  4. 点击 Save"
echo "============================================"
