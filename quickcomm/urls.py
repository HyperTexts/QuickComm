from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('create/plain', views.create_post, name='create_plain'),
    path('create/markdown', views.create_markdown, name='create_markdown'),
    path('create/image', views.create_image, name='create_image'),
]
