import pandas as pd
import numpy as np
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load data
months_order = ["2025年12月","2026年01月","2026年02月","2026年03月","2026年04月","2026年05月"]
files = {
    "2025年12月": r"C:/Users/赵/Downloads/搜索词数据(2025年12月).xlsx",
    "2026年01月": r"C:/Users/赵/Downloads/搜索词数据(2026年01月).xlsx",
    "2026年02月": r"C:/Users/赵/Downloads/搜索词数据(2026年02月).xlsx",
    "2026年03月": r"C:/Users/赵/Downloads/搜索词数据(2026年03月).xlsx",
    "2026年04月": r"C:/Users/赵/Downloads/搜索词数据(2026年04月).xlsx",
    "2026年05月": r"C:/Users/赵/Downloads/搜索词数据(2026年05月).xlsx",
}

all_data = {}
for month, path in files.items():
    df = pd.read_excel(path)
    df['月份'] = month
    all_data[month] = df

merged = pd.concat(all_data.values(), ignore_index=True)

# Aggregate
monthly = merged.groupby('月份').agg(
    总支付金额=('支付金额', 'sum'),
    总订单数=('支付订单数', 'sum'),
    总曝光=('商卡曝光人数', 'sum'),
    总点击=('商品点击人数', 'sum'),
    搜索词数=('搜索词', 'nunique'),
).reindex(months_order)
monthly['CTR%'] = (monthly['总点击'] / monthly['总曝光'] * 100).round(2)
monthly['CVR%'] = (monthly['总订单数'] / monthly['总点击'] * 100).round(2)
monthly['客单价'] = (monthly['总支付金额'] / monthly['总订单数']).round(2)

# Categories
categories = {
    '三文鱼': ['三文鱼', '三文', '三文魚'],
    '减脂餐/健康': ['减脂', '减肥', '轻食', '健身', '代餐', '控卡', '低脂', '低卡', '瘦身', '燃脂', '健康餐', '减重', '健康食谱'],
    '虾类': ['虾', '甜虾', '北极虾', '黑虎虾', '虾仁', '虾滑', '虾尾', '罗氏虾', '竹节虾', '大虾', '青虾', '基围虾'],
    '生蚝': ['生蚝', '乳山生蚝', '蚝', '牡蛎'],
    '鱼类（其他）': ['鲅鱼', '带鱼', '黄花鱼', '鳕鱼', '金枪鱼', '巴沙鱼', '龙利鱼', '多宝鱼', '鲈鱼', '鳜鱼', '马哈鱼', '鱼柳', '鱼排', '鱼片', '深海鱼'],
    '其他': [],
}

def classify_query(query):
    q = str(query)
    for cat, kws in categories.items():
        if cat == '其他': continue
        for kw in kws:
            if kw in q:
                return cat
    return '其他'

merged['品类'] = merged['搜索词'].apply(classify_query)

# Category stats
cat_stats = merged.groupby('品类').agg(
    总支付金额=('支付金额', 'sum'),
    总订单数=('支付订单数', 'sum'),
    总曝光=('商卡曝光人数', 'sum'),
    总点击=('商品点击人数', 'sum'),
    搜索词数=('搜索词', 'nunique'),
    有转化词数=('支付订单数', lambda x: (x > 0).sum()),
).sort_values('总支付金额', ascending=False)

cat_stats['金额占比%'] = (cat_stats['总支付金额'] / cat_stats['总支付金额'].sum() * 100).round(1)
cat_stats['CTR%'] = (cat_stats['总点击'] / cat_stats['总曝光'] * 100).round(2)
cat_stats['CVR%'] = (cat_stats['总订单数'] / cat_stats['总点击'] * 100).round(2)
cat_stats['有转化率%'] = (cat_stats['有转化词数'] / cat_stats['搜索词数'] * 100).round(1)

# Seasonal pivot
seasonal = merged.groupby(['月份', '品类']).agg(总支付金额=('支付金额', 'sum')).reset_index()
pivot_rev = seasonal.pivot_table(values='总支付金额', index='品类', columns='月份', aggfunc='sum', fill_value=0)
pivot_rev = pivot_rev[months_order]

# Top 30 queries all time
top30 = merged.groupby('搜索词').agg(
    总支付金额=('支付金额', 'sum'),
    总订单数=('支付订单数', 'sum'),
    总曝光=('商卡曝光人数', 'sum'),
    总点击=('商品点击人数', 'sum'),
).sort_values('总支付金额', ascending=False).head(30)
top30['CTR%'] = (top30['总点击'] / top30['总曝光'] * 100).round(2)
top30['CVR%'] = (top30['总订单数'] / top30['总点击'] * 100).round(2)
top30['客单价'] = (top30['总支付金额'] / top30['总订单数']).round(2)

# Waste queries
zero_conv = merged.groupby('搜索词').agg(
    总曝光=('商卡曝光人数', 'sum'),
    总点击=('商品点击人数', 'sum'),
).query('总曝光 >= 30')
zero_conv['has_conv'] = merged.groupby('搜索词')['总支付金额'].sum() > 0
waste_queries = zero_conv[~zero_conv['has_conv']].sort_values('总曝光', ascending=False).head(30)

# Recent gems (Apr/May)
recent = merged[merged['月份'].isin(['2026年04月', '2026年05月'])]
gems = recent.groupby('搜索词').agg(
    支付金额=('支付金额', 'sum'),
    订单数=('支付订单数', 'sum'),
    曝光=('商卡曝光人数', 'sum'),
    点击=('商品点击人数', 'sum'),
).reset_index()
gems['CTR%'] = (gems['点击'] / gems['曝光'] * 100).round(2)
gems['CVR%'] = (gems['订单数'] / gems['点击'] * 100).round(2)
gems['客单价'] = (gems['支付金额'] / gems['订单数']).round(2)
gem_filter = gems[(gems['CTR%'] > 10) & (gems['CVR%'] > 3) & (gems['订单数'] >= 2) & (gems['曝光'] > 20) & (gems['曝光'] < 5000)]
gem_filter = gem_filter.sort_values('CVR%', ascending=False)

# Monthly diversity
div_data = []
prev = set()
for m in months_order:
    current = set(all_data[m]['搜索词'].unique())
    conv = set(all_data[m][all_data[m]['支付订单数'] > 0]['搜索词'].unique())
    div_data.append({
        '月份': m,
        '独特搜索词': len(current),
        '有转化词': len(conv),
        '零转化词': len(current - conv),
        '新增词': len(current - prev),
        '消失词': len(prev - current),
        '转化覆盖率%': round(len(conv) / max(len(current), 1) * 100, 1),
        '新增词营收': int(all_data[m][all_data[m]['搜索词'].isin(current - prev)]['支付金额'].sum()),
        '新增词订单': int(all_data[m][all_data[m]['搜索词'].isin(current - prev)]['支付订单数'].sum()),
    })
    prev = current
div_df = pd.DataFrame(div_data)

print("=== DATA READY ===")
print(f"Monthly stats: {monthly.to_json(force_ascii=False)}")
print(f"\nCategory stats: {cat_stats.to_json(force_ascii=False)}")
print(f"\nPivot revenue: {pivot_rev.to_json(force_ascii=False)}")
print(f"\nTop 30: {top30.to_json(force_ascii=False)}")
print(f"\nWaste top 30: {waste_queries.to_json(force_ascii=False)}")
print(f"\nGems ({len(gem_filter)}): {gem_filter.to_json(force_ascii=False)}")
print(f"\nDiversity: {div_df.to_json(force_ascii=False)}")
