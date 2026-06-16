import pandas as pd
import numpy as np
from collections import Counter
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

# SECTION 1: MONTHLY TRENDS
print("=" * 100)
print("SECTION 1: MONTHLY PERFORMANCE TRENDS")
print("=" * 100)

monthly_stats = merged.groupby('月份').agg(
    总支付金额=('支付金额', 'sum'),
    总订单数=('支付订单数', 'sum'),
    总买家数=('支付买家数', 'sum'),
    总曝光=('商卡曝光人数', 'sum'),
    总点击=('商品点击人数', 'sum'),
    搜索词数=('搜索词', 'nunique'),
).round(2)

monthly_stats['整体CTR'] = (monthly_stats['总点击'] / monthly_stats['总曝光']).round(4)
monthly_stats['整体CVR'] = (monthly_stats['总订单数'] / monthly_stats['总点击']).round(4)
monthly_stats['客单价'] = (monthly_stats['总支付金额'] / monthly_stats['总订单数']).round(2)

print(monthly_stats.to_string())
print()

# SECTION 2: CATEGORIES
print("=" * 100)
print("SECTION 2: PRODUCT CATEGORY ANALYSIS")
print("=" * 100)

categories = {
    '减脂餐/健康': ['减脂', '减肥', '轻食', '健身', '代餐', '控卡', '低脂', '低卡', '瘦身', '燃脂', '健康餐', '减重'],
    '三文鱼': ['三文鱼', '三文', '三文魚'],
    '虾类': ['虾', '甜虾', '北极虾', '黑虎虾', '虾仁', '虾滑', '虾尾', '罗氏虾', '竹节虾', '大虾', '青虾', '基围虾'],
    '生蚝': ['生蚝', '乳山生蚝', '蚝'],
    '鱼类（其他）': ['鲅鱼', '带鱼', '黄花鱼', '鳕鱼', '金枪鱼', '巴沙鱼', '龙利鱼', '多宝鱼', '鲈鱼', '鳜鱼', '马哈鱼', '鱼柳', '鱼排', '鱼片'],
    '贝类（其他）': ['扇贝', '鲍鱼', '蛤蜊', '海螺', '青口', '花甲', '蛏子', '花蛤', '象拔蚌'],
    '蟹类': ['蟹', '帝王蟹', '面包蟹', '梭子蟹', '大闸蟹', '雪蟹', '螃蟹'],
    '牛排/肉类': ['牛排', '牛肉', '和牛', '羊肉', '羊排', '猪肉', '鸡肉', '鸡胸', '牛腩', '肥牛'],
    '水果': ['榴莲', '车厘子', '草莓', '蓝莓', '芒果', '椰子', '橙子', '苹果', '牛油果', '葡萄'],
    '火锅/预制菜': ['火锅', '烧烤', '香肠', '烤肠', '培根', '丸子', '牛丸', '预制菜', '半成品', '速食'],
}

def classify_query(query):
    q = str(query)
    for cat, keywords in categories.items():
        for kw in keywords:
            if kw in q:
                return cat
    return '其他/长尾'

merged['品类'] = merged['搜索词'].apply(classify_query)

cat_stats = merged.groupby('品类').agg(
    总支付金额=('支付金额', 'sum'),
    总订单数=('支付订单数', 'sum'),
    总曝光=('商卡曝光人数', 'sum'),
    总点击=('商品点击人数', 'sum'),
    搜索词数=('搜索词', 'nunique'),
    有转化词数=('支付金额', lambda x: (x > 0).sum()),
).sort_values('总支付金额', ascending=False)

cat_stats['金额占比%'] = (cat_stats['总支付金额'] / cat_stats['总支付金额'].sum() * 100).round(1)
cat_stats['CTR%'] = (cat_stats['总点击'] / cat_stats['总曝光'] * 100).round(2)
cat_stats['CVR%'] = (cat_stats['总订单数'] / cat_stats['总点击'] * 100).round(2)
cat_stats['客单价'] = (cat_stats['总支付金额'] / cat_stats['总订单数']).round(2)
cat_stats['有转化率%'] = (cat_stats['有转化词数'] / cat_stats['搜索词数'] * 100).round(1)

print(cat_stats.to_string())
print()

# SECTION 3: TOP CONVERTERS
print("=" * 100)
print("SECTION 3: TOP 25 CONVERTING SEARCH TERMS (BY REVENUE)")
print("=" * 100)

top_revenue = merged.groupby('搜索词').agg(
    总支付金额=('支付金额', 'sum'),
    总订单数=('支付订单数', 'sum'),
    总曝光=('商卡曝光人数', 'sum'),
    总点击=('商品点击人数', 'sum'),
    出现月数=('月份', 'nunique'),
).sort_values('总支付金额', ascending=False).head(25)

