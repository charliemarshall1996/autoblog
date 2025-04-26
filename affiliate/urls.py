from django.urls import path
from . import views

urlpatterns = [
    path('click/', views.track_affiliate_click, name='affiliate_click'),
]
