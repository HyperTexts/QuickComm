from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField
from rest_framework.reverse import reverse
from django.urls import reverse as django_reverse
from .models import Author, Post, Comment, Follow, Like
from .pagination import CommentsPagination
from django.core.paginator import Paginator


# This file contains the serializers for the API. Serializers are used to convert
# model objects into JSON.



class AuthorSerializer(serializers.ModelSerializer):
    """This is a serializer for the Author model."""

    type = serializers.CharField(default='author', read_only=True)
    id = serializers.SerializerMethodField(method_name='get_id')
    url = serializers.SerializerMethodField(method_name='get_id')
    profileImage = serializers.URLField(source='profile_image', required=False)
    host = serializers.SerializerMethodField(method_name='get_host')
    displayName = serializers.CharField(source='display_name', required=False)
    github = serializers.CharField(required=False)

    # TODO keep GitHub as a URLField


    def get_host(self, obj):
        """This method defines a custom getter that returns the absolute URL of
        the author as the ID."""
        request = self.context.get('request')
        if obj.host is None:
            return request.build_absolute_uri("/api/")
        return obj.host.url

    def get_id(self, obj):
        """This method defines a custom getter that returns the absolute URL of
        the author as the ID."""
        request = self.context.get('request')
        if obj.host is None:
            return request.build_absolute_uri(reverse('author-detail', args=[obj.id]))
        else:
            return obj.external_url


    @staticmethod
    def get_examples():
        examples = {
            "type": "author",
            "id": "http://localhost:8000/api/authors/de574df8-6543-4566-b1cb-8cb74c70e8be/",
            "url": "http://localhost:8000/api/authors/de574df8-6543-4566-b1cb-8cb74c70e8be/",
            "host": "http://localhost:8000/",
            "displayName":"Greg Johnson",
            "github": "gjohnson",
            "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
        }
        return examples

    @staticmethod
    def get_descriptions():
        descriptions = {
            "type": "The type of object. Must be 'author'.",
            "id": "The unique identifier for the author.",
            "url": "The URL of the author.",
            "host": "The host machine of the author. This is where the author's profile is hosted.",
            "displayName": "The display name of the author.",
            "github": "The username of a GitHub profile.",
            "profileImage": "The URL of the author's profile image. This can be hosted anywhere."
        }
        return descriptions

    class Meta:
        model = Author
        fields = ['type', 'id', 'url', 'host', 'displayName', 'github', 'profileImage']

# TODO fix time unit of published
class CommentSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='comment', read_only=True)
    author = AuthorSerializer(read_only=True)
    comment = serializers.CharField(required=False)
    contentType = serializers.CharField(required=False, source='content_type')
    published = serializers.DateTimeField(required=False)
    id = serializers.SerializerMethodField()


    def get_id(self, obj):
        """This method defines a custom getter that returns the absolute URL of
        the post as the ID."""
        request = self.context.get('request')
        return request.build_absolute_uri(reverse('comment-detail', kwargs={'pk': obj.id.__str__(), 'posts_pk': obj.post_id.__str__(), 'authors_pk': obj.post.author_id.__str__()}))

    @staticmethod
    def get_examples():
        examples = {
            "type": "comment",
            "comment": "This is a comment.",
            "contentType": "text/plain",
            "published": "2020-04-03T20:00:00Z",
            "id": "http://localhost:8000/api/authors/de574df8-6543-4566-b1cb-8cb74c70e8be/posts/de574df8-6543-4566-b1cb-8cb74c70e2be/comments/de574df8-6543-4566-b1cb-8cb74c70e0be/"
        }
        return examples
    class Meta:
        model = Comment
        fields = ('type','author', 'comment', 'contentType', 'published',  'id')