top_revenue['客单价'] = (top_revenue['总支付金额'] / top_revenue['总订单数']).round(2)
top_revenue['CTR%'] = (top_revenue['总点击'] / top_revenue['总曝光'] * 100).round(2)
top_revenue['CVR%'] = (top_revenue['总订单数'] / top_revenue['总点击'] * 100).round(2)
print(top_revenue.to_string())
print()

# SECTION 4: WASTE ANALYSIS
print("=" * 100)
print("SECTION 4: WASTE ANALYSIS - ZERO CONVERSION QUERIES WITH HIGH EXPOSURE")
print("=" * 100)

zero_conv = merged.groupby('搜索词').agg(
    总曝光=('商卡曝光人数', 'sum'),
    总点击=('商品点击人数', 'sum'),
    总支付金额=('支付金额', 'sum'),
    总订单数=('支付订单数', 'sum'),
    出现月数=('月份', 'nunique'),
).query('总订单数 == 0 and 总曝光 >= 30').sort_values('总曝光', ascending=False)

print(f"Zero-conversion queries with >=30 impressions: {len(zero_conv)}")
print(zero_conv.head(35).to_string())
print()

# Low CVR queries
low_cvr = merged.groupby('搜索词').agg(
    总曝光=('商卡曝光人数', 'sum'),
    总点击=('商品点击人数', 'sum'),
    总订单数=('支付订单数', 'sum'),
).query('总订单数 > 0 and 总曝光 >= 500')
low_cvr['CVR%'] = (low_cvr['总订单数'] / low_cvr['总点击'] * 100).round(3)
low_cvr_waste = low_cvr[low_cvr['CVR%'] < 1.0].sort_values('总曝光', ascending=False)

print(f"\nLow CVR (<1%) queries with >=500 impressions: {len(low_cvr_waste)}")
print(low_cvr_waste.head(20).to_string())
print()

# SECTION 5: INTENT CLASSIFICATION
print("=" * 100)
print("SECTION 5: QUERY INTENT CLASSIFICATION")
print("=" * 100)

informational_patterns = ['怎么', '如何', '做法', '吃法', '好吃', '教程', '视频', '区别', '作用',
                          '营养', '热量', '卡路里', '保质期', '保存', '什么', '那种',
                          '食谱', '菜单', '功效', '好处', '方法', '步骤']
competitor_patterns = ['盒马', '叮咚', '美团', '京东', '天猫', '山姆', 'costco', '每日优鲜', '河马']
navigational_patterns = ['app', '官网', '旗舰店', '官方', '公众号', '小程序']
transactional_patterns = ['买', '价格', '多少钱', '便宜', '优惠', '包邮', '团购', '批发', '配送',
                          '外卖', '订购', '下单', '热销', '推荐', '排名', '进口', '野生', '现货', '即食', '顺丰']

def classify_intent(query):
    query_str = str(query)
    for p in informational_patterns:
        if p in query_str:
            return '信息型(Informational)'
    for p in competitor_patterns:
        if p in query_str:
            return '竞品导航(Competitor)'
    for p in navigational_patterns:
        if p in query_str:
            return '品牌导航(Navigational)'
    for p in transactional_patterns:
        if p in query_str:
            return '交易型(Transactional)'
    return '商业型(Commercial)'

merged['意图分类'] = merged['搜索词'].apply(classify_intent)

intent_stats = merged.groupby('意图分类').agg(
    搜索词数=('搜索词', 'nunique'),
    总支付金额=('支付金额', 'sum'),
    总订单数=('支付订单数', 'sum'),
    总曝光=('商卡曝光人数', 'sum'),
    总点击=('商品点击人数', 'sum'),
).sort_values('总支付金额', ascending=False)

intent_stats['金额占比%'] = (intent_stats['总支付金额'] / intent_stats['总支付金额'].sum() * 100).round(1)
intent_stats['CTR%'] = (intent_stats['总点击'] / intent_stats['总曝光'] * 100).round(2)
intent_stats['CVR%'] = (intent_stats['总订单数'] / intent_stats['总点击'] * 100).round(2)
print(intent_stats.to_string())
print()

# SECTION 6: N-GRAM ANALYSIS
print("=" * 100)
print("SECTION 6: N-GRAM ANALYSIS - MODIFIERS IN ZERO-CONVERSION QUERIES (May 2026)")
print("=" * 100)

may_data = all_data['2026年05月']
may_zero = may_data[may_data['支付订单数'] == 0]
may_conv = may_data[may_data['支付订单数'] > 0]

def extract_ngrams(text, n=2):
    chars = list(str(text))
    return [''.join(chars[i:i+n]) for i in range(len(chars)-n+1)]

zero_ngrams = Counter()
for _, row in may_zero.iterrows():
    ngrams = extract_ngrams(row['搜索词'], 2)
    for ng in ngrams:
        zero_ngrams[ng] += row['商卡曝光人数']

