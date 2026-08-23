# -*- coding: utf-8 -*-
"""선지 해설의 상투 문구("옳은 설명입니다", "정답입니다" 등)를 제거해 자연스럽게 다듬는다.

  python fix_boiler.py            # 변경 목록 생성(_boiler_changes.json)만
  python fix_boiler.py --apply    # 로컬 DB 반영
서버 반영은 load_boiler.py (_boiler_changes.json 의 before/after 안전장치 방식).
"""
import io, os, sys, re, json, django
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from gisa.models import GisaQuestion

F = ["choice_1_exp", "choice_2_exp", "choice_3_exp", "choice_4_exp"]

# 판정 문장이 내용의 일부인 것 — 건드리지 않는다 (부분 정답 분석)
SKIP = {(4308, "choice_3_exp"), (4308, "choice_4_exp")}

# 직접 읽고 정한 수동 교정 (규칙으로는 어색해지는 경우)
MANUAL = {
 (19220,"choice_1_exp"):[("따라서 넓은 보호지역이 더 많은 종을 보전할 수 있다는 것은 옳은 설명입니다.","따라서 넓은 보호지역이 더 많은 종을 보전할 수 있습니다.")],
 (19257,"choice_3_exp"):[("작성할 수 있도록 한 것은 옳은 내용입니다.","작성할 수 있도록 하고 있습니다.")],
 (18965,"choice_3_exp"):[("순수 자연과학에 머무르지 않는다는 점에서 옳은 서술입니다.","순수 자연과학에 머무르지 않는 학문입니다.")],
 (18831,"choice_4_exp"):[("안정된 수원을 확보하는 것은 옳은 설명입니다.","안정된 수원을 확보해야 합니다.")],
 (18271,"choice_2_exp"):[("생물학적 질소고정이라 불리는 이 과정은 옳은 설명입니다.","이 과정을 생물학적 질소고정이라 부릅니다.")],
 (4193,"choice_4_exp"):[("따라서 벼에는 잎귀와 잎혀가 있으나 피에는 없는 ④번이 가장 옳은 설명입니다. ","")],
 (5761,"choice_2_exp"):[(" 따라서 일년생 잡초에도 적용된다는 ②번은 옳은 설명입니다.","")],
 (3796,"choice_2_exp"):[(" 따라서 한 생육기 동안 몇 미터밖에 이동하지 못한다는 것은 맞는 설명입니다.","")],
 (3736,"choice_2_exp"):[(" 따라서 습지에서도 많이 자생하는 것은 맞는 설명입니다.","")],
 (3768,"choice_1_exp"):[(" 따라서 식용으로 연결된 것은 올바른 설명입니다.","")],
 (3768,"choice_2_exp"):[(" 따라서 수질정화로 연결된 것은 올바른 설명입니다.","")],
 (3768,"choice_3_exp"):[(" 따라서 한방약용으로 연결된 것은 올바른 설명입니다.","")],
 (3588,"choice_4_exp"):[(" 따라서 무도 가해하는 것은 올바른 설명입니다.","")],
 (18102,"choice_1_exp"):[("법 제2조에 정의되어 있어 옳은 서술입니다.","법 제2조에 정의되어 있습니다.")],
 (7892,"choice_1_exp"):[(" 따라서 보기 ①은 옳은 설명입니다.","")],
 (7892,"choice_2_exp"):[(" 따라서 보기 ②는 옳은 설명입니다.","")],
 (7892,"choice_4_exp"):[(" 따라서 보기 ④는 옳은 설명입니다.","")],
 (18322,"choice_4_exp"):[("안정적인 서식지 조성을 위한 옳은 설명입니다.","안정적인 서식지 조성을 위한 기본 원칙입니다.")],
 (1636,"choice_1_exp"):[("(나)의 '높아'는 올바른 설명입니다.","(나)의 '높아'는 맞는 표현입니다.")],
 (4326,"choice_1_exp"):[(" 따라서 '불연성이다'는 옳은 설명입니다.","")],
 (4326,"choice_3_exp"):[(" 따라서 '수용액은 인화성이나 폭발성이 없다'는 옳은 설명입니다.","")],
 (4326,"choice_4_exp"):[(" 따라서 '피부에 접촉하면 침식시키고 눈에 들어가면 점막을 격렬히 자극하므로 세척해야 한다'는 옳은 설명입니다.","")],
 (5233,"choice_1_exp"):[("따라서 '비선택성 제초제'는 맞는 설명입니다.","따라서 '비선택성 제초제'에 해당합니다.")],
 (5233,"choice_2_exp"):[("따라서 '경엽처리형 제초제'는 맞는 설명입니다.","따라서 '경엽처리형 제초제'에 해당합니다.")],
 (5233,"choice_3_exp"):[("따라서 '접촉형 제초제'는 맞는 설명입니다.","따라서 '접촉형 제초제'에 해당합니다.")],
 (3714,"choice_4_exp"):[("격리된 밀폐된 공간에서 사용하며, 이는 올바른 설명입니다.","격리된 밀폐된 공간에서 사용합니다.")],
 (5487,"choice_1_exp"):[(" 따라서 '효과가 늦은 편이다'는 생물적 방제법의 올바른 설명입니다.","")],
}

