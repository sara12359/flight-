from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('airport-search/', views.airport_search, name='airport_search'),
]
