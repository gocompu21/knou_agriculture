from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/<int:pk>/", views.subject_detail, name="subject_detail"),
    path("manage/subjects/", views.subject_manage, name="subject_manage"),
    path("manage/subjects/create/", views.subject_create, name="subject_create"),
    path("manage/subjects/<int:pk>/update/", views.subject_update, name="subject_update"),
    path("manage/subjects/<int:pk>/delete/", views.subject_delete, name="subject_delete"),
]
