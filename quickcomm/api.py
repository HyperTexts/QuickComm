
# This file houses the API views.

from rest_framework import viewsets
from rest_framework.response import Response

from .models import Author, Post, Comment, Follow, Like
from .serializers import AuthorSerializer, AuthorsSerializer, PostSerializer, CommentSerializer, FollowSerializer, LikeSerializer, PostsSerializer

from drf_yasg.utils import swagger_auto_schema

# This file contains the viewsets for the API. Viewsets are almost like collections
# of views, with certain methods that can be mapped to different HTTP methods.
# Those mappings are done in the routers.

# NOTE: there are no docstrings for overrides of built-in methods.

# TODO what kind of response should we return for successful requests?
# TODO turn these into mixins

class AuthorViewSet(viewsets.ModelViewSet):

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    http_method_names = ['get', 'patch', 'post']

    @swagger_auto_schema(
        operation_summary="Get a list of all authors.",
        operation_description="This endpoint returns a list of all authors on the server.",
        responses={200: AuthorsSerializer},
    )
    def list(self, request):
        queryset = Author.objects.all()
        serializer = AuthorSerializer(queryset, many=True, context={'request': request})
        return Response({'type': 'authors', 'data': serializer.data})

    @swagger_auto_schema(
            operation_summary="Update parts of an author.",
            operation_description="This endpoint allows you to update parts of an author's profile. You must be authenticated as the author to do this.",
            responses={200: "Success", 404: "Author not found", 403: "Not authorized"},
            security=[{"BasicAuth": []}],
    )
    def partial_update(*args, **kwargs):
        super().partial_update(*args, **kwargs)
        return Response(status=200)

    @swagger_auto_schema(
            operation_summary="Get the details of a specific author.",
            operation_description="This endpoint returns the details of a specific author.",
            responses={200: AuthorSerializer, 404: "Author not found"},
    )
    def retrieve(self, *args, **kwargs):
        return super(AuthorViewSet, self).retrieve(*args, **kwargs)

class PostViewSet(viewsets.ModelViewSet):

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
        #check if authors_pk exists in kwargs
        if 'authors_pk' not in self.kwargs:
            return Post.objects.none()
        return Post.objects.filter(author=self.kwargs['authors_pk'])

    @swagger_auto_schema(
            operation_summary="Get a list of all posts for a specific author.",
            operation_description="This endpoint returns a list of all posts for a specific author.",
            responses={200: PostsSerializer, 404: "Author not found"},
    )
    def list(self, request, authors_pk=None):
        queryset = self.get_queryset()
        serializer = PostSerializer(queryset, many=True, context={'request': request})
        return Response({'type': 'posts', 'data': serializer.data})

    @swagger_auto_schema(
            operation_summary="Create a new post.",
            operation_description="This endpoint allows you to create a new post. You must be authenticated as the author to do this.",
            responses={200: "Success", 404: "Author not found", 403: "Not authorized"},
            security=[{"BasicAuth": []}],
    )
    @verify_same_author
    def create(self, request, authors_pk=None):
        super().create(request)
        return Response(status=200)

    @swagger_auto_schema(
            operation_summary="Perform a partial update of a specific post.",
            operation_description="This endpoint allows you to update parts of a post. You must be authenticated as the author to do this.",
            responses={200: "Success", 404: "Author not found", 403: "Not authorized"},
            security=[{"BasicAuth": []}],
    )
    @verify_same_author
    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        return Response(status=200)

    @swagger_auto_schema(
            operation_summary="Delete a specific post.",
            operation_description="This endpoint allows you to delete a post. You must be authenticated as the author to do this.",
            responses={200: "Success", 404: "Post not found", 403: "Not authorized"},
            security=[{"BasicAuth": []}],
    )
    @verify_same_author
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(status=200)

    @swagger_auto_schema(
            operation_summary="Replace the contents of a post.",
            operation_description="This endpoint allows you to replace the contents of a post. You must be authenticated as the author to do this.",
            responses={200: "Success", 404: "Post not found", 403: "Not authorized"},
            security=[{"BasicAuth": []}],
    )
    @verify_same_author
    def update(*args, **kwargs):
        return super().update(*args, **kwargs)

    @swagger_auto_schema(
            operation_summary="Get the details of a specific post.",
            operation_description="This endpoint returns the details of a specific post.",
            responses={200: PostSerializer, 404: "Post not found"},
    )
    def retrieve(*args, **kwargs):
        return super().retrieve(*args, **kwargs)



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
