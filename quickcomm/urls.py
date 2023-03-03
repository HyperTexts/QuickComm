from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('create/plain', views.create_post, name='create_plain'),
    path('create/markdown', views.create_markdown, name='create_markdown'),
    path('post/<uuid:post_id>/', views.post_view, name='post_view'),
    path('post/<uuid:post_id>/post_liked', views.post_like, name='post_like'),
    path('post/<uuid:post_id>/post_comment', views.post_comment, name='post_comment')
]
