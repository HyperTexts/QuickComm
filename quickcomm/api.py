
# This file houses the API views.


from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Author, Post, Comment, Follow, Like, ImageFile
from .serializers import AuthorSerializer, PostSerializer, CommentSerializer, FollowSerializer, LikeSerializer
from .models import Author, Post, Comment, Follow, Like
from .serializers import AuthorSerializer, AuthorsSerializer, PostSerializer, CommentSerializer, FollowSerializer, LikeSerializer, PostsSerializer

from drf_yasg.utils import swagger_auto_schema

# This file contains the viewsets for the API. Viewsets are almost like collections
# of views, with certain methods that can be mapped to different HTTP methods.
# Those mappings are done in the routers.

# NOTE: there are no docstrings for overrides of built-in methods.

# TODO what kind of response should we return for successful requests?
# TODO turn these into mixins
# TODO pagination


# create a decorator that checks if the user is authenticated using API authentication
def authAPI(view):
    def wrapper(self, request, *args, **kwargs):
        # if the user is authenticated, via either API or session authentication, then
        # call the view
        if request.user.is_authenticated:
            return view(self, request, *args, **kwargs)
        else:
            raise exceptions.AuthenticationFailed('Not authenticated')

    return wrapper

# create a decorator that checks if the user is the author of the object
def authAuthor(view):
    def wrapper(self, request, *args, **kwargs):
        # get the object
        obj = self.get_object()

        # check if the user is the author
        # TODO FIX ME we need to add a check for the current user being the author
        # after Jordan's changes
        if isinstance(request.user, User): # and request.user.author == obj:
            return view(self, request, *args, **kwargs)
        else:
            # raise a not authorized exception
            raise exceptions.PermissionDenied('Not authorized')

    return wrapper

class AuthorViewSet(viewsets.ModelViewSet):
    """This is a viewset that allows us to interact with the Author model."""

    queryset = Author.safe_queryset()
    serializer_class = AuthorSerializer
    pagination_class = AuthorsPagination
    http_method_names = ['get', 'patch', 'post']
    authentication_classes = [APIBasicAuthentication, SessionAuthentication]

    def get_queryset(self):
        self.paginator.url = self.request.build_absolute_uri()
        return super().get_queryset()


    @swagger_auto_schema(
        operation_summary="Get a list of all authors.",
        operation_description="This endpoint returns a list of all authors on the server.",
        responses={200: AuthorsSerializer},
    )
    # @authAPI
    def list(self, request):
        return super(AuthorViewSet, self).list(request)

    @swagger_auto_schema(
            operation_summary="Update parts of an author.",
            operation_description="This endpoint allows you to update parts of an author's profile. You must be authenticated as the author to do this.",
            responses={200: "Success", 404: "Author not found", 403: "Not authorized"},
            security=[{"BasicAuth": []}],
    )

    @authAPI
    @authAuthor
    def partial_update(*args, **kwargs):
        super().partial_update(*args, **kwargs)
        return Response(status=200)

    @swagger_auto_schema(
            operation_summary="Get the details of a specific author.",
            operation_description="This endpoint returns the details of a specific author.",
            responses={200: AuthorSerializer, 404: "Author not found"},
    )
    @authAPI
    def retrieve(self, *args, **kwargs):
        return super(AuthorViewSet, self).retrieve(*args, **kwargs)

class FollowerViewSet(viewsets.ModelViewSet):
    """This is a viewset that allows us to interact with the Follower model."""

    serializer_class = AuthorSerializer
    queryset = Author.objects.all()
    http_method_names = ['get']
    lookup_value_regex = '[^/]+'
    authentication_classes = [APIBasicAuthentication, SessionAuthentication]
    pagination_class = FollowersPagination

    def get_queryset(self):
        """Returns followers for this specific author."""

        self.paginator.url = self.request.build_absolute_uri()

        #check if authors_pk exists in kwargs
        if 'authors_pk' not in self.kwargs:
            return Author.objects.none()

        self.paginator.upper_response_param = 'author'
        self.paginator.upper_url = self.request.build_absolute_uri(reverse('author-detail', kwargs={'pk': self.kwargs['authors_pk']}))

        try:
            return Author.objects.filter(follower__following=self.kwargs['authors_pk'])
        except:
            raise exceptions.NotFound('Author not found')
        # return Follow.objects.filter(following=self.kwargs['authors_pk'])

    @swagger_auto_schema(
            operation_summary="Get a list of all followers for a specific author.",
            operation_description="This endpoint returns a list of all followers for a specific author.",
            responses={200: FollowersSerializer, 404: "Author not found"},
    )

    @authAPI
    def list(self, request, authors_pk=None):
        return super(FollowerViewSet, self).list(request)


    def retrieve(self, request, authors_pk=None, pk=None, *args, **kwargs):

        # determine if pk is a full URL or just the ID
        try:
            author = Author.objects.get(pk=authors_pk)
        except:
            raise exceptions.NotFound('Author not found')

        if pk.startswith('http'):
            # url decode the pk
            pk = urllib.parse.unquote(pk)
            # get the host of the author
            followingAuthor = Author.get_from_url(pk)
            # check if the author is following the author
        else:
            # TODO beware!!! We have to wrap any internal issues with this or redo 500 page
            try:
                followingAuthor = Author.objects.get(pk=pk)
            except:
                raise exceptions.NotFound('Author not found')

        if not followingAuthor:
            raise exceptions.NotFound('Author not found')

        if not followingAuthor.is_following(author):
            raise exceptions.NotFound('Author is not following')

        return Response(status=200, data={'detail': 'Author is following'})


