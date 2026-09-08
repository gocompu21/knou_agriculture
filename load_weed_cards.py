"""잡초 동정 카드(WeedCard) 적재 — 로컬·서버 공용.

  python load_weed_cards.py                 # 검증만
  python load_weed_cards.py --apply         # (subject, card_no) 기준 update_or_create

_weed_cards.json: PDF 를 직접 읽어 옮긴 카드 122종 (이름·카드번호·출제횟수·교수 메모 +
직접 쓴 과·생활형·발생지·식별 포인트·유사종 구별·방제).
이미지는 media/weeds/s<subject_pk>/ 에 미리 넣어 두어야 한다 (q###.jpg, a###.jpg).
"""
import json
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
sys.stdout.reconfigure(encoding="utf-8")

from django.conf import settings  # noqa: E402

from exam.models import WeedCard  # noqa: E402
from main.models import Subject  # noqa: E402

SUBJECT, GRADE = "잡초방제학", 4
subject = Subject.objects.get(name=SUBJECT, grade=GRADE)
cards = json.load(open("_weed_cards.json", encoding="utf-8"))
img_dir = os.path.join(settings.MEDIA_ROOT, "weeds", f"s{subject.pk}")

missing = [c[k] for c in cards for k in ("q_img", "a_img") if not os.path.exists(os.path.join(img_dir, c[k]))]
names = [c["name"] for c in cards]
print(f"카드 {len(cards)}종, 이미지 누락 {len(missing)}건, 이름 중복 {len(names) - len(set(names))}건")
if missing:
    print("  누락:", missing[:10])
    sys.exit(1)
if "--apply" not in sys.argv:
    print("(검증만 함. --apply 로 반영)")
    sys.exit(0)

n_new = n_upd = 0
for c in cards:
    obj, created = WeedCard.objects.update_or_create(
        subject=subject, card_no=c["card_no"],
        defaults={
            "order": c["order"], "name": c["name"], "family": c["family"],
            "life_form": c["life_form"], "habitat": c["habitat"],
            "features": c["features"], "similar": c["similar"], "control": c["control"],
            "notes": "\n".join(c.get("notes", [])), "exam_count": c.get("exam_count", 0),
            "q_image": f"weeds/s{subject.pk}/{c['q_img']}",
            "a_image": f"weeds/s{subject.pk}/{c['a_img']}",
        })
    n_new += created
    n_upd += (not created)
print(f"신규 {n_new}, 갱신 {n_upd} → 총 {WeedCard.objects.filter(subject=subject).count()}종")