conv_ngrams = Counter()
for _, row in may_conv.iterrows():
    ngrams = extract_ngrams(row['搜索词'], 2)
    for ng in ngrams:
        conv_ngrams[ng] += row['商卡曝光人数']

zero_total_imp = may_zero['商卡曝光人数'].sum()
conv_total_imp = may_conv['商卡曝光人数'].sum()

suspect_bigrams = []
for ng, zero_count in zero_ngrams.most_common(200):
    if len(ng.strip()) < 2:
        continue
    conv_count = conv_ngrams.get(ng, 0)
    zero_ratio = zero_count / max(zero_total_imp, 1)
    conv_ratio = conv_count / max(conv_total_imp, 1)
    if zero_ratio > conv_ratio * 3 and zero_count > 100:
        suspect_bigrams.append((ng, int(zero_count), round(zero_ratio,4), round(conv_ratio,4)))

print("Bigrams over-represented in zero-conversion queries (potential negative keyword fragments):")
for ng, cnt, zr, cr in suspect_bigrams[:30]:
    print(f"  '{ng}' | zero_imp: {cnt} | zero_ratio: {zr} | conv_ratio: {cr}")
print()

# SECTION 7: OPPORTUNITY MINING
print("=" * 100)
print("SECTION 7: OPPORTUNITY MINING - HIGH-POTENTIAL LONG TAIL (Apr-May 2026)")
print("=" * 100)

recent = merged[merged['月份'].isin(['2026年04月', '2026年05月'])]
opportunities = recent.groupby('搜索词').agg(
    总支付金额=('支付金额', 'sum'),
    总订单数=('支付订单数', 'sum'),
    总曝光=('商卡曝光人数', 'sum'),
    总点击=('商品点击人数', 'sum'),
).reset_index()

opportunities['CTR%'] = (opportunities['总点击'] / opportunities['总曝光'] * 100).round(2)
opportunities['CVR%'] = (opportunities['总订单数'] / opportunities['总点击'] * 100).round(2)
opportunities['客单价'] = (opportunities['总支付金额'] / opportunities['总订单数']).round(2)

gems = opportunities[
    (opportunities['CTR%'] > 10) &
    (opportunities['CVR%'] > 3) &
    (opportunities['总订单数'] >= 2) &
    (opportunities['总曝光'] < 5000) &
    (opportunities['总曝光'] > 20)
].sort_values('CVR%', ascending=False)

print(f"High-potential long-tail keywords: {len(gems)}")
print(gems.head(35).to_string())
print()

# SECTION 8: SEASONAL TRENDS
print("=" * 100)
print("SECTION 8: CATEGORY SEASONAL REVENUE TRENDS")
print("=" * 100)

seasonal = merged.groupby(['月份', '品类']).agg(总支付金额=('支付金额', 'sum')).reset_index()
pivot_rev = seasonal.pivot_table(values='总支付金额', index='品类', columns='月份', aggfunc='sum', fill_value=0)
pivot_rev = pivot_rev[months_order]
print(pivot_rev.round(0).to_string())
print()

# SECTION 9: LOW CTR DIAGNOSIS
print("=" * 100)
print("SECTION 9: HIGH IMPRESSION / LOW CTR QUERIES (May 2026)")
print("=" * 100)

may_stats = may_data.groupby('搜索词').agg(
    曝光=('商卡曝光人数', 'sum'),
    点击=('商品点击人数', 'sum'),
    订单数=('支付订单数', 'sum'),
    支付金额=('支付金额', 'sum'),
).query('曝光 >= 200')

may_stats['CTR%'] = (may_stats['点击'] / may_stats['曝光'] * 100).round(2)
low_ctr = may_stats[may_stats['CTR%'] < 5].sort_values('曝光', ascending=False)
print(f"Queries with >=200 impressions and CTR <5%: {len(low_ctr)}")
print(low_ctr.head(25).to_string())
print()

# SECTION 10: QUERY DIVERSITY GROWTH
print("=" * 100)
print("SECTION 10: QUERY DIVERSITY & COVERAGE METRICS")
print("=" * 100)

diversity = merged.groupby('月份').agg(
    独特搜索词数=('搜索词', 'nunique'),
    有转化词数=('支付订单数', lambda x: (x > 0).sum()),
    零转化词数=('支付订单数', lambda x: (x == 0).sum()),
).round(0)

diversity['转化覆盖率%'] = (diversity['有转化词数'] / diversity['独特搜索词数'] * 100).round(1)
diversity['零转化占比%'] = (diversity['零转化词数'] / diversity['独特搜索词数'] * 100).round(1)
print(diversity.to_string())
print()

print("=== ANALYSIS COMPLETE ===")
