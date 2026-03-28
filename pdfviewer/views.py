from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import UploadedPDF


@login_required
def pdf_list(request):
    """PDF 목록 + 업로드"""
    if request.method == 'POST':
        file = request.FILES.get('pdf_file')
        if file:
            title = request.POST.get('title', '').strip()
            if not title:
                title = file.name.replace('.pdf', '').replace('.PDF', '')
            UploadedPDF.objects.create(user=request.user, title=title, file=file)
            return redirect('pdfviewer:pdf_list')
    pdfs = UploadedPDF.objects.filter(user=request.user)
    return render(request, 'pdfviewer/list.html', {'pdfs': pdfs})


@login_required
def pdf_view(request, pk):
    """PDF 뷰어 페이지"""
    pdf = get_object_or_404(UploadedPDF, pk=pk, user=request.user)
    return render(request, 'pdfviewer/viewer.html', {'pdf': pdf})


@login_required
def pdf_delete(request, pk):
    """PDF 삭제"""
    pdf = get_object_or_404(UploadedPDF, pk=pk, user=request.user)
    if request.method == 'POST':
        pdf.file.delete(save=False)
        pdf.delete()
    return redirect('pdfviewer:pdf_list')
