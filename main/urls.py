from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path("mypage/", views.mypage, name="mypage"),
    path("mypage/favorite/<int:subject_id>/", views.favorite_toggle, name="favorite_toggle"),
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/<int:pk>/", views.subject_detail, name="subject_detail"),
    path("subjects/<int:pk>/latest/create/", views.latest_question_create, name="latest_question_create"),
    path("subjects/<int:pk>/latest/clone/", views.latest_question_clone, name="latest_question_clone"),
    path("subjects/<int:pk>/api/years/", views.api_existing_years, name="api_existing_years"),
    path("subjects/<int:pk>/api/questions/<int:year>/", views.api_existing_questions, name="api_existing_questions"),
    path("subjects/<int:pk>/api/search/", views.api_search_questions, name="api_search_questions"),
    path("subjects/<int:pk>/api/parse/", views.api_parse_text, name="api_parse_text"),
    path("subjects/<int:pk>/api/bulk-create/", views.api_bulk_create, name="api_bulk_create"),
    path("subjects/latest/<int:question_pk>/update/", views.latest_question_update, name="latest_question_update"),
    path("subjects/latest/<int:question_pk>/delete/", views.latest_question_delete, name="latest_question_delete"),
    path("manage/subjects/", views.subject_manage, name="subject_manage"),
    path("manage/subjects/create/", views.subject_create, name="subject_create"),
    path("manage/subjects/<int:pk>/update/", views.subject_update, name="subject_update"),
    path("manage/subjects/<int:pk>/delete/", views.subject_delete, name="subject_delete"),
    path("manage/members/", views.member_manage, name="member_manage"),
    path("manage/members/<int:pk>/toggle/", views.member_toggle, name="member_toggle"),
]
