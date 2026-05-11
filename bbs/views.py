import hmac
import hashlib
import os
import re
import threading
import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import UserProfile
from .models import Comment, Notice, NoticeOpenLog

SITE_URL = "https://hanulstudy.kr"

# 트래킹 픽셀 1x1 투명 PNG (정적 바이트)
_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _track_token(notice_id, user_id):
    """HMAC-SHA256 토큰 (앞 16자) — 위변조 방지."""
    msg = f"{notice_id}:{user_id}".encode()
    key = settings.SECRET_KEY.encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()[:16]


def _track_pixel_url(notice_id, user_id):
    token = _track_token(notice_id, user_id)
    return f"{SITE_URL}/bbs/track/{notice_id}/{user_id}/{token}.png"


def _send_notice_email(notice, recipient_users):
    """공지사항 이메일을 회원별로 트래킹 픽셀과 함께 발송 (개별 발송)."""
    content_html = re.sub(
        r'src="(/media/[^"]+)"',
        rf'src="{SITE_URL}\1"',
        notice.content,
    )

    def _send():
        for u in recipient_users:
            if not u.email:
                continue
            pixel = _track_pixel_url(notice.pk, u.pk)
            body_html = (
                f'<div style="font-family:sans-serif;max-width:600px;margin:0 auto;">'
                f'<p style="color:#555;">안녕하세요, 한울회 A+ 학습시스템입니다.</p>'
                f'<p>새로운 공지사항이 등록되었습니다.</p>'
                f'<h2 style="color:#1b4332;margin:16px 0 8px;">{notice.title}</h2>'
                f'<hr style="border:none;border-top:1px solid #ddd;">'
                f'<div style="padding:12px 0;line-height:1.7;">{content_html}</div>'
                f'<hr style="border:none;border-top:1px solid #ddd;">'
                f'<p><a href="{SITE_URL}/bbs/{notice.pk}/" '
                f'style="color:#1b4332;font-weight:bold;">전체 내용 보기 →</a></p>'
                f'<p style="color:#999;font-size:0.82em;margin-top:18px;text-align:center;">'
                f'본 메일은 <strong>한울회 A+ 학습시스템</strong>(hanulstudy.kr)에서 발송된 공식 안내입니다.<br>'
                f'발신 계정: gocompu21@gmail.com (운영자 Gmail로 발송)'
                f'</p>'
                f'<img src="{pixel}" width="1" height="1" alt="" style="display:none">'
                f'</div>'
            )
            msg = EmailMessage(
                subject=f"[한울회 A+] 공지사항: {notice.title}",
                body=body_html,
                # from_email 생략 → settings.DEFAULT_FROM_EMAIL 사용
                to=[u.email],
            )
            msg.content_subtype = "html"
            try:
                msg.send(fail_silently=True)
            except Exception:
                pass

    threading.Thread(target=_send, daemon=True).start()


def notice_track_pixel(request, notice_id, user_id, token):
    """1x1 투명 PNG 반환 + 열람 기록 저장. HMAC 토큰으로 위변조 차단."""
    expected = _track_token(notice_id, user_id)
    if hmac.compare_digest(expected, token):
        try:
            ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() \
                or request.META.get("REMOTE_ADDR")
            ua = request.META.get("HTTP_USER_AGENT", "")[:300]
            NoticeOpenLog.objects.create(
                notice_id=notice_id,
                user_id=user_id,
                ip=ip or None,
                user_agent=ua,
            )
        except Exception:
            pass
    response = HttpResponse(_PIXEL_PNG, content_type="image/png")
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    return response


def notice_list(request):
    pinned = Notice.objects.filter(is_pinned=True)
    return render(request, "bbs/notice_list.html", {"pinned": pinned})


def notice_api(request):
    page = int(request.GET.get("page", 1))
    per_page = 15
    qs = Notice.objects.filter(is_pinned=False)
    total = qs.count()
    start = (page - 1) * per_page
    rows = qs[start : start + per_page]

    results = []
    for n in rows:
        results.append(
            {
                "id": n.pk,
                "title": n.title,
                "author": n.author.first_name or n.author.username if n.author else "",
                "created_at": n.created_at.strftime("%Y-%m-%d %H:%M"),
                "view_count": n.view_count,
                "comment_count": n.comments.count(),
            }
        )

    return JsonResponse(
        {"notices": results, "has_next": (start + per_page) < total, "total": total}
    )