class PostViewSet(viewsets.ModelViewSet):
    """This is a viewset that allows us to interact with the Post model."""

    serializer_class = PostSerializer
    queryset = Post.objects.all()
    http_method_names = ['get', 'put', 'post', 'delete']

    # TODO extend wiht decorators for unlisted and listed posts
    # these should also return 404s when not found, rather than
    # 403s

    def get_queryset(self):
        """Returns posts for this specific author."""

        # TODO use reverse
        self.paginator.url = self.request.build_absolute_uri()

        #check if authors_pk exists in kwargs
        if 'authors_pk' not in self.kwargs:
            return Post.objects.none()

        self.paginator.upper_response_param = 'author'
        self.paginator.upper_url = self.request.build_absolute_uri(reverse('author-detail', kwargs={'pk': self.kwargs['authors_pk']}))
        try:
            return Post.objects.filter(author=self.kwargs['authors_pk'])
        except:
            raise exceptions.NotFound('Author not found')

    @swagger_auto_schema(
            operation_summary="Get a list of all posts for a specific author.",
            operation_description="This endpoint returns a list of all posts for a specific author.",
            responses={200: PostsSerializer, 404: "Author not found"},
    )

    @authAPI
    def list(self, request, authors_pk=None):
        return super(PostViewSet, self).list(request)


    @swagger_auto_schema(
            operation_summary="Create a new post.",
            operation_description="This endpoint allows you to create a new post. You must be authenticated as the author to do this.",
            responses={200: "Success", 404: "Author not found", 403: "Not authorized"},
            security=[{"BasicAuth": []}],
    )
    @authAPI
    @authAuthor
    def create(self, request, authors_pk=None):
        super().create(request)
        return Response(status=200)

    @swagger_auto_schema(
            operation_summary="Perform a partial update of a specific post.",
            operation_description="This endpoint allows you to update parts of a post. You must be authenticated as the author to do this.",
            responses={200: "Success", 404: "Author not found", 403: "Not authorized"},
            security=[{"BasicAuth": []}],
    )
    @authAPI
    @authAuthor
    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        return Response(status=200)

    @swagger_auto_schema(
            operation_summary="Delete a specific post.",
            operation_description="This endpoint allows you to delete a post. You must be authenticated as the author to do this.",
            responses={200: "Success", 404: "Post not found", 403: "Not authorized"},
            security=[{"BasicAuth": []}],
    )
    @authAPI
    @authAuthor
    def destroy(self, request, *args, **kwargs):
        super().destroy(self, request, *args, **kwargs)
        return Response(status=200)

    @swagger_auto_schema(
            operation_summary="Return the contents of a post as an image.",
            operation_description="This endpoint allows to return the contents of a post as an image. If the post is an image, it will be returned as an image request to be used anywhere. Otherwise, it will not be found, even if the post exists.",
            responses={200: "Success", 404: "Post not found"},
            security=[],
    )
    @authAPI
    def image(self, request, authors_pk=None, pk=None):
        post = get_object_or_404(Post, pk=pk)
        if post.content_type != Post.PostType.PNG and post.content_type != Post.PostType.JPG:
            return Response(status=404)
        image = get_object_or_404(ImageFile, post=post)
        return FileResponse(image.image)

    @swagger_auto_schema(
            operation_summary="Replace the contents of a post.",
            operation_description="This endpoint allows you to replace the contents of a post. You must be authenticated as the author to do this.",
            responses={200: "Success", 404: "Post not found", 403: "Not authorized"},
            security=[{"BasicAuth": []}],
    )
    @authAPI
    @authAuthor
    def update(*args, **kwargs):
        return super().update(*args, **kwargs)

    @swagger_auto_schema(
            operation_summary="Get the details of a specific post.",
            operation_description="This endpoint returns the details of a specific post.",
            responses={200: PostSerializer, 404: "Post not found"},
    )
    @authAPI
    def retrieve(self, *args, **kwargs):
        return super().retrieve(self, *args, **kwargs)

    @authAPI
    def likes(self, request, authors_pk=None, pk=None):
        post = get_object_or_404(Post, pk=pk)
        queryset = post.likes.all()
        serializer = LikeActivitySerializer(queryset, many=True, context={'request': request})
        return Response({'type': 'likes', 'items': serializer.data})


