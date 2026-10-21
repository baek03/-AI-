# 보고서용 차트 5개 (PNG, 200dpi). 입력: 입력/*.csv, 표/*.csv (분석코드_analyze.py 먼저 실행)
import pathlib
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

D = pathlib.Path(__file__).parent
OUT = D / '차트'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family': 'Malgun Gothic', 'axes.unicode_minus': False, 'font.size': 11,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#999',
                     'axes.grid': True, 'grid.color': '#e6e6e6', 'axes.axisbelow': True})
DAY, NIGHT, GRAY, INK = '#2a78d6', '#eb6834', '#b5b5b5', '#333'
SIX = ['부안군', '군산시', '익산시', '김제시', '고창군', '순창군']

acc = pd.read_csv(D / '입력/사고_농기계_6개시군_2021-2025.csv', encoding='utf-8-sig')
tab = lambda n: pd.read_csv(D / '표' / n, encoding='utf-8-sig')


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=200)
    plt.close(fig)


# 1. 주야별 사고 상대: 승용차 / 기타 차·보행자 / 단독 (100% 가로 막대)
def kind(r):
    if r == '해당없음(단독사고)':
        return '농기계 단독'
    return '승용차와 충돌' if r == '승용' else '기타 차량·보행자'
acc['상대'] = acc['피해운전자_차종'].map(kind)
order = ['승용차와 충돌', '기타 차량·보행자', '농기계 단독']
colors = [NIGHT, '#f3b08f', GRAY]
ct = pd.crosstab(acc['주야'], acc['상대']).reindex(['주간', '야간'])[order]
pct = ct.div(ct.sum(axis=1), axis=0) * 100
fig, ax = plt.subplots(figsize=(8, 2.8))
left = [0, 0]
for k, c in zip(order, colors):
    ax.barh(pct.index, pct[k], left=left, color=c, edgecolor='white', linewidth=2, label=k, height=0.6)
    for i, (v, n) in enumerate(zip(pct[k], ct[k])):
        if v >= 8:
            ax.text(left[i] + v / 2, i, f'{n}건\n{v:.0f}%', ha='center', va='center', fontsize=10, color=INK)
    left = [a + b for a, b in zip(left, pct[k])]
ax.set_yticks([0, 1], [f'주간 (n={ct.loc["주간"].sum()})', f'야간 (n={ct.loc["야간"].sum()})'])
ax.set_xlim(0, 100)
ax.set_xlabel('사고 비율 (%)')
ax.grid(axis='y', visible=False)
ax.legend(ncol=3, loc='upper center', bbox_to_anchor=(0.5, 1.28), frameon=False)
ax.set_title('야간 사고는 승용차와의 충돌이 64% (주간 22%, p=0.012)', loc='left', pad=34, fontsize=12)
save(fig, '그림1_주야별_사고상대.png')

# 2. 주야별 심각도: 중상 이상 사고 비율 + 사망자
sev = tab('1_주야별_심각도.csv')
sev = sev[sev['지역'] == '6개시군'].set_index('주야').loc[['주간', '야간']]
fig, ax = plt.subplots(figsize=(5.5, 3.4))
bars = ax.bar(sev.index, sev['중상이상사고비율(%)'], color=[DAY, NIGHT], width=0.5)
for b, (_, r) in zip(bars, sev.iterrows()):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 2,
            f"{r['중상이상사고비율(%)']:.0f}%\n(사망 {r['사망']}명, 중상 {r['중상']}명)", ha='center', fontsize=10, color=INK)
ax.set_ylim(0, 100)
ax.set_ylabel('중상 이상 사고 비율 (%)')
ax.grid(axis='x', visible=False)
ax.set_title('치명도는 주간이 높음 (단독 전도·추락)', loc='left', fontsize=12)
save(fig, '그림2_주야별_심각도.png')

