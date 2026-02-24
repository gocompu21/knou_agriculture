"""기사시험 최신기출 JSON을 update_or_create로 import하는 스크립트.

Usage:
    # 로컬: JSON 추출
    python load_gisa_latest.py export 식물보호기사

    # 서버: JSON import
    python load_gisa_latest.py import gisa_latest_식물보호기사.json
"""
import json, sys, os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from gisa.models import Certification, GisaExam, GisaQuestion, GisaSubject


def export_latest(cert_name):
    cert = Certification.objects.get(name=cert_name)
    qs = (
        GisaQuestion.objects.filter(exam__certification=cert, exam__exam_type="최신")
        .select_related("exam", "subject")
        .order_by("exam__year", "exam__round", "number")
    )
    data = []
    for q in qs:
        data.append({
            "cert_name": cert.name,
            "subject_name": q.subject.name,
            "year": q.exam.year,
            "round": q.exam.round,
            "number": q.number,
            "text": q.text,
            "choice_1": q.choice_1,
            "choice_2": q.choice_2,
            "choice_3": q.choice_3,
            "choice_4": q.choice_4,
            "answer": q.answer,
            "explanation": q.explanation or "",
            "choice_1_exp": q.choice_1_exp or "",
            "choice_2_exp": q.choice_2_exp or "",
            "choice_3_exp": q.choice_3_exp or "",
            "choice_4_exp": q.choice_4_exp or "",
        })

    filename = f"gisa_latest_{cert.name}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"추출 완료: {filename} ({len(data)}문항)")


def import_latest(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    created_count = 0
    updated_count = 0

    for item in data:
        cert = Certification.objects.get(name=item["cert_name"])
        subject = GisaSubject.objects.get(certification=cert, name=item["subject_name"])
        exam, _ = GisaExam.objects.get_or_create(
            certification=cert,
            year=item["year"],
            round=item["round"],
            exam_type="최신",
        )
        _, created = GisaQuestion.objects.update_or_create(
            exam=exam,
            number=item["number"],
            defaults={
                "subject": subject,
                "text": item["text"],
                "choice_1": item["choice_1"],
                "choice_2": item["choice_2"],
                "choice_3": item["choice_3"],
                "choice_4": item["choice_4"],
                "answer": item["answer"],
                "explanation": item.get("explanation", ""),
                "choice_1_exp": item.get("choice_1_exp", ""),
                "choice_2_exp": item.get("choice_2_exp", ""),
                "choice_3_exp": item.get("choice_3_exp", ""),
                "choice_4_exp": item.get("choice_4_exp", ""),
            },
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    print(f"완료: {created_count}개 신규, {updated_count}개 업데이트 (총 {len(data)}문항)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python load_gisa_latest.py export 식물보호기사")
        print("  python load_gisa_latest.py import gisa_latest_식물보호기사.json")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "export":
        export_latest(sys.argv[2])
    elif cmd == "import":
        import_latest(sys.argv[2])
    else:
        print(f"알 수 없는 명령: {cmd} (export 또는 import)")
        sys.exit(1)
