
# This file houses the API views.

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Author, Post, Comment, Follow, Like, ImageFile
from .serializers import AuthorSerializer, PostSerializer, CommentSerializer, FollowSerializer, LikeSerializer

# This file contains the viewsets for the API. Viewsets are almost like collections
# of views, with certain methods that can be mapped to different HTTP methods.
# Those mappings are done in the routers.

# NOTE: there are no docstrings for overrides of built-in methods.

# TODO what kind of response should we return for successful requests?
# TODO turn these into mixins

class AuthorViewSet(viewsets.ModelViewSet):
    """This is a viewset that allows us to interact with the Author model."""

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    http_method_names = ['get', 'patch', 'post']

    def list(self, request):
        queryset = Author.objects.all()
        serializer = AuthorSerializer(queryset, many=True, context={'request': request})
        return Response({'type': 'authors', 'data': serializer.data})

    def partial_update(*args, **kwargs):
        super().partial_update(*args, **kwargs)
        return Response(status=200)

class PostViewSet(viewsets.ModelViewSet):
    """This is a viewset that allows us to interact with the Post model."""

    serializer_class = PostSerializer
    queryset = Post.objects.all()
    http_method_names = ['get', 'put', 'post', 'delete']

    # TODO extend wiht decorators for unlisted and listed posts
    # these should also return 404s when not found, rather than
    # 403s

    # Sample code taken from decorator tutorial: https://realpython.com/primer-on-python-decorators/
    def verify_same_author(func):
        """This is a decorator that checks that the user is authenticated and that the author matches the logged in user.
        This is similar to middleware, but it is applied to a specific function. We can use this to reuse the same code
        and ensure it is well-written."""
        def wrapper(self, request, *args, **kwargs):
            # check that the user is authenticated
            if not request.user.is_authenticated:
                return Response(status=403)

            # check that the author matches the logged in use
            author = Author.objects.get(user=request.user)
            if author.id != self.kwargs['authors_pk']:
                return Response(status=403)
            return func(self, request, *args, **kwargs)
        return wrapper

    def get_queryset(self):
        """Returns posts for this specific author."""
        return Post.objects.filter(author=self.kwargs['authors_pk'])

    def list(self, request, authors_pk=None):
        queryset = self.get_queryset()
        serializer = PostSerializer(queryset, many=True, context={'request': request})
        return Response({'type': 'posts', 'data': serializer.data})

    @verify_same_author
    def create(self, request, authors_pk=None):
        super().create(request)
        return Response(status=200)

    @verify_same_author
    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        return Response(status=200)

    @verify_same_author
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(status=200)

    def image(self, request, authors_pk=None, pk=None):
        post = get_object_or_404(Post, pk=pk)
        if post.content_type != Post.PostType.PNG and post.content_type != Post.PostType.JPG:
            return Response(status=404)
        image = get_object_or_404(ImageFile, post=post)
        return FileResponse(image.image)



class CommentViewSet(viewsets.ModelViewSet):
    # TODO implement
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

class FollowViewSet(viewsets.ModelViewSet):
    # TODO implement
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer

class LikeViewSet(viewsets.ModelViewSet):
    # TODO implement
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
