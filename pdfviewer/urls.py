from django.urls import path
from . import views

app_name = 'pdfviewer'

urlpatterns = [
    path('', views.pdf_list, name='pdf_list'),
    path('<int:pk>/', views.pdf_view, name='pdf_view'),
    path('<int:pk>/delete/', views.pdf_delete, name='pdf_delete'),
]
