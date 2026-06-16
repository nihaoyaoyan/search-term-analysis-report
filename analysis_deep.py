import pandas as pd
import numpy as np
from collections import Counter
import sys
import io
import json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

# ==== NEGATIVE KEYWORD ARCHITECTURE ====
print("=" * 100)
print("NEGATIVE KEYWORD ARCHITECTURE")
print("=" * 100)

# Account-level negatives (broad match killers - queries NEVER relevant)
account_level = []

# 1. "How to cook" / recipe queries (zero intent to purchase)
howto_patterns = ['怎么做好吃', '怎么做', '做法大全', '做法家常', '怎么吃', '咋做', '怎么做才', 
                  '的吃法', '烹饪', '清蒸几分钟', '要蒸多久', '煮多久', '教程', '步骤',
                  '怎么做简单', '怎么做才好吃', '怎么烧', '如何做', '怎么处理', '怎么清洗',
                  '蘸料怎么', '怎么调', '怎么煎', '怎么煮', '怎么炒']

# 2. Pure informational / health queries
info_patterns = ['热量', '卡路里', '营养', '功效', '好处', '成分', '维生素', '蛋白质含量',
                 '能吃吗', '可以吃吗', '不能吃', '有毒', '过敏']

# 3. Entertainment / content consumption
entertainment_patterns = ['吃播', '沉浸式吃', 'asmr', '视频', '直播', '博主', '开箱']

# 4. Non-commercial modifiers
noncom_patterns = ['是什么', '什么意思', '区别', 'vs', '对比', '排名', '测评', '哪种好',
                   '哪个牌子好', '多少钱一斤', '价格表']

# 5. Geographic / location queries (for a delivery area mismatch)
geo_patterns = ['附近', '哪里', '哪家', '哪个市场', '菜市场', '超市']

# 6. Diet/meal plan queries that are pure content
diet_content = ['抗炎饮食', '抗炎食谱', '地中海饮食', '生酮', '断食', '轻断食']

all_negatives = howto_patterns + info_patterns + entertainment_patterns + noncom_patterns + geo_patterns + diet_content

# Test: find queries matching these patterns with zero conversions
may_data = all_data['2026年05月'].copy()
may_data['is_zeroconv'] = may_data['支付订单数'] == 0

neg_matches = []
for _, row in may_data.iterrows():
    query = str(row['搜索词'])
    for pat in all_negatives:
        if pat in query:
            neg_matches.append({
                '查询词': query,
                '匹配模式': pat,
                '曝光': row['商卡曝光人数'],
                '点击': row['商品点击人数'],
                '支付金额': row['支付金额'],
                '是否零转化': row['is_zeroconv'],
            })
            break

neg_df = pd.DataFrame(neg_matches)
neg_summary = neg_df.groupby(['匹配模式', '是否零转化']).agg(
    查询数=('查询词', 'nunique'),
    总曝光=('曝光', 'sum'),
    总支付金额=('支付金额', 'sum'),
).sort_values('总曝光', ascending=False)

print("\nNegative keyword candidates by pattern (May 2026):")
print(neg_summary.to_string())

# Total waste that could be prevented
total_waste_imp = neg_df[neg_df['是否零转化']]['曝光'].sum()
total_waste_rev = neg_df[neg_df['是否零转化']]['支付金额'].sum()
money_saved = neg_df[neg_df['是否零转化']]['点击'].sum() * 0  # just count impressions
print(f"\nEstimated wasted impressions preventable by negatives: {int(total_waste_imp)}")
print(f"Zero-conversion queries matching negative patterns: {len(neg_df[neg_df['是否零转化']])}")

# ==== MONTH-OVER-MONTH QUERY PATTERN DETECTION ====
print("\n" + "=" * 100)
print("MONTH-OVER-MONTH TREND: NEW VS DISAPPEARING QUERIES")
print("=" * 100)

queries_by_month = {}
for month in ["2025年12月","2026年01月","2026年02月","2026年03月","2026年04月","2026年05月"]:
    queries_by_month[month] = set(all_data[month]['搜索词'].unique())

# New queries each month
prev_set = set()
for month in ["2025年12月","2026年01月","2026年02月","2026年03月","2026年04月","2026年05月"]:
    current = queries_by_month[month]
    new_this_month = current - prev_set
    disappeared = prev_set - current
    print(f"\n{month}:")
    print(f"  Total queries: {len(current)}")
    print(f"  New this month: {len(new_this_month)}")
    print(f"  Disappeared from last month: {len(disappeared)}")
    if len(new_this_month) > 0 and month in ["2026年04月","2026年05月"]:
        # Show revenue of new queries
        month_df = all_data[month]
        new_df = month_df[month_df['搜索词'].isin(new_this_month)]
        new_rev = new_df['支付金额'].sum()
        new_orders = new_df['支付订单数'].sum()
        print(f"  Revenue from new queries: {new_rev:.0f} ({new_orders} orders)")
        # Top 5 new queries by revenue
        top_new = new_df.groupby('搜索词').agg(支付金额=('支付金额', 'sum')).sort_values('支付金额', ascending=False).head(5)
        print(f"  Top 5 new queries: {list(top_new.index)}")
    prev_set = current

