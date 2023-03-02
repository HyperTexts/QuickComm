from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField
from rest_framework.reverse import reverse

from .models import Author, Post, Comment, Follow, Like

class AuthorSerializer(serializers.ModelSerializer):

    type = serializers.CharField(default='author', read_only=True)
    id = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    url = serializers.HyperlinkedIdentityField( view_name='author-detail', read_only=True)
    profileImage = serializers.URLField(source='profile_image', required=False)
    host = serializers.URLField(required=False)
    displayName = serializers.CharField(source='display_name', required=False)
    github = serializers.URLField(required=False)

    class Meta:
        model = Author
        fields = ['type', 'id', 'url', 'host', 'displayName', 'github', 'profileImage']


class PostSerializer(serializers.ModelSerializer):

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

    # https://stackoverflow.com/questions/19775507/django-rest-framework-hyperlinking-a-nested-relationship
    def get_id(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(reverse('post-detail', kwargs={'pk': obj.id.__str__(), 'authors_pk': obj.author_id.__str__()}))


    class Meta:
        model = Post
        fields = ('type', 'id', 'url', 'title', 'source', 'origin', 'description', 'contentType', 'content', 'author', 'categories', 'published', 'visibility', 'unlisted')



class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'comment', 'author', 'contentType', 'published', 'post')

class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('id', 'follower', 'author', 'host')

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ('id', 'author', 'post')
