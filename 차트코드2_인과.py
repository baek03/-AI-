# 인과 분석 그림 2개 (PNG, 200dpi). 분석코드2_인과.py 먼저 실행 (표/14~19 사용)
import pathlib
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

D = pathlib.Path(__file__).parent
OUT = D / '차트'
plt.rcParams.update({'font.family': 'Malgun Gothic', 'axes.unicode_minus': False, 'font.size': 11,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#999'})
DAY, NIGHT, GRAY, INK = '#2a78d6', '#eb6834', '#b5b5b5', '#333'
tab = lambda n: pd.read_csv(D / '표' / n, encoding='utf-8-sig').set_index('변수')

# 그림 5. 사고 경로도: 두 갈래 인과 경로와 조정 오즈비
car, alone, death = tab('15_로지스틱_승용충돌.csv'), tab('18_로지스틱_단독.csv'), tab('16_로지스틱_사망.csv')
fig, ax = plt.subplots(figsize=(8.5, 3.6))
ax.set_xlim(0, 10); ax.set_ylim(0, 4.4); ax.axis('off')


def box(x, y, text, color):
    ax.add_patch(FancyBboxPatch((x - 0.9, y - 0.38), 1.8, 0.76, boxstyle='round,pad=0.05', fc=color, ec='none'))
    ax.text(x, y, text, ha='center', va='center', color='white', fontsize=11.5, weight='bold')


def arrow(x1, x2, y, r):
    ax.annotate('', xy=(x2 - 0.97, y), xytext=(x1 + 0.97, y), arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.8))
    pv = 'p<0.001' if r['p'] < 0.001 else f"p={r['p']:.3f}"
    ax.text((x1 + x2) / 2, y + 0.45, f"OR {r['OR']:.1f}", ha='center', fontsize=11, weight='bold', color=INK)
    ax.text((x1 + x2) / 2, y + 0.17, f"95% CI {r['CI_하한']:.1f}~{r['CI_상한']:.1f}, {pv}", ha='center', fontsize=8, color='#666')


ax.text(0.05, 4.15, '① 야간 경로', fontsize=11, weight='bold', color=NIGHT)
box(1.2, 3.4, '야간 운행', NIGHT); box(5.0, 3.4, '승용차와 충돌', NIGHT)
arrow(1.2, 5.0, 3.4, car.loc['야간'])
ax.text(6.25, 3.4, '도로형태·연령·농번기·지역 통제 후', va='center', fontsize=9, color='#666')
ax.text(0.05, 2.0, '② 고령 경로', fontsize=11, weight='bold', color=DAY)
box(1.2, 1.2, '65세 이상 운전', DAY); box(5.0, 1.2, '단독 전도·추락', DAY); box(8.8, 1.2, '사망', INK)
arrow(1.2, 5.0, 1.2, alone.loc['고령']); arrow(5.0, 8.8, 1.2, death.loc['단독'])
fig.tight_layout(); fig.savefig(OUT / '그림5_사고경로도.png', dpi=200); plt.close(fig)

# 그림 6. 조정 오즈비 포레스트 플롯 (승용차 충돌, 사망)
rows = [('승용차와 충돌', car, ['야간', '교차로', '고령', '농번기']), ('사망 사고', death, ['단독', '야간', '고령', '교차로', '농번기'])]
label = {'야간': '야간', '교차로': '교차로', '고령': '65세 이상', '농번기': '농번기', '단독': '단독사고'}
fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), sharey=False)
for ax, (title, t, vs) in zip(axes, rows):
    t = t.loc[vs][::-1]
    sig = t['p'] < 0.05
    ax.hlines(range(len(t)), t['CI_하한'], t['CI_상한'], color=[NIGHT if s else GRAY for s in sig], lw=2.5)
    ax.scatter(t['OR'], range(len(t)), color=[NIGHT if s else GRAY for s in sig], zorder=3, s=40)
    ax.axvline(1, color=INK, lw=1, ls='--')
    ax.set_xscale('log'); ticks = [x for x in [0.1, 0.3, 1, 3, 10, 30, 100] if t['CI_하한'].min() / 1.5 <= x <= t['CI_상한'].max() * 1.5]
    ax.set_xticks(ticks); ax.set_xticklabels([f'{x:g}' for x in ticks]); ax.minorticks_off(); ax.set_yticks(range(len(t))); ax.set_yticklabels([label[v] for v in t.index])
    for i, (o, p) in enumerate(zip(t['OR'], t['p'])):
        ax.text(t['CI_상한'].iloc[i] * 1.15, i, f'{o:.1f}' + (' *' if p < 0.05 else ''), va='center', fontsize=9.5)
    ax.set_title(title, fontsize=11.5, weight='bold'); ax.set_xlabel('조정 오즈비 (로그 척도, 1 = 영향 없음)', fontsize=9)
    ax.grid(axis='x', color='#e6e6e6')
fig.tight_layout(); fig.savefig(OUT / '그림6_조정오즈비.png', dpi=200); plt.close(fig)
print('ok')
