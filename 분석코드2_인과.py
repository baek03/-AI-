# 혼동 요인 통제 분석 (전북 전체 124건, 2021-2025)
# 1) 야간 -> 다른 차·사람과 충돌: 층화(Mantel-Haenszel) + 로지스틱 회귀
# 2) 사망 사고를 부르는 요인: 로지스틱 회귀 (단독사고, 고령, 야간, 도로형태, 농번기)
# 3) 일몰 시각(월별, 전주 기준 계산) vs 월별 야간 사고 비율: 용량-반응
# 출력: 표/14~17_*.csv, 요약2.txt
import math, pathlib
import numpy as np
import pandas as pd
from statsmodels.discrete.discrete_model import Logit  # statsmodels.api는 scipy.signal DLL이 PC 보안정책에 막혀 직접 import
from statsmodels.stats.contingency_tables import StratifiedTable
from scipy import stats

D = pathlib.Path(__file__).parent
d = pd.read_csv(D / '입력/사고_농기계_전북전체_2021-2025.csv', encoding='utf-8-sig')
SIX = ['익산시', '김제시', '군산시', '고창군', '부안군', '순창군']

d['야간'] = (d['주야'] == '야간').astype(int)
d['충돌'] = (d['피해운전자_차종'] != '해당없음(단독사고)').astype(int)  # 다른 차·사람과의 사고
d['승용충돌'] = (d['피해운전자_차종'] == '승용').astype(int)
d['단독'] = 1 - d['충돌']
d['사망'] = (d['사고내용'] == '사망사고').astype(int)
d['고령'] = (d['가해운전자_연령대'] == '65세 이상').astype(int)
d['교차로'] = (d['도로형태_대'] == '교차로').astype(int)
d['농번기'] = (d['농번기'] != '기타').astype(int)
d['6개시군'] = d['시군'].isin(SIX).astype(int)
lines = []


def logit(y, xs, name):
    X = d[xs].astype(float).assign(const=1.0)
    m = Logit(d[y], X).fit(disp=0)
    ci = m.conf_int()
    t = pd.DataFrame({'변수': xs, 'OR': np.exp(m.params[xs]).round(2),
                      'CI_하한': np.exp(ci.loc[xs, 0]).round(2), 'CI_상한': np.exp(ci.loc[xs, 1]).round(2),
                      'p': m.pvalues[xs].round(3)})
    t.to_csv(D / '표' / name, index=False, encoding='utf-8-sig')
    lines.append(f'[{name}] y={y}, n={len(d)}, pseudoR2={m.prsquared:.3f}')
    lines.append(t.to_string(index=False))
    return t


# 1. 야간 -> 충돌 (혼동 요인 통제)
logit('충돌', ['야간', '고령', '교차로', '농번기', '6개시군'], '14_로지스틱_충돌.csv')
logit('승용충돌', ['야간', '고령', '교차로', '농번기', '6개시군'], '15_로지스틱_승용충돌.csv')

# 층화: 도로형태(교차로/그 외), 고령 여부별 2x2 -> MH 공통 OR
for s in ['교차로', '고령', '농번기']:
    tabs = []
    for v in [0, 1]:
        g = d[d[s] == v]
        tabs.append(np.array([[((g.야간 == 1) & (g.충돌 == 1)).sum(), ((g.야간 == 1) & (g.충돌 == 0)).sum()],
                              [((g.야간 == 0) & (g.충돌 == 1)).sum(), ((g.야간 == 0) & (g.충돌 == 0)).sum()]]) + 0.5)
    st = StratifiedTable(tabs)
    lines.append(f'MH 층화({s}): 공통OR={st.oddsratio_pooled:.2f}, p={st.test_null_odds().pvalue:.3f}, '
                 f'층별OR={[round(t[0,0]*t[1,1]/(t[0,1]*t[1,0]),2) for t in tabs]}, 동질성p={st.test_equal_odds().pvalue:.3f}')

# 2. 사망 사고 요인
logit('사망', ['단독', '고령', '야간', '교차로', '농번기'], '16_로지스틱_사망.csv')
ct = pd.crosstab([d['단독'], d['고령']], d['사망'])
ct['사망률(%)'] = (100 * ct[1] / ct.sum(axis=1)).round(1)
lines.append('단독 x 고령 사망률\n' + ct.to_string())


# 3. 월별 일몰 시각 (전주 35.82N, 127.15E, KST) vs 야간 비율
def sunset(month, lat=35.82, lon=127.15):
    n = int(pd.Timestamp(2023, month, 15).dayofyear)
    g = 2 * math.pi / 365 * (n - 1)
    eq = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    dec = 0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
    ha = math.degrees(math.acos(math.cos(math.radians(90.833)) / (math.cos(math.radians(lat)) * math.cos(dec)) - math.tan(math.radians(lat)) * math.tan(dec)))
    return (720 - 4 * (lon - ha) - eq + 540) / 60  # 시(KST)


m = d.groupby('월').agg(사고=('야간', 'size'), 야간=('야간', 'sum')).reindex(range(1, 13), fill_value=0)
m['일몰'] = [round(sunset(i), 2) for i in m.index]
m['야간비율(%)'] = (100 * m['야간'] / m['사고'].replace(0, np.nan)).round(1)
m.to_csv(D / '표' / '17_월별_일몰_야간비율.csv', encoding='utf-8-sig')
mm = m[m['사고'] > 0]
r, p = stats.spearmanr(mm['일몰'], mm['야간비율(%)'])
# 이른 일몰(18시 이전) vs 늦은 일몰
early = mm[mm['일몰'] < 18.5]
late = mm[mm['일몰'] >= 18.5]
lines.append(m.to_string())
lines.append(f'일몰-야간비율 Spearman r={r:.2f}, p={p:.3f}')
lines.append(f'일몰 18:30 이전 달: 야간 {early.야간.sum()}/{early.사고.sum()}, 이후 달: {late.야간.sum()}/{late.사고.sum()}, '
             f'Fisher p={stats.fisher_exact([[early.야간.sum(), early.사고.sum()-early.야간.sum()],[late.야간.sum(), late.사고.sum()-late.야간.sum()]])[1]:.3f}')

(D / '요약2.txt').write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines))

# 4. 고령 -> 단독사고 -> 사망 경로 (매개)
lines.append('--- 고령 경로 ---')
logit('단독', ['고령', '야간', '교차로', '농번기'], '18_로지스틱_단독.csv')
logit('사망', ['고령'], '19_로지스틱_사망_고령단순.csv')
for g, name in [(1, '65세 이상'), (0, '65세 미만')]:
    s = d[d['고령'] == g]
    lines.append(f'{name}: 사고 {len(s)}, 단독 {s.단독.sum()} ({100*s.단독.mean():.1f}%), 사망사고 {s.사망.sum()} ({100*s.사망.mean():.1f}%)')
lines.append('단독사고 유형x사망\n' + pd.crosstab(d[d.단독 == 1]['사고유형'], d[d.단독 == 1]['사망'], margins=True).to_string())
lines.append('승용충돌 사고유형x주야\n' + pd.crosstab(d[d.승용충돌 == 1]['사고유형'], d[d.승용충돌 == 1]['주야']).to_string())
lines.append('도로형태_대 x 충돌\n' + pd.crosstab(d['도로형태_대'], d['충돌'], margins=True).to_string())
(D / '요약2.txt').write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines[lines.index('--- 고령 경로 ---'):]))
