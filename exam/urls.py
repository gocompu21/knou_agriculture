from django.urls import path

from . import views

app_name = "exam"

urlpatterns = [
    path("study/<int:subject_id>/<int:year>/", views.study_mode, name="study_mode"),
    path("take/<int:subject_id>/<int:year>/", views.exam_take, name="exam_take"),
    path("submit/<int:subject_id>/<int:year>/", views.exam_submit, name="exam_submit"),
    path("result/<int:subject_id>/<int:year>/", views.exam_result, name="exam_result"),
    path("manage/", views.exam_manage, name="exam_manage"),
    path("manage/create/", views.exam_create, name="exam_create"),
    path("manage/<int:pk>/update/", views.exam_update, name="exam_update"),
    path("manage/<int:pk>/delete/", views.exam_delete, name="exam_delete"),
    path("manage/questions/", views.question_manage, name="question_manage"),
    path("manage/questions/<int:pk>/delete/", views.question_delete, name="question_delete"),
]
