from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField
from rest_framework.reverse import reverse
from .models import Author, Post, Comment, Follow, Like

# This file contains the serializers for the API. Serializers are used to convert
# model objects into JSON.

class AuthorSerializer(serializers.ModelSerializer):
    """This is a serializer for the Author model."""

    type = serializers.CharField(default='author', read_only=True)
    id = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    url = serializers.HyperlinkedIdentityField( view_name='author-detail', read_only=True)
    profileImage = serializers.URLField(source='profile_image', required=False)
    host = serializers.URLField(required=False)
    displayName = serializers.CharField(source='display_name', required=False)
    github = serializers.URLField(required=False)

    # TODO keep GitHub as a URLField

    @staticmethod
    def get_examples():
        examples = {
            "type": "author",
            "id": "http://localhost:8000/api/authors/de574df8-6543-4566-b1cb-8cb74c70e8be/",
            "url": "http://localhost:8000/api/authors/de574df8-6543-4566-b1cb-8cb74c70e8be/",
            "host": "http://localhost:8000/",
            "displayName":"Greg Johnson",
            "github": "https://github.com/gjohnson",
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


class AuthorsSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='authors', read_only=True)
    data = AuthorSerializer(many=True, read_only=True)

    class Meta:
        model = Author
        fields = ['type', 'data']

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
            "unlisted": False
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
        fields = ('type', 'id', 'url', 'title', 'source', 'origin', 'description', 'contentType', 'content', 'author', 'categories', 'published', 'visibility', 'unlisted')


class PostsSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='posts', read_only=True)
    data = PostSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['type', 'data']

class CommentSerializer(serializers.ModelSerializer):
    # TODO implement this
    class Meta:
        model = Comment
        fields = ('id', 'comment', 'author', 'contentType', 'published', 'post')

class FollowSerializer(serializers.ModelSerializer):
    # TODO implement this
    class Meta:
        model = Follow
        fields = ('id', 'follower', 'author', 'host')

class LikeSerializer(serializers.ModelSerializer):
    # TODO implement this
    class Meta:
        model = Like
        fields = ('id', 'author', 'post')