def get_paginated_serializer(pagination_class, serializer, example=None):
    class PaginatedItems(serializers.ModelSerializer):

        id = serializers.URLField()
        type = serializers.CharField(default=pagination_class.response_type, read_only=True)
        page = serializers.IntegerField(read_only=True)
        size = serializers.IntegerField(read_only=True)
        # TODO use pagination_class to get the correct item
        items = serializer(many=True, read_only=True)

        @staticmethod
        def get_examples():
            return {
                "type": pagination_class.response_type,
                "id": "http://localhost:8000/api/authors" if example is None else example,
                "page": 1,
                "size": 10,
            }

        @staticmethod
        def get_descriptions():
            return {
                "type": "The type of object.",
                "id": "The unique identifier for the response.",
                "page": "The current page.",
                "size": "The number of items per page.",
            }

        class Meta:
            model = serializer.Meta.model
            ref_name = serializer.Meta.model.__name__ + 'Paginated'
            fields = ['id', 'type', 'page', 'size', 'items']

    return PaginatedItems

class FollowersSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='followers', read_only=True)
    items = AuthorSerializer(many=True, read_only=True)

    class Meta:
        model = Author
        fields = ['type', 'items']

class PostSerializer(serializers.ModelSerializer):
    """This is a serializer for the Post model."""

    parent_lookup_kwargs = {
        'author_id': 'author_id'
    }

    type = serializers.CharField(default='post', read_only=True)
    id = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField(method_name='get_id')
    title = serializers.CharField(required=False)
    source = serializers.URLField(required=False)
    origin = serializers.URLField(required=False)
    description = serializers.CharField(required=False)
    contentType = serializers.CharField(required=False, source='content_type')
    content = serializers.CharField(required=False)
    author = AuthorSerializer(read_only=True)
    categories = serializers.ListField(child=serializers.CharField(), required=False)
    published = serializers.DateTimeField(required=False)
    visibility = serializers.CharField(required=False)
    unlisted = serializers.BooleanField(required=False)

    # get pagination comments
    commentsSrc = serializers.SerializerMethodField(method_name='get_comments_src')
    comments = serializers.SerializerMethodField(method_name='get_comments')
    count = serializers.IntegerField(required=False, read_only=True)

    def get_comments(self, obj):
        return self.context.get('request').build_absolute_uri(
        reverse('comment-list', kwargs={'authors_pk': obj.author_id.__str__(), 'posts_pk': obj.id.__str__()}))

    def get_comments_src(self, obj):
        page = 1,
        size = 10
        request = self.context.get('request')


        comments = Comment.objects.filter(post_id=obj.id).order_by('published')
        paginator = Paginator(comments, size)
        comments = paginator.get_page(page)
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return {
            "type": "comments",
            "page": page,
            "size": size,
            "post": request.build_absolute_uri(reverse('post-detail', kwargs={'authors_pk': obj.author_id.__str__(), 'pk': obj.id.__str__()})),
            "id": request.build_absolute_uri(reverse('comment-list', kwargs={'authors_pk': obj.author_id.__str__(), 'posts_pk': obj.id.__str__()
                                                                             })),
            "comments": serializer.data,
        }




    @staticmethod
    def get_examples():
        examples = {
            "type": "post",
            "title":"A post title about a post about web dev",
            "id": "http://localhost:8000/api/authors/e3b90f3f-1c01-4b60-aaf6-01a1554505df/posts/eb5901f2-b85b-4656-8940-c85dedab7b91/",
            "url": "http://localhost:8000/api/authors/e3b90f3f-1c01-4b60-aaf6-01a1554505df/posts/eb5901f2-b85b-4656-8940-c85dedab7b91/",
            "source":"http://lastplaceigotthisfrom.com/posts/yyyyy",
            "origin":"http://whereitcamefrom.com/posts/zzzzz",
            "description":"This post discusses stuff -- brief",
            "contentType": "text/markdown",
            "content": "This is my first post!",
            "categories":["web","tutorial"],
            "visibility": "PUBLIC",
            "unlisted": False,
            "comments": "http://localhost:8000/api/authors/e3b90f3f-1c01-4b60-aaf6-01a1554505df/posts/eb5901f2-b85b-4656-8940-c85dedab7b91/comments/",
            "count": 1,
            "commentsSrc": {
                "type": "comments",
                "page": 1,
                "size": 10,
                "post": "http://localhost:8000/api/authors/e3b90f3f-1c01-4b60-aaf6-01a1554505df/posts/eb5901f2-b85b-4656-8940-c85dedab7b91/",
                "id": "http://localhost:8000/api/authors/e3b90f3f-1c01-4b60-aaf6-01a1554505df/posts/eb5901f2-b85b-4656-8940-c85dedab7b91/comments/",
                "comments": [
                    {
                        "type": "comment",
                        "id": "http://localhost:8000/api/authors/e3b90f3f-1c01-4b60-aaf6-01a1554505df/posts/eb5901f2-b85b-4656-8940-c85dedab7b91/comments/eb5901f2-b85b-4656-8940-c85dedab7b91/",
                        "author": {
                            "type": "author",
                            "id": "http://localhost:8000/api/authors/e3b90f3f-1c01-4b60-aaf6-01a1554505df/",
                            "host": "http://localhost:8000/",
                            "displayName": "Test User",
                            "url": "http://localhost:8000/api/authors/e3b90f3f-1c01-4b60-aaf6-01a1554505df/",
                            "github": "http://github.com/testuser"
                        },
                        "comment": "This is a comment!",
                        "contentType": "text/plain",
                        "published": "2019-04-20T20:00:00Z",
                    }
                ]

            }
        }
        return examples

    @staticmethod
    def get_descriptions():
        descriptions = {
            "type": "The type of object. Must be 'post'.",
            "id": "The unique identifier for the post.",
            "url": "The URL of the post.",
            "title": "The title of the post.",
            "source": "The URL of where this post was taken from.",
            "origin": "The URL of where this post was originally from.",
            "description": "A brief description of the post.",
            "contentType": "The content type of the post. Must be one of 'text/markdown', 'text/plain', 'image/png;base64', 'image/jpeg;base64', or 'application/base64'.",
            "content": "The content of the post.",
            "categories": "A list of categories that the post belongs to.",
            "published": "The date and time that the post was published.",
            "visibility": "The visibility of the post. Must be 'PUBLIC', or 'PRIVATE'.",
            "unlisted": "Whether the post is unlisted or not."
        }
        return descriptions

    # Sample code taken from https://stackoverflow.com/questions/19775507/django-rest-framework-hyperlinking-a-nested-relationship
    def get_id(self, obj):
        """This method defines a custom getter that returns the absolute URL of
        the post as the ID."""
        request = self.context.get('request')
        return request.build_absolute_uri(reverse('post-detail', kwargs={'pk': obj.id.__str__(), 'authors_pk': obj.author_id.__str__()}))

    class Meta:
        model = Post
        fields = ('type', 'id', 'url', 'title', 'source', 'origin', 'description', 'contentType', 'content', 'author', 'categories', 'published', 'visibility', 'unlisted', 'count', 'comments', 'commentsSrc')



