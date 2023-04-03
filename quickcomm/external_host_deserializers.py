

# This file deals with desearializing data from other servers. All of the
# requests will have their data "cached" in our database, so we can just
# access that data instead of making a request to the other server. The calls
# to other servers can then be made independently of our internal calls.

# TODO make sure that our API only return local hosts
# TODO achieve this by having special querysets in the models that only return items we want on the frontend
# TODO handle case where looking at an author's liked items returns a post or comment that doesn't exist on our server
# in that case, we don't want to represent the post or comment on our end, we just wanna store the external url

import uuid
from rest_framework import serializers
from django.core.files.base import ContentFile
from quickcomm.external_host_requests import Group1QCRequest, InternalQCRequest, MattGroupQCRequest, THTHQCRequest
from quickcomm.models import Author, Comment, CommentLike, Follow, FollowRequest, Host, Like, Post
import base64

from quickcomm.serializers import CommentActivitySerializer, CommentLikeActivitySerializer, FollowActivitySerializer, LikeActivitySerializer, PostActivitySerializer

# TODO use forms from creating items to validate data? that way we don't have duplicate information

def get_request_class_from_host(host: Host):
    if host is None:
        return InternalQCRequest(host, Deserializers, InboxSerializers)

    serializer_type = host.serializer_class
    if serializer_type == Host.SerializerClass.THTH:
        return THTHQCRequest(host, Deserializers, InboxSerializers)
    elif serializer_type == Host.SerializerClass.GROUP1:
        return Group1QCRequest(host, Deserializers, InboxSerializers)
    elif serializer_type == Host.SerializerClass.INTERNAL:
        return InternalQCRequest(host, Deserializers, InboxSerializers)
    elif serializer_type == Host.SerializerClass.MATTGROUP:
        return MattGroupQCRequest(host, Deserializers, InboxSerializers)
    else:
        raise Exception("Unknown serializer type")


def sync_authors(host: Host):
    """Get all authors from the remote API."""
    get_request_class_from_host(host).update_authors()

def sync_posts(author: Author):
    """Get all posts from the remote API."""
    get_request_class_from_host(author.host).update_posts(
        author
    )

def sync_comments(post: Post):
    """Get all comments from the remote API."""
    get_request_class_from_host(post.author.host).update_comments(
        post
    )

def sync_post_likes(post: Post):
    """Get all likes from the remote API."""
    get_request_class_from_host(post.author.host).update_post_likes(
        post
    )

def sync_comment_likes(comment: Comment):
    """Get all likes from the remote API."""
    get_request_class_from_host(comment.post.author.host).update_comment_likes(
        comment
    )

def sync_followers(author: Author):
    """Get all followers from the remote API."""
    get_request_class_from_host(author.host).update_followers(
        author
    )

def import_http_inbox_item(author: Author, item, host):
    """On a post request to the inbox, import the item into our database."""
    return get_request_class_from_host(host).import_inbox_item(
        item
    )


# The following classes are used to deserialize data from other servers. This
# data may be passed through a separate map to ensure it is valid, but it is
# not guaranteed to be valid. The data is then saved to the database.

class AuthorDeserializer(serializers.ModelSerializer):
    external_url = serializers.URLField()
    display_name = serializers.CharField()
    profile_image = serializers.URLField(required=False, allow_null=True)
    github = serializers.URLField(required=False, allow_null=True)

    # TODO error catching the save when type does not match
    # TODO don't overwrite the author if it is a local author, someone could try to attach it!
    # TODO move all of this to use get_from_url and discern between types of authors
    def save(self, host=None):
        author = Author.get_from_url(self.validated_data['external_url'])
        if author is None:
            author = Author.objects.create(**self.validated_data, host=host)
        else:
            # we can have an author without a host, but if we do have a host, it must match
            assert(author.host is None or host is None or author.host == host)
            author.display_name = self.validated_data['display_name']
            author.profile_image = self.validated_data['profile_image']
            author.github = self.validated_data['github']
            if author.external_url is not None:
                author.external_url = self.validated_data['external_url']
            author.save()

        return author

    class Meta:
        model = Author
        fields = ['external_url', 'display_name', 'profile_image', 'github']

