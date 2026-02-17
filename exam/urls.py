from django.urls import path

from . import views

app_name = "exam"

urlpatterns = [
    path("manage/", views.exam_manage, name="exam_manage"),
    path("manage/create/", views.exam_create, name="exam_create"),
    path("manage/<int:pk>/update/", views.exam_update, name="exam_update"),
    path("manage/<int:pk>/delete/", views.exam_delete, name="exam_delete"),
]