# THIS IS ONLY USED FOR DOCUMENTATION
# TODO use this instead of hardcoding dictionaries in the views
class PostsSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='posts', read_only=True)
    items = PostSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['type', 'items']



class FollowActivitySerializer(serializers.ModelSerializer):

    type = serializers.CharField(default='Follow', read_only=True)
    summary = serializers.SerializerMethodField()
    actor = AuthorSerializer(read_only=True, source='follower')
    object = AuthorSerializer(read_only=True, source='following')

    def get_summary(self, obj):
        return obj.follower.display_name.__str__() + " wants to follow " + obj.following.display_name.__str__()

    class Meta:
        model = Follow
        fields = ('@context', 'summary', 'type', 'actor', 'object')
        extra_kwargs = {
            '@context': {'read_only': True, 'source': 'context'},
        }

class PostActivitySerializer(serializers.ModelSerializer):

    type = serializers.CharField(default='Post', read_only=True)
    summary = serializers.SerializerMethodField()
    author = AuthorSerializer(read_only=True)
    object = PostSerializer(read_only=True, source='*')

    def get_summary(self, obj):
        return obj.author.display_name.__str__() + " posted a new post"

    class Meta:
        model = Post
        fields = ('@context', 'summary', 'type', 'author', 'object')
        extra_kwargs = {
            '@context': {'read_only': True, 'source': 'context'},
        }