class AuthorLikedViewSet(viewsets.ModelViewSet):
    serializer_class = LikeActivitySerializer
    pagination_class = AuthorLikedPagination
    # TODO this only returns likes for posts and not comments
    queryset = Like.objects.all()
    http_method_names = ['get']
    authentication_classes = [APIBasicAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Returns likes for this specific author."""
        self.paginator.url = self.request.build_absolute_uri()

        #check if authors_pk exists in kwargs
        if 'authors_pk' not in self.kwargs:
            return Like.objects.none()

        self.paginator.upper_response_param = 'author'
        self.paginator.upper_url = self.request.build_absolute_uri(reverse('author-detail', kwargs={'pk': self.kwargs['authors_pk']}))
        try:
            return Like.objects.filter(author=self.kwargs['authors_pk'])
        except:
            raise exceptions.NotFound('Author not found')

class PostLikesViewSet(viewsets.ModelViewSet):

    serializer_class = LikeActivitySerializer
    pagination_class = PostLikesPagination
    queryset = Like.objects.all()
    http_method_names = ['get']
    authentication_classes = [APIBasicAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Returns likes for this specific post and author."""
        self.paginator.url = self.request.build_absolute_uri()

        #check if authors_pk exists in kwargs
        if 'authors_pk' not in self.kwargs or 'posts_pk' not in self.kwargs:
            return Like.objects.none()

        self.paginator.upper_response_param = 'post'
        self.paginator.upper_url = self.request.build_absolute_uri(reverse('post-detail', kwargs={'authors_pk': self.kwargs['authors_pk'], 'pk': self.kwargs['posts_pk']}))
        try:
            return Like.objects.filter(post=self.kwargs['posts_pk'], post__author=self.kwargs['authors_pk'])
        except:
            raise exceptions.NotFound('Post not found')

class CommentLikesViewSet(viewsets.ModelViewSet):

    serializer_class = CommentLikeActivitySerializer
    pagination_class = CommentLikesPagination
    queryset = CommentLike.objects.all()
    http_method_names = ['get']
    authentication_classes = [APIBasicAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Returns likes for this specific comment and author."""
        self.paginator.url = self.request.build_absolute_uri()

        #check if authors_pk exists in kwargs
        if 'authors_pk' not in self.kwargs or 'posts_pk' not in self.kwargs or 'comments_pk' not in self.kwargs:
            return CommentLike.objects.none()

        self.paginator.upper_response_param = 'comment'
        self.paginator.upper_url = self.request.build_absolute_uri(reverse('comment-detail', kwargs={'authors_pk': self.kwargs['authors_pk'], 'posts_pk': self.kwargs['posts_pk'], 'pk': self.kwargs['comments_pk']}))
        try:
            return CommentLike.objects.filter(comment=self.kwargs['comments_pk'], comment__post=self.kwargs['posts_pk'], comment__post__author=self.kwargs['authors_pk'])
        except:
            raise exceptions.NotFound('Comment not found')


class CommentViewSet(viewsets.ModelViewSet):
    """This is a viewset that allows us to interact with the Comment model."""

    serializer_class = CommentSerializer
    pagination_class = CommentsPagination
    queryset = Comment.objects.all()
    http_method_names = ['get', 'post']
    authentication_classes = [APIBasicAuthentication, SessionAuthentication]

    # TODO extend wiht decorators for unlisted and listed posts
    # these should also return 404s when not found, rather than
    # 403s

    def get_queryset(self):
        """Returns comments for this specific post and author."""
        self.paginator.url = self.request.build_absolute_uri()

        #check if authors_pk exists in kwargs
        if 'authors_pk' not in self.kwargs or 'posts_pk' not in self.kwargs:
            return Comment.objects.none()

        self.paginator.upper_response_param = 'post'
        self.paginator.upper_url = self.request.build_absolute_uri(reverse('post-detail', kwargs={'authors_pk': self.kwargs['authors_pk'],
        'pk': self.kwargs['posts_pk']}))
        try:
            return Comment.objects.filter(post=self.kwargs['posts_pk'], author=self.kwargs['authors_pk'])
        except:
            raise exceptions.NotFound('Post or author not found.')