# ==== QUERY SCULPTING: IDENTIFYING CROSS-CATEGORY OVERLAP ====
print("\n" + "=" * 100)
print("QUERY SCULPTING: CATEGORY OVERLAP ANALYSIS")
print("=" * 100)

categories = {
    '三文鱼': ['三文鱼', '三文', '三文魚'],
    '生蚝': ['生蚝', '乳山生蚝', '蚝'],
    '虾类': ['虾', '甜虾', '北极虾', '黑虎虾', '虾仁', '虾滑', '虾尾', '罗氏虾', '竹节虾', '大虾', '青虾', '基围虾'],
    '减脂餐/健康': ['减脂', '减肥', '轻食', '健身', '代餐', '控卡', '低脂', '低卡', '瘦身', '燃脂', '健康餐', '减重'],
    '鱼类（其他）': ['鲅鱼', '带鱼', '黄花鱼', '鳕鱼', '金枪鱼', '巴沙鱼', '龙利鱼', '多宝鱼', '鲈鱼', '鳜鱼', '马哈鱼', '鱼柳', '鱼排', '鱼片'],
}

# Find queries that match multiple categories (ambiguous)
may_queries = may_data[['搜索词', '支付金额', '支付订单数', '商品点击率', '支付转化率']].drop_duplicates(subset='搜索词')
ambiguous = []
for _, row in may_queries.iterrows():
    query = str(row['搜索词'])
    matched = []
    for cat, kws in categories.items():
        for kw in kws:
            if kw in query:
                matched.append(cat)
                break
    if len(set(matched)) > 1:
        ambiguous.append({
            '搜索词': query,
            '匹配品类': ','.join(set(matched)),
            '支付金额': row['支付金额'],
            '支付订单数': row['支付订单数'],
            'CTR': row['商品点击率'],
            'CVR': row['支付转化率'],
        })

if ambiguous:
    amb_df = pd.DataFrame(ambiguous).sort_values('支付金额', ascending=False)
    print(f"Ambiguous queries matching multiple categories: {len(amb_df)}")
    print(amb_df.to_string())
else:
    print("No ambiguous cross-category queries found.")

# ==== SHOPPING SPECIFIC: BRAND vs NON-BRAND ====
print("\n" + "=" * 100)
print("BRAND-AFFILIATED QUERIES (COMPETITOR / PLATFORM)")
print("=" * 100)

competitor_patterns = ['盒马', '叮咚', '美团', '京东', '天猫', '山姆', 'costco', '每日优鲜', '河马']
brand_queries = may_data[may_data['搜索词'].apply(lambda x: any(p in str(x) for p in competitor_patterns))]
brand_stats = brand_queries.groupby('搜索词').agg(
    支付金额=('支付金额', 'sum'),
    支付订单数=('支付订单数', 'sum'),
    曝光=('商卡曝光人数', 'sum'),
    点击=('商品点击人数', 'sum'),
    点击率=('商品点击率', 'mean'),
    转化率=('支付转化率', 'mean'),
).sort_values('支付金额', ascending=False)

print(f"Brand/competitor affiliated queries in May: {len(brand_stats)}")
print(brand_stats.to_string())
print(f"\nTotal revenue from brand queries: {brand_queries['支付金额'].sum():.0f}")

# ==== HIGH PERFORMANCE QUERIES WITH NEGATIVE TREND ====
print("\n" + "=" * 100)
print("DECLINING HIGH-VALUE QUERIES (WERE CONVERTING BUT FADING)")
print("=" * 100)

# Queries that had conversions in early months but zero in recent months
early = merged[merged['月份'].isin(['2025年12月','2026年01月','2026年02月'])]
late = merged[merged['月份'].isin(['2026年03月','2026年04月','2026年05月'])]

early_conv = set(early[early['支付订单数'] > 0]['搜索词'].unique())
late_conv = set(late[late['支付订单数'] > 0]['搜索词'].unique())

declining = early_conv - late_conv
early_rev = early[early['搜索词'].isin(declining)].groupby('搜索词')['支付金额'].sum().sort_values(ascending=False)

print(f"Queries that converted early but stopped converting: {len(declining)}")
print("Top 20 by historical revenue:")
print(early_rev.head(20).to_string())
print()

# ==== CPA ESTIMATES ====
print("=" * 100)
print("ESTIMATED CPA & ROAS BY CATEGORY (May 2026)")
print("=" * 100)

# Without actual cost data, estimate using industry benchmarks
# Assuming average CPC of $3-5 for food e-commerce in China
# Let's say avg CPC = 4 yuan for estimation purposes
avg_cpc = 4.0

cat_cpa = merged.groupby('品类').agg(
    总点击=('商品点击人数', 'sum'),
    总订单数=('支付订单数', 'sum'),
    总金额=('支付金额', 'sum'),
).sort_values('总金额', ascending=False)

cat_cpa['估算总花费'] = cat_cpa['总点击'] * avg_cpc
cat_cpa['估算CPA'] = (cat_cpa['估算总花费'] / cat_cpa['总订单数']).round(2)
cat_cpa['估算ROAS'] = (cat_cpa['总金额'] / cat_cpa['估算总花费']).round(2)
cat_cpa['点击转化率%'] = (cat_cpa['总订单数'] / cat_cpa['总点击'] * 100).round(2)

print(cat_cpa.to_string())
print()

print("=== DEEP ANALYSIS COMPLETE ===")