class CommentActivitySerializer(serializers.ModelSerializer):

        type = serializers.CharField(default='Comment', read_only=True)
        summary = serializers.SerializerMethodField()
        author = AuthorSerializer(read_only=True)
        comment = CommentSerializer(read_only=True, source='*')
        object = serializers.SerializerMethodField()

        def get_object(self, obj):
            if obj.post.external_url:
                return obj.post.external_url
            request = self.context.get('request')
            return request.build_absolute_uri(reverse('post-detail', kwargs={'authors_pk': obj.author_id.__str__(), 'posts_pk': obj.post_id.__str__()}))

        def get_summary(self, obj):
            return obj.author.display_name.__str__() + " commented on your post"


        class Meta:
            model = Comment
            fields = ('@context', 'summary', 'type', 'author', 'comment', 'object')
            extra_kwargs = {
                '@context': {'read_only': True, 'source': 'context'},
            }


class LikeActivitySerializer(serializers.ModelSerializer):

    type = serializers.CharField(default='Like', read_only=True)
    summary = serializers.SerializerMethodField()
    author = AuthorSerializer(read_only=True)
    object = serializers.SerializerMethodField()

    def get_object(self, obj):
        if obj.post.external_url:
            return obj.post.external_url
        request = self.context.get('request')
        return request.build_absolute_uri(reverse('post-detail', kwargs={'pk': obj.post_id.__str__(), 'authors_pk': obj.author_id.__str__()}))

    def get_summary(self, obj):
        return obj.author.display_name.__str__() + " Likes your post"

    def get_context(self, obj):
        return 'https://www.w3.org/ns/activitystreams'

    @staticmethod
    def get_examples():
        return {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Like",
            "summary": "Alice Likes your post",
            "object": "http://localhost:8000/api/authors/e3b90f3f-1c01-4b60-aaf6-01a1554505df/posts/eb5901f2-b85b-4656-8940-c85dedab7b91/"
        }

    @staticmethod
    def get_descriptions():
        return {
            "@context": "The context of the activity. Must be 'https://www.w3.org/ns/activitystreams'.",
            "type": "The type of the activity. Must be 'Like'.",
            "summary": "A description of the activity.",
            "object": "The object of the activity."
        }

    class Meta:
        model = Like
        fields = ('@context', 'summary', 'type', 'author', 'object')
        extra_kwargs = {
            '@context': {'source': 'context', 'read_only': True},
        }

class CommentLikeActivitySerializer(serializers.ModelSerializer):

    type = serializers.CharField(default='Like', read_only=True)
    summary = serializers.SerializerMethodField()
    author = AuthorSerializer(read_only=True)
    object = serializers.SerializerMethodField()

    def get_object(self, obj):
        if obj.comment.external_url:
            return obj.comment.external_url
        request = self.context.get('request')
        return request.build_absolute_uri(reverse('comment-detail', kwargs={'pk': obj.comment_id.__str__(), 'authors_pk': obj.author_id.__str__(), 'posts_pk': obj.comment.post_id.__str__()}))

    def get_summary(self, obj):
        return obj.author.display_name.__str__() + " Likes your comment"

    def get_context(self, obj):
        return 'https://www.w3.org/ns/activitystreams'

    class Meta:
        model = Like
        fields = ('@context', 'summary', 'type', 'author', 'object')
        extra_kwargs = {
            '@context': {'source': 'context', 'read_only': True},
        }

