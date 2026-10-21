# 6개 시군(익산·김제·군산·고창·부안·순창) 농기계 사고 주야 분석, 2021-2025
# 입력: 입력/*.csv (정리데이터 복사본), 출력: 표/*.csv, 요약.txt
import csv, collections, pathlib, math

D = pathlib.Path(__file__).parent
SIX = ['익산시', '김제시', '군산시', '고창군', '부안군', '순창군']


def load(name):
    with open(D / '입력' / name, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


six = load('사고_농기계_6개시군_2021-2025.csv')
jb = load('사고_농기계_전북전체_2021-2025.csv')
mach = load('농업기계보유현황_전북_2021-2025.csv')
(D / '표').mkdir(exist_ok=True)


def num(x):
    return int(float(x or 0))


def stats(rows):
    n = len(rows)
    return dict(
        사고=n,
        사망=sum(num(r['사망자수']) for r in rows),
        중상=sum(num(r['중상자수']) for r in rows),
        경상=sum(num(r['경상자수']) for r in rows),
        사상자=sum(num(r['사상자수']) for r in rows),
        사상자_per_사고=round(sum(num(r['사상자수']) for r in rows) / n, 2) if n else 0,
        중상이상사고비율=round(100 * sum(r['사고내용'] in ('사망사고', '중상사고') for r in rows) / n, 1) if n else 0,
    )


def write(name, header, rows):
    with open(D / '표' / name, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def crosstab(rows, col, name, order=None):
    c = collections.Counter((r[col], r['주야']) for r in rows)
    keys = order or sorted({r[col] for r in rows}, key=lambda k: -(c[(k, '주간')] + c[(k, '야간')]))
    out = []
    for k in keys:
        d, n = c[(k, '주간')], c[(k, '야간')]
        out.append([k, d, n, d + n, round(100 * n / (d + n), 1) if d + n else 0])
    write(name, [col, '주간', '야간', '합계', '야간비율(%)'], out)
    return out


def wilson(k, n, z=1.96):
    # 95% 신뢰구간 (표본이 작아 비율 해석 시 함께 제시)
    if n == 0:
        return (0, 0)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(100 * (mid - half), 1), round(100 * (mid + half), 1))


# 1. 주야별 심각도: 6개 시군 vs 전북 전체
out = []
for label, rows in [('6개시군', six), ('전북전체', jb)]:
    for dn in ['주간', '야간']:
        s = stats([r for r in rows if r['주야'] == dn])
        out.append([label, dn] + list(s.values()))
write('1_주야별_심각도.csv', ['지역', '주야', '사고', '사망', '중상', '경상', '사상자', '사고당사상자', '중상이상사고비율(%)'], out)

# 2. 야간비율 + 95% 신뢰구간: 6개 시군 각각, 6개 시군 합, 전북 나머지, 전북 전체
out = []
groups = [(s, [r for r in six if r['시군'] == s]) for s in SIX]
groups += [('6개시군 합계', six), ('전북 나머지 8개 시군', [r for r in jb if r['시군'] not in SIX]), ('전북 전체', jb)]
for name, rows in groups:
    n = len(rows)
    k = sum(r['주야'] == '야간' for r in rows)
    lo, hi = wilson(k, n)
    out.append([name, n, k, round(100 * k / n, 1) if n else 0, lo, hi])
write('2_시군별_야간비율.csv', ['구분', '사고', '야간사고', '야간비율(%)', '95%CI_하한', '95%CI_상한'], out)

# 3~9. 6개 시군 교차표
crosstab(six, '연도', '3_연도별.csv', order=[str(y) for y in range(2021, 2026)])
crosstab(six, '월', '4_월별.csv', order=[str(m) for m in range(1, 13)])
crosstab(six, '농번기', '5_농번기별.csv', order=['모내기(4-6월)', '수확기(9-11월)', '기타'])
crosstab(six, '사고유형', '6_사고유형별.csv')
crosstab(six, '도로형태', '7_도로형태별.csv')
crosstab(six, '법규위반', '8_법규위반별.csv')
crosstab(six, '가해운전자_연령대', '9_가해운전자연령대별.csv')
crosstab(six, '피해운전자_차종', '10_피해운전자차종별.csv')

# 11. 야간 사고 11건 목록
cols = ['구분번호', '발생년월', '시군', '사고내용', '사상자수', '사고유형', '도로형태', '법규위반', '노면상태', '기상상태',
        '가해운전자_연령대', '피해운전자_차종']
write('11_야간사고_목록.csv', cols, [[r[c] for c in cols] for r in six if r['주야'] == '야간'])

# 12. 전북 농기계 보유대수 대비 사고 (전북 전체만 가능, 시군별 보유 자료 없음)
held = {r['연도']: num(r['보유대수']) for r in mach if r['기계'] == '합계' and r['규격'] == '소계'}
out = []
for y in sorted(held):
    rows = [r for r in jb if r['연도'] == y]
    night = sum(r['주야'] == '야간' for r in rows)
    out.append([y, held[y], len(rows), night, round(len(rows) / held[y] * 10000, 2), round(night / held[y] * 10000, 2)])
write('12_전북_보유대수대비사고.csv', ['연도', '보유대수', '사고', '야간사고', '1만대당사고', '1만대당야간사고'], out)

# 요약
night = [r for r in six if r['주야'] == '야간']
day = [r for r in six if r['주야'] == '주간']
sn, sd = stats(night), stats(day)
lines = [
    f"6개 시군 2021-2025 농기계 사고 {len(six)}건, 야간 {len(night)}건 ({100*len(night)/len(six):.1f}%)",
    f"사고당 사상자: 야간 {sn['사상자_per_사고']} vs 주간 {sd['사상자_per_사고']}",
    f"중상 이상 사고 비율: 야간 {sn['중상이상사고비율']}% vs 주간 {sd['중상이상사고비율']}%",
    f"사망: 야간 {sn['사망']} vs 주간 {sd['사망']}",
    f"야간 사고유형 차대차: {sum(r['사고유형_대']=='차대차' for r in night)}/{len(night)}, 주간 {sum(r['사고유형_대']=='차대차' for r in day)}/{len(day)}",
    f"야간 피해차종 승용·화물 등 다른 차와 충돌: {sum(r['피해운전자_차종']!='해당없음(단독사고)' for r in night)}/{len(night)}",
    f"야간 가해운전자 60세 이상: {sum(r['가해운전자_연령대'] in ('60-64세','65세 이상') for r in night)}/{len(night)}",
]


def fisher(a, b, c, d):
    # 2x2 Fisher 정확검정 양측 p값 (야간 a/a+b vs 주간 c/c+d)
    n, r1, c1 = a + b + c + d, a + b, a + c
    f = lambda x: math.comb(r1, x) * math.comb(n - r1, c1 - x)
    p0 = f(a)
    return sum(f(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1) if f(x) <= p0) / math.comb(n, c1)


def test(label, cond, rows_n=night, rows_d=day):
    a, c = sum(map(cond, rows_n)), sum(map(cond, rows_d))
    return [label, f'{a}/{len(rows_n)}', f'{c}/{len(rows_d)}', round(fisher(a, len(rows_n) - a, c, len(rows_d) - c), 3)]


tests = [
    test('승용차와 충돌', lambda r: r['피해운전자_차종'] == '승용'),
    test('다른 차·사람과 충돌(단독 아님)', lambda r: r['피해운전자_차종'] != '해당없음(단독사고)'),
    test('중상 이상 사고', lambda r: r['사고내용'] in ('사망사고', '중상사고')),
    test('중앙선침범', lambda r: r['법규위반'] == '중앙선침범'),
]
other = [r for r in jb if r['시군'] not in SIX]
tests.append(test('야간 사고 (6개시군 vs 전북 나머지)', lambda r: r['주야'] == '야간', six, other))
write('13_주야비교_검정.csv', ['항목', '야간(또는 6개시군)', '주간(또는 나머지)', 'Fisher_p'], tests)
lines += [f"{t[0]}: {t[1]} vs {t[2]}, p={t[3]}" for t in tests]

(D / '요약.txt').write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines))