@login_required
def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    notice.view_count += 1
    notice.save(update_fields=["view_count"])

    comments = notice.comments.select_related("author").all()
    nearby = Notice.objects.exclude(pk=pk)[:10]
    can_edit = request.user == notice.author or request.user.is_staff

    # 메일 열람 통계 (스태프 전용)
    open_stats = None
    if request.user.is_staff:
        from django.db.models import Count, Max
        opened_users = (
            NoticeOpenLog.objects.filter(notice=notice)
            .values("user_id", "user__username", "user__first_name")
            .annotate(opens=Count("id"), last_opened=Max("opened_at"))
            .order_by("-last_opened")
        )
        opt_out_count = UserProfile.objects.filter(receive_email=False).count()
        sent_total = (
            User.objects.filter(is_active=True)
            .exclude(email="")
            .count() - opt_out_count
        )
        open_stats = {
            "sent": max(sent_total, 0),
            "opened": len(opened_users),
            "opened_list": list(opened_users),
        }

    return render(
        request,
        "bbs/notice_detail.html",
        {
            "notice": notice,
            "comments": comments,
            "nearby": nearby,
            "can_edit": can_edit,
            "open_stats": open_stats,
        },
    )


@login_required
def notice_create(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        is_pinned = request.POST.get("is_pinned") == "on" and request.user.is_staff

        if title and content:
            notice = Notice.objects.create(
                title=title,
                content=content,
                author=request.user,
                is_pinned=is_pinned,
            )

            # 전체 회원에게 이메일 발송 (개별 발송 + 트래킹 픽셀, 수신 거부 제외)
            opt_out_ids = set(
                UserProfile.objects.filter(receive_email=False)
                .values_list("user_id", flat=True)
            )
            recipient_users = list(
                User.objects.filter(is_active=True)
                .exclude(email="")
                .exclude(pk__in=opt_out_ids)
            )
            if recipient_users:
                _send_notice_email(notice, recipient_users)

            return redirect("bbs:notice_list")

    return render(request, "bbs/notice_form.html", {"mode": "create"})


@login_required
def notice_update(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.user != notice.author and not request.user.is_staff:
        return redirect("bbs:notice_detail", pk=pk)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()

        if title and content:
            notice.title = title
            notice.content = content
            if request.user.is_staff:
                notice.is_pinned = request.POST.get("is_pinned") == "on"
            notice.save()
            return redirect("bbs:notice_detail", pk=pk)

    return render(
        request, "bbs/notice_form.html", {"mode": "update", "notice": notice}
    )


@login_required
@require_POST
def notice_delete(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.user == notice.author or request.user.is_staff:
        notice.delete()
    return redirect("bbs:notice_list")


@login_required
@require_POST
def comment_create(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    content = request.POST.get("content", "").strip()
    if content:
        Comment.objects.create(notice=notice, author=request.user, content=content)
    return redirect("bbs:notice_detail", pk=pk)


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    notice_pk = comment.notice.pk
    if request.user == comment.author or request.user.is_staff:
        comment.delete()
    return redirect("bbs:notice_detail", pk=notice_pk)


@login_required
@require_POST
def image_upload(request):
    if not request.FILES.get("file"):
        return JsonResponse({"error": "파일이 없습니다."}, status=400)

    uploaded = request.FILES["file"]

    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if uploaded.content_type not in allowed_types:
        return JsonResponse({"error": "허용되지 않는 파일 형식입니다."}, status=400)

    upload_dir = os.path.join(settings.MEDIA_ROOT, "bbs", "images")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(uploaded.name)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        ext = ".jpg"

    filename = f"bbs_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb+") as f:
        for chunk in uploaded.chunks():
            f.write(chunk)

    return JsonResponse({"url": f"{settings.MEDIA_URL}bbs/images/{filename}"})
