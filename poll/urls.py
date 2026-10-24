from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "poll"

# /poll/ 은 강의실 프로젝터용 QR 화면, 수강생 휴대폰 설문은 /poll/s/ (QR 이 가리키는 곳)
urlpatterns = [
    path("", views.qr, name="qr"),
    path("s/", views.survey, name="survey"),
    path("thanks/", views.thanks, name="thanks"),
    path("qr/", RedirectView.as_view(pattern_name="poll:qr", permanent=False)),
    path("count/", views.count, name="count"),
    path("stats/", views.stats, name="stats"),
    path("stats/csv/", views.stats_csv, name="stats_csv"),
]
