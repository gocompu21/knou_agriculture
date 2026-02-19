from django.urls import path

from . import views

app_name = "exam"

urlpatterns = [
    path("study/<int:subject_id>/<int:year>/", views.study_mode, name="study_mode"),
    path("take/<int:subject_id>/<int:year>/", views.exam_take, name="exam_take"),
    path("submit/<int:subject_id>/<int:year>/", views.exam_submit, name="exam_submit"),
    path("result/<int:subject_id>/<int:year>/", views.exam_result, name="exam_result"),
    # 모의고사
    path("mock/<int:subject_id>/", views.mock_exam_take, name="mock_exam_take"),
    path("mock/<int:subject_id>/submit/", views.mock_exam_submit, name="mock_exam_submit"),
    path("mock/<int:subject_id>/result/<str:session_id>/", views.mock_exam_result, name="mock_exam_result"),
    # 오답노트
    path("wrong/<int:subject_id>/", views.wrong_answers, name="wrong_answers"),
    path("wrong/<int:subject_id>/session/<str:session_id>/", views.wrong_answers_session, name="wrong_answers_session"),
    path("wrong/<int:subject_id>/retry/", views.wrong_answers_retry, name="wrong_answers_retry"),
    path("wrong/<int:subject_id>/retry/submit/", views.wrong_answers_submit, name="wrong_answers_submit"),
    path("wrong/<int:subject_id>/retry/result/<str:session_id>/", views.wrong_answers_result, name="wrong_answers_result"),
    # 숙지완료
    path("wrong/<int:subject_id>/dismiss/<int:question_id>/", views.wrong_dismiss, name="wrong_dismiss"),
    # 세션 삭제
    path("session/<int:subject_id>/<str:session_id>/delete/", views.session_delete, name="session_delete"),
    path("session/<int:subject_id>/delete-all/", views.session_delete_all, name="session_delete_all"),
    # 관리
    path("manage/", views.exam_manage, name="exam_manage"),
    path("manage/create/", views.exam_create, name="exam_create"),
    path("manage/<int:pk>/update/", views.exam_update, name="exam_update"),
    path("manage/<int:pk>/delete/", views.exam_delete, name="exam_delete"),
    path("manage/questions/", views.question_manage, name="question_manage"),
    path("manage/questions/<int:pk>/delete/", views.question_delete, name="question_delete"),
]
