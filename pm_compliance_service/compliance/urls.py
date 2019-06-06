from django.conf.urls import include, url
from django.urls import path

from rest_framework.authtoken import views as rest_views

from . import views

app_name = "compliance"

timestamp_regex = '\\d{4}[-]?\\d{1,2}[-]?\\d{1,2} \\d{1,2}:\\d{1,2}:\\d{1,2}'

urlpatterns = [
    path('about/', views.AboutView.as_view(), name='about'),
]