class PostDeserializer(serializers.ModelSerializer):
    external_url = serializers.URLField()
    title = serializers.CharField()
    source = serializers.URLField(required=False, allow_null=True)
    origin = serializers.URLField(required=False, allow_null=True)
    description = serializers.CharField()
    content_type = serializers.ChoiceField(choices=Post.PostType.choices)
    content = serializers.CharField()
    # TODO add categories
    # FIXME serialize categories
    published = serializers.DateTimeField()
    visibility = serializers.ChoiceField(choices=Post.PostVisibility.choices)
    unlisted = serializers.BooleanField()

    def save(self, author=None):
        assert(author is not None)
        post = Post.objects.filter(external_url=self.validated_data['external_url']).first()
        if post is None:

            # TODO support application mimetype
            post = Post.objects.create(**self.validated_data, author=author)

        else:
            assert(post.author == author)
            post.title = self.validated_data['title']
            post.source = self.validated_data['source']
            post.origin = self.validated_data['origin']
            post.description = self.validated_data['description']
            post.content_type = self.validated_data['content_type']
            post.published = self.validated_data['published']
            post.visibility = self.validated_data['visibility']
            post.unlisted = self.validated_data['unlisted']
            post.external_url = self.validated_data['external_url']
            post.content = self.validated_data['content']

            post.save()

        return post


    class Meta:
        model = Post
        fields = ['title', 'source', 'origin', 'description', 'content_type', 'content', 'published', 'visibility', 'unlisted', 'external_url']



# TODO fix comment data types, right now only allow md and plaintext
class CommentDeserializer(serializers.ModelSerializer):
    # if external_url is not provided, then we will generate one as we assume this is a local comment
    external_url = serializers.URLField(required=False, allow_null=True)
    comment = serializers.CharField()
    published = serializers.DateTimeField()
    content_type = serializers.ChoiceField(choices=Post.PostType.choices)

    # TODO move to using kwargs
    def save(self, post=None, author=None):
        assert(post is not None)
        assert(author is not None)

        # if we have a comment that already exists, but without an external url, then we will update it
        # otherwise we will create a new comment
        comment = Comment.objects.filter(post=post, author=author, external_url=None, comment=self.validated_data['comment'],  content_type=self.validated_data['content_type']).first()
        if comment is not None:
            comment.external_url = self.validated_data['external_url']
            comment.save()
            return comment

        comment = Comment.objects.filter(external_url=self.validated_data['external_url']).first()
        if comment is None or self.validated_data['external_url'] is None:
            comment = Comment.objects.create(**self.validated_data, post=post, author=author)
        else:
            assert(comment.post == post)
            assert (comment.author == author)
            comment.comment = self.validated_data['comment']
            comment.published = self.validated_data['published']
            comment.content_type = self.validated_data['contentType']
            comment.external_url = self.validated_data['external_url']
            comment.save()

        return comment

    class Meta:
        model = Comment
        fields = ['comment', 'published','content_type', 'external_url']

class PostLikeDeserializer(serializers.ModelSerializer):

    def save(self, post=None, author=None):
        assert(post is not None)
        assert(author is not None)
        post_like = Like.objects.filter(
            post=post,
            author=author
        ).first()
        if post_like is None:
            post_like = Like.objects.create(**self.validated_data, post=post, author=author)
        else:
            assert(post_like.post == post)
            assert (post_like.author == author)
            post_like.save()

        return post_like

    class Meta:
        model = Like
        fields = []

class CommentLikeDeserializer(serializers.ModelSerializer):

    def save(self, comment=None, author=None):
        assert(comment is not None)
        assert(author is not None)
        comment_like = CommentLike.objects.filter(
            comment=comment,
            author=author
        ).first()
        if comment_like is None:
            comment_like = CommentLike.objects.create(**self.validated_data, comment=comment, author=author)
        else:
            assert(comment_like.comment == comment)
            assert (comment_like.author == author)
            comment_like.save()

        return comment_like

    class Meta:
        model = Like
        fields = []

class FollowerDeserializer(serializers.ModelSerializer):

    def save(self, author=None, following=None, request=False):
        assert(author is not None)
        assert(following is not None)
        item = Follow.objects.filter(
            follower=author,
            following=following
        ).first()
        if item is None:
            item = Follow.objects.create(**self.validated_data, follower=author, following=following)
        else:
            assert(item.follower == author)
            assert (item.following == following)

        return item

    class Meta:
        model = Follow
        fields = []

class FollowRequestDeserializer(serializers.ModelSerializer):

    def save(self, author=None, following=None, request=False):
        assert(author is not None)
        assert(following is not None)
        item = FollowRequest.objects.filter(
            from_user=author,
            to_user=following
        ).first()
        if item is None:
            item = FollowRequest.objects.create(**self.validated_data, from_user=author, to_user=following)
        else:
            assert(item.from_user == author)
            assert (item.to_user == following)

        return item
    class Meta:
        model = FollowRequest
        fields = []

class Deserializers:
    author = AuthorDeserializer
    post = PostDeserializer
    comment = CommentDeserializer
    post_like = PostLikeDeserializer
    comment_like = CommentLikeDeserializer
    follower = FollowerDeserializer
    follow_request = FollowRequestDeserializer


class InboxSerializers:
    post = PostActivitySerializer
    comment = CommentActivitySerializer
    post_like = LikeActivitySerializer
    comment_like = CommentLikeActivitySerializer
    follow = FollowActivitySerializer