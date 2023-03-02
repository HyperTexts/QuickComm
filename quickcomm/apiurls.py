
from django.urls import path, include

from quickcomm.routers import AuthorRouter, PostRouter
from . import api


author = AuthorRouter()
author.register(r'authors', api.AuthorViewSet)

post = PostRouter(author, r'authors', lookup='authors')
post.register(r'posts', api.PostViewSet)

urlpatterns = [
    path('', include(author.urls)),
    path('', include(post.urls)),
]