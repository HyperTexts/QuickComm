
from django.urls import path, include

from quickcomm.routers import AuthorLikedRouter, AuthorRouter, CommentsRouter, InboxRouter, PostLikesRouter, PostRouter, FollowersRouter
from . import api


# This file contains all the urls that the API will use. They override the default
# routers to define custom methods on the views.

author = AuthorRouter()
author.register(r'authors', api.AuthorViewSet)

liked = AuthorLikedRouter(author, r'authors', lookup='authors')
liked.register(r'liked', api.AuthorLikedViewSet, basename='liked')

post = PostRouter(author, r'authors', lookup='authors')
post.register(r'posts', api.PostViewSet)

postlikes = PostLikesRouter(post, r'posts', lookup='posts')
postlikes.register(r'likes', api.PostLikesViewSet, basename='likes')

follower = FollowersRouter(author, r'authors', lookup='authors')
follower.register(r'followers', api.FollowerViewSet)

comment = CommentsRouter(post, r'posts', lookup='posts')
comment.register(r'comments', api.CommentViewSet)

commentlikes = PostLikesRouter(comment, r'comments', lookup='comments')
commentlikes.register(r'likes', api.CommentLikesViewSet, basename='likes')

inbox = InboxRouter(author, r'authors', lookup='authors')
inbox.register(r'inbox', api.InboxViewSet)

urlpatterns = [
    path('', include(author.urls)),
    path('', include(post.urls)),
    path('', include(follower.urls)),
    path('', include(comment.urls)),
    path('', include(inbox.urls)),
    path('', include(postlikes.urls)),
    path('', include(commentlikes.urls)),
    path('', include(liked.urls)),
]