from django.urls import path

from . import views

app_name = "bbs"

urlpatterns = [
    path("", views.notice_list, name="notice_list"),
    path("api/notices/", views.notice_api, name="notice_api"),
    path("create/", views.notice_create, name="notice_create"),
    path("<int:pk>/", views.notice_detail, name="notice_detail"),
    path("<int:pk>/update/", views.notice_update, name="notice_update"),
    path("<int:pk>/delete/", views.notice_delete, name="notice_delete"),
    path("<int:pk>/comment/", views.comment_create, name="comment_create"),
    path("comment/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
    path("image/upload/", views.image_upload, name="image_upload"),
]
