from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('create/plain', views.create_post, name='create_plain'),
    path('create/markdown', views.create_markdown, name='create_markdown'),
    path('authors/', views.view_authors, name='view_authors'),
    path('authors/<uuid:author_id>/', views.view_profile, name='view_profile'),
    path('authors/<uuid:author_id>/followers/', views.view_followers, name='view_followers'),
    path('authors/<uuid:author_id>/requests/', views.view_requests, name='view_requests')
]