V = "옳은|맞는|올바른"; N = "설명|서술|내용"
LEAD = re.compile(r'^(?:이 설명은\s*|이것은\s*|이는\s*)?(?:정답입니다|오답입니다|(?:옳은|맞는|올바른|적절한|적합한|정확한|틀린|잘못된|옳지 않은)\s*(?:설명|서술|내용|연결|정의|원칙|조합|짝|보기)입니다)[.!]?\s*')
SENT = re.compile(r'\s*(?:이는|따라서)?\s*(?:이 보기는|해당 설명은|이 설명은|[①②③④]번은|이 조합은|[가-힣A-Za-z()·\s]{0,10}의)?\s*(?:'+V+r')\s*(?:'+N+r')입니다[.!]')
ATTR = re.compile(r'(?<=[는닌한된운인])\s('+V+r')\s('+N+r')입니다')
G1 = re.compile(r'([가-힣]+)으므로,?\s*(?:'+V+r')\s*(?:'+N+r')입니다')
G2 = re.compile(r'([가-힣])므로,?\s*(?:'+V+r')\s*(?:'+N+r')입니다')
G3a = re.compile(r'([가-힣]+)으며,?\s*(?:이는\s*)?(?:'+V+r')\s*(?:'+N+r')입니다')
G3b = re.compile(r'([가-힣])며,?\s*(?:이는\s*)?(?:'+V+r')\s*(?:'+N+r')입니다')
G4 = re.compile(r'(?<!므)(?:으로서?|로서?),?\s+(?:'+V+r')\s*(?:'+N+r')입니다')

def decl(m):
    """X므로/X며 → 서술형 종결 (하→합니다, 되→됩니다, 들→듭니다)"""
    ch = m.group(1); o = ord(ch) - 0xAC00
    if 0 <= o <= 11171:
        if o % 28 == 0:            # 받침 없음 → ㅂ받침 추가
            return chr(ord(ch) + 17) + "니다"
        if o % 28 == 8:            # ㄹ받침 → ㄹ탈락 + ㅂ받침 (줄어들→줄어듭)
            return chr(ord(ch) + 9) + "니다"
    return m.group(0)

def transform(v, key):
    if key in SKIP:
        return v
    new = v
    for old, rep in MANUAL.get(key, []):
        if old in new:
            new = new.replace(old, rep)
    m = LEAD.match(new)
    if m and len(new[m.end():].strip()) >= 15:
        new = new[m.end():].lstrip()
    new = G1.sub(lambda m: m.group(1) + "습니다", new)
    new = G2.sub(decl, new)
    new = G3a.sub(lambda m: m.group(1) + "습니다", new)
    new = G3b.sub(decl, new)
    new = G4.sub("입니다", new)
    def drop(mo):
        s = mo.start()
        if s == 0 or new[:s].rstrip().endswith('.'):
            return ''
        return mo.group(0)
    new = SENT.sub(drop, new)
    new = ATTR.sub(lambda m2: ' ' + m2.group(2) + '입니다', new)
    new = re.sub(r'[ \t]{2,}', ' ', new).strip()
    return new

def main():
    apply = "--apply" in sys.argv
    rows = []
    for q in GisaQuestion.objects.select_related("exam__certification", "exam").iterator():
        for f in F:
            v = getattr(q, f) or ''
            if not v:
                continue
            nv = transform(v, (q.pk, f))
            if nv != v:
                rows.append({"pk": q.pk, "cert": q.exam.certification.name,
                             "ref": f"{q.exam.year}-{q.exam.round}-{q.number}",
                             "field": f, "before": v, "after": nv})
    json.dump(rows, open('_boiler_changes.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('변경', len(rows), '필드')
    left = re.compile(r'(' + V + r')\s*(' + N + r')입니다|^정답입니다|^오답입니다')
    bad = [(r['ref'], r['field'], r['after'][:80]) for r in rows if left.search(r['after'])]
    print('변환 후 상투구 잔존(의도된 SKIP 제외):', len(bad))
    for b in bad: print('  ', *b)
    if apply:
        for r in rows:
            q = GisaQuestion.objects.get(pk=r["pk"])
            if getattr(q, r["field"]) == r["before"]:
                setattr(q, r["field"], r["after"]); q.save(update_fields=[r["field"]])
        print('로컬 반영 완료')

if __name__ == '__main__':
    main()