# 3. 시군별 야간 사고 건수 + 야간비율 95% 신뢰구간
sg = tab('2_시군별_야간비율.csv').set_index('구분')
rows = SIX + ['6개시군 합계', '전북 나머지 8개 시군']
sg = sg.loc[rows]
fig, ax = plt.subplots(figsize=(8, 3.8))
y = range(len(rows))[::-1]
for yi, (name, r) in zip(y, sg.iterrows()):
    c = INK if '시군' in name and name not in SIX else NIGHT
    ax.plot([r['95%CI_하한'], r['95%CI_상한']], [yi, yi], color=c, lw=2, alpha=0.35)
    ax.plot(r['야간비율(%)'], yi, 'o', color=c, ms=8)
    ax.text(r['95%CI_상한'] + 1.5, yi, f"{r['야간비율(%)']:.0f}%  (야간 {int(r['야간사고'])}/{int(r['사고'])}건)", va='center', fontsize=10, color=INK)
ax.set_yticks(list(y), rows)
ax.set_xlim(-2, 90)
ax.set_xlabel('야간 사고 비율 (%) · 선 = 95% 신뢰구간')
ax.grid(axis='y', visible=False)
ax.set_title('시군별 야간 사고 비율 (2021-2025)', loc='left', fontsize=12)
save(fig, '그림3_시군별_야간비율.png')

# 4. 월별 주야 사고 (쌓은 막대)
m = tab('4_월별.csv')
fig, ax = plt.subplots(figsize=(8, 3.4))
ax.bar(m['월'], m['주간'], color=DAY, label='주간', width=0.7)
ax.bar(m['월'], m['야간'], bottom=m['주간'], color=NIGHT, label='야간', width=0.7, edgecolor='white', linewidth=2)
for x, d, n in zip(m['월'], m['주간'], m['야간']):
    if n:
        ax.text(x, d + n + 0.2, f'야간 {n}', ha='center', fontsize=9, color=INK)
ax.axvspan(8.5, 11.5, color='#f6f6f6', zorder=0)
ax.text(10, 11.4, '수확기', ha='center', fontsize=10, color='#666')
ax.axvspan(3.5, 6.5, color='#f6f6f6', zorder=0)
ax.text(5, 11.4, '모내기', ha='center', fontsize=10, color='#666')
ax.set_xticks(range(1, 13), [f'{i}월' for i in range(1, 13)])
ax.set_ylim(0, 12)
ax.set_ylabel('사고 건수')
ax.grid(axis='x', visible=False)
ax.legend(frameon=False, loc='upper left')
ax.set_title('월별 농기계 사고 (6개 시군 합계) · 10-11월 사고 7건 중 4건 야간', loc='left', fontsize=12)
save(fig, '그림4_월별_주야.png')

# 5. 야간 사고 법규위반 (중앙선침범 집중)
lv = tab('8_법규위반별.csv').set_index('법규위반')
keys = ['안전운전불이행', '중앙선침범', '기타']
fig, ax = plt.subplots(figsize=(6.5, 3.2))
x = range(len(keys))
w = 0.38
dn = acc['주야'].value_counts()
ax.bar([i - w / 2 for i in x], [100 * lv.loc[k, '주간'] / dn['주간'] for k in keys], w, color=DAY, label=f'주간 (n={dn["주간"]})')
ax.bar([i + w / 2 for i in x], [100 * lv.loc[k, '야간'] / dn['야간'] for k in keys], w, color=NIGHT, label=f'야간 (n={dn["야간"]})')
for i, k in zip(x, keys):
    for off, col, n in [(-w / 2, '주간', dn['주간']), (w / 2, '야간', dn['야간'])]:
        v = lv.loc[k, col]
        ax.text(i + off, 100 * v / n + 2, f'{v}건', ha='center', fontsize=9, color=INK)
ax.set_xticks(list(x), keys)
ax.set_ylim(0, 100)
ax.set_ylabel('주야별 사고 중 비율 (%)')
ax.grid(axis='x', visible=False)
ax.legend(frameon=False)
ax.set_title('중앙선침범 5건 중 3건이 야간 (p=0.039)', loc='left', fontsize=12)
save(fig, '그림5_법규위반_주야.png')
print('saved', sorted(p.name for p in OUT.iterdir()))
