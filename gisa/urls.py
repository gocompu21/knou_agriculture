from django.urls import path

from . import resource_views
from . import cad, essay_views, pest, pesticide, views

app_name = "gisa"

urlpatterns = [
    # 자격증 목록/상세
    path("", views.certification_list, name="certification_list"),
    path("<int:cert_id>/", views.certification_detail, name="certification_detail"),
    # 최신기출
    path("<int:cert_id>/latest/create/", views.gisa_latest_create, name="gisa_latest_create"),
    path("<int:cert_id>/latest/<int:question_id>/update/", views.gisa_latest_update, name="gisa_latest_update"),
    path("<int:cert_id>/latest/<int:question_id>/delete/", views.gisa_latest_delete, name="gisa_latest_delete"),
    path("<int:cert_id>/latest/study/<int:year>/<int:round_num>/", views.gisa_latest_study, name="gisa_latest_study"),
    path("<int:cert_id>/latest/clone/", views.gisa_latest_clone, name="gisa_latest_clone"),
    path("<int:cert_id>/api/latest/exams/", views.api_gisa_existing_exams, name="api_gisa_existing_exams"),
    path("<int:cert_id>/api/latest/questions/<int:exam_id>/", views.api_gisa_exam_questions, name="api_gisa_exam_questions"),
    path("<int:cert_id>/api/latest/search/", views.api_gisa_search_questions, name="api_gisa_search_questions"),
    # 학습모드
    path("<int:cert_id>/study/<int:exam_id>/", views.study_mode, name="study_mode_all"),
    path("<int:cert_id>/study/<int:exam_id>/<int:subject_id>/", views.study_mode, name="study_mode"),
    path("<int:cert_id>/study/log/<int:question_id>/", views.study_log, name="study_log"),
    # 풀이모드
    path("<int:cert_id>/take/<int:exam_id>/", views.exam_take, name="exam_take"),
    path("<int:cert_id>/submit/<int:exam_id>/", views.exam_submit, name="exam_submit"),
    path("<int:cert_id>/result/<int:exam_id>/", views.exam_result, name="exam_result"),
    # 모의고사
    path("<int:cert_id>/mock/", views.mock_exam_take, name="mock_exam_take"),
    path("<int:cert_id>/mock/submit/", views.mock_exam_submit, name="mock_exam_submit"),
    path("<int:cert_id>/mock/mark-answered/", views.mock_mark_answered, name="mock_mark_answered"),
    path("<int:cert_id>/mock/result/<str:session_id>/", views.mock_exam_result, name="mock_exam_result"),
    # 오답노트
    path("<int:cert_id>/wrong/", views.wrong_answers, name="wrong_answers"),
    path("<int:cert_id>/wrong/session/<str:session_id>/", views.wrong_answers_session, name="wrong_answers_session"),
    path("<int:cert_id>/wrong/retry/", views.wrong_answers_retry, name="wrong_answers_retry"),
    path("<int:cert_id>/wrong/retry/submit/", views.wrong_answers_submit, name="wrong_answers_submit"),
    path("<int:cert_id>/wrong/retry/result/<str:session_id>/", views.wrong_answers_result, name="wrong_answers_result"),
    path("<int:cert_id>/wrong/dismiss/<int:question_id>/", views.wrong_dismiss, name="wrong_dismiss"),
    path("<int:cert_id>/wrong/review/<int:question_id>/", views.wrong_review, name="wrong_review"),
    path("<int:cert_id>/wrong/mark/<int:question_id>/", views.mark_wrong, name="mark_wrong"),
    # 교재 학습
    path("<int:cert_id>/textbook/study/", views.textbook_study, name="textbook_study"),
    path("<int:cert_id>/textbook/chapter/", views.textbook_chapter_api, name="textbook_chapter_api"),
    path("<int:cert_id>/textbook/questions/", views.api_textbook_questions, name="api_textbook_questions"),
    # 시험이력 API
    path("<int:cert_id>/api/history/", views.history_api, name="history_api"),
    # 세션 관리
    path("<int:cert_id>/session/<str:session_id>/delete/", views.session_delete, name="session_delete"),
    path("<int:cert_id>/session/delete-all/", views.session_delete_all, name="session_delete_all"),
    # 기사문제 관리
    path("manage/", views.gisa_question_manage, name="gisa_question_manage"),
    path("manage/grading/", essay_views.essay_grading_manage, name="essay_grading_manage"),
    path("manage/api/nouns/", views.manage_nouns, name="manage_nouns"),
    path("manage/api/search/", views.manage_search, name="manage_search"),
    path("manage/api/register/", views.manage_register, name="manage_register"),
    path("manage/question/<int:pk>/delete/", views.gisa_question_delete, name="gisa_question_delete"),
    path("manage/question/<int:pk>/update/", views.gisa_question_update, name="gisa_question_update"),
    path("manage/question/<int:pk>/generate-exp/", views.gisa_question_generate_exp, name="gisa_question_generate_exp"),
    # 용어집
    path("glossary/<int:pk>/delete/", views.glossary_delete, name="glossary_delete"),
    # 실기 필답형
    path("<int:cert_id>/essay/", essay_views.essay_list, name="essay_list"),
    path("<int:cert_id>/essay/take/", essay_views.essay_take, name="essay_take"),
    path("<int:cert_id>/essay/study/", essay_views.essay_study, name="essay_study"),
    path("<int:cert_id>/essay/overview/", essay_views.essay_overview, name="essay_overview"),
    path("<int:cert_id>/essay/work/", essay_views.essay_work, name="essay_work"),
    path("<int:cert_id>/essay/strategy/", essay_views.essay_strategy, name="essay_strategy"),
    path("<int:cert_id>/essay/pass/", essay_views.essay_pass, name="essay_pass"),
    # 자료실 — 유튜브·블로그. 필기 상세와 실기 목록이 같은 조각을 쓴다.
    path("<int:cert_id>/resources/add/", resource_views.resource_add, name="resource_add"),
    path("resources/<int:res_id>/delete/", resource_views.resource_delete, name="resource_delete"),
    path("resources/<int:res_id>/open/", resource_views.resource_open, name="resource_open"),
    # 동영상 — 분류(대>중) 관리와 영상 옮기기. 영상 등록은 resource_add 를 함께 쓴다.
    path("<int:cert_id>/videos/category/add/", resource_views.video_category_add, name="video_category_add"),
    path("videos/category/<int:cat_id>/edit/", resource_views.video_category_edit, name="video_category_edit"),
    path("videos/<int:res_id>/move/", resource_views.video_move, name="video_move"),
    path("videos/<int:res_id>/summarize/", resource_views.video_summarize, name="video_summarize"),
    path("<int:cert_id>/essay/<int:session_id>/submit/", essay_views.essay_submit, name="essay_submit"),
    path("<int:cert_id>/essay/<int:session_id>/save/", essay_views.essay_save, name="essay_save"),
    path("<int:cert_id>/essay/<int:session_id>/draft/", essay_views.essay_draft, name="essay_draft"),
    path("<int:cert_id>/essay/<int:session_id>/grade/<int:question_id>/", essay_views.essay_grade_step, name="essay_grade_step"),
    path("<int:cert_id>/essay/<int:session_id>/finish/", essay_views.essay_finish, name="essay_finish"),
    path("<int:cert_id>/essay/<int:session_id>/result/", essay_views.essay_result, name="essay_result"),
    path("<int:cert_id>/essay/<int:session_id>/sheet/", essay_views.essay_sheet, name="essay_sheet"),
    path("<int:cert_id>/essay/<int:session_id>/upload/", essay_views.essay_upload, name="essay_upload"),
    path("<int:cert_id>/essay/<int:session_id>/flatten/", essay_views.essay_flatten, name="essay_flatten"),
    path("<int:cert_id>/essay/<int:session_id>/overlay/", essay_views.essay_overlay, name="essay_overlay"),
    path("<int:cert_id>/essay/<int:session_id>/upload/remove/", essay_views.essay_upload_remove, name="essay_upload_remove"),
    path("<int:cert_id>/essay/<int:session_id>/confirm/", essay_views.essay_confirm, name="essay_confirm"),
    path("<int:cert_id>/essay/adjust/<int:attempt_id>/", essay_views.essay_adjust, name="essay_adjust"),
    path("<int:cert_id>/essay/grade-one/<int:question_id>/", essay_views.essay_grade_one, name="essay_grade_one"),
    path("<int:cert_id>/essay/siblings/<int:question_id>/", essay_views.essay_siblings, name="essay_siblings"),
    path("<int:cert_id>/essay/edit/<int:question_id>/", essay_views.essay_question_update, name="essay_question_update"),
    # 작업형 CAD 탭 — 도면(회원별)과 라이브러리 기호
    path("<int:cert_id>/cad/drawings/", cad.drawing_list, name="cad_drawing_list"),
    path("<int:cert_id>/cad/drawings/<int:pk>/", cad.drawing_get, name="cad_drawing_get"),
    path("<int:cert_id>/cad/drawings/save/", cad.drawing_save, name="cad_drawing_save"),
    path("<int:cert_id>/cad/drawings/<int:pk>/delete/", cad.drawing_delete, name="cad_drawing_delete"),
    path("cad/symbols/", cad.symbol_list, name="cad_symbol_list"),
    path("cad/symbols/save/", cad.symbol_save, name="cad_symbol_save"),
    path("cad/symbols/<int:pk>/delete/", cad.symbol_delete, name="cad_symbol_delete"),
    path("<int:cert_id>/essay/work/ref/<int:ref_id>/", essay_views.drawing_ref_update,
         name="drawing_ref_update"),
    path("<int:cert_id>/essay/note/<slug:slug>/", essay_views.essay_note, name="essay_note"),
    path("<int:cert_id>/essay/wrong/dismiss/<int:question_id>/", essay_views.essay_wrong_dismiss, name="essay_wrong_dismiss"),
    path("<int:cert_id>/essay/<int:session_id>/delete/", essay_views.essay_session_delete, name="essay_session_delete"),
    path("<int:cert_id>/essay/delete-all/", essay_views.essay_session_delete_all, name="essay_session_delete_all"),

    # 농약 DVD 암기카드 — 카드가 자격증에 매이지 않아 cert_id 를 받지 않는다.
    # 식물보호 두 급수가 같은 92종을 함께 쓴다.
    path("pesticide/next/", pesticide.api_next, name="pesticide_next"),
    path("pesticide/answer/", pesticide.api_answer, name="pesticide_answer"),
    path("pesticide/reset/", pesticide.api_reset, name="pesticide_reset"),
    path("pesticide/list/", pesticide.api_list, name="pesticide_list"),

    # 해충 DVD 암기카드 — 농약과 같이 자격증에 매이지 않는다
    path("pest/next/", pest.api_next, name="pest_next"),
    path("pest/answer/", pest.api_answer, name="pest_answer"),
    path("pest/reset/", pest.api_reset, name="pest_reset"),
    path("pest/list/", pest.api_list, name="pest_list"),
]
