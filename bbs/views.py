import os
import re
import threading
import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import UserProfile
from .models import Comment, Notice

SITE_URL = "https://hanulstudy.kr"


def _send_notice_email(notice, recipients):
    """공지사항 이메일을 별도 스레드에서 발송한다."""
    content_html = re.sub(
        r'src="(/media/[^"]+)"',
        rf'src="{SITE_URL}\1"',
        notice.content,
    )
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
        f'</div>'
    )
    msg = EmailMessage(
        subject=f"[한울회 A+] 공지사항: {notice.title}",
        body=body_html,
        from_email="admin@hanulstudy.kr",
        bcc=recipients,
    )
    msg.content_subtype = "html"
    threading.Thread(target=msg.send, kwargs={"fail_silently": True}, daemon=True).start()


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

    return render(
        request,
        "bbs/notice_detail.html",
        {
            "notice": notice,
            "comments": comments,
            "nearby": nearby,
            "can_edit": can_edit,
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

            # 전체 회원에게 이메일 발송 (BCC, 이메일 수신 거부 회원 제외)
            opt_out_ids = set(
                UserProfile.objects.filter(receive_email=False)
                .values_list("user_id", flat=True)
            )
            recipients = list(
                User.objects.filter(is_active=True)
                .exclude(email="")
                .exclude(pk__in=opt_out_ids)
                .values_list("email", flat=True)
            )
            if recipients:
                _send_notice_email(notice, recipients)

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
