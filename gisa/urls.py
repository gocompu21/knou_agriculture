from django.urls import path

from . import views

app_name = "gisa"

urlpatterns = [
    # 자격증 목록/상세
    path("", views.certification_list, name="certification_list"),
    path("<int:cert_id>/", views.certification_detail, name="certification_detail"),
    # 학습모드
    path("<int:cert_id>/study/<int:exam_id>/<int:subject_id>/", views.study_mode, name="study_mode"),
    # 풀이모드
    path("<int:cert_id>/take/<int:exam_id>/", views.exam_take, name="exam_take"),
    path("<int:cert_id>/submit/<int:exam_id>/", views.exam_submit, name="exam_submit"),
    path("<int:cert_id>/result/<int:exam_id>/", views.exam_result, name="exam_result"),
    # 모의고사
    path("<int:cert_id>/mock/", views.mock_exam_take, name="mock_exam_take"),
    path("<int:cert_id>/mock/submit/", views.mock_exam_submit, name="mock_exam_submit"),
    path("<int:cert_id>/mock/result/<str:session_id>/", views.mock_exam_result, name="mock_exam_result"),
    # 오답노트
    path("<int:cert_id>/wrong/", views.wrong_answers, name="wrong_answers"),
    path("<int:cert_id>/wrong/session/<str:session_id>/", views.wrong_answers_session, name="wrong_answers_session"),
    path("<int:cert_id>/wrong/retry/", views.wrong_answers_retry, name="wrong_answers_retry"),
    path("<int:cert_id>/wrong/retry/submit/", views.wrong_answers_submit, name="wrong_answers_submit"),
    path("<int:cert_id>/wrong/retry/result/<str:session_id>/", views.wrong_answers_result, name="wrong_answers_result"),
    path("<int:cert_id>/wrong/dismiss/<int:question_id>/", views.wrong_dismiss, name="wrong_dismiss"),
    # 교재 학습
    path("<int:cert_id>/textbook/study/", views.textbook_study, name="textbook_study"),
    path("<int:cert_id>/textbook/chapter/", views.textbook_chapter_api, name="textbook_chapter_api"),
    # 세션 관리
    path("<int:cert_id>/session/<str:session_id>/delete/", views.session_delete, name="session_delete"),
    path("<int:cert_id>/session/delete-all/", views.session_delete_all, name="session_delete_all"),
]
