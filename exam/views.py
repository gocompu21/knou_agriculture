from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ExamForm
from .models import Exam


def staff_required(user):
    return user.is_staff


@login_required
@user_passes_test(staff_required)
def exam_manage(request):
    exams = Exam.objects.all()
    return render(request, "exam/exam_manage.html", {"exams": exams})


@login_required
@user_passes_test(staff_required)
def exam_create(request):
    if request.method == "POST":
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("exam:exam_manage")
    else:
        form = ExamForm()
    return render(request, "exam/exam_form.html", {"form": form, "is_edit": False})


@login_required
@user_passes_test(staff_required)
def exam_update(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == "POST":
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            return redirect("exam:exam_manage")
    else:
        form = ExamForm(instance=exam)
    return render(request, "exam/exam_form.html", {"form": form, "is_edit": True})


@login_required
@user_passes_test(staff_required)
def exam_delete(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == "POST":
        exam.delete()
        return redirect("exam:exam_manage")
    return redirect("exam:exam_manage")
