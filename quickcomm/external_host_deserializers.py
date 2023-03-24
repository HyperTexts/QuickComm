

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
from quickcomm.external_host_requests import InternalQCRequest, THTHQCRequest
from quickcomm.models import Author, Comment, CommentLike, Follow, Host, ImageFile, Like, Post
import base64

from quickcomm.serializers import CommentActivitySerializer, CommentLikeActivitySerializer, FollowActivitySerializer, LikeActivitySerializer, PostActivitySerializer

# TODO use forms from creating items to validate data? that way we don't have duplicate information

def get_request_class_from_host(host: Host):
    if host is None:
        return InternalQCRequest(host, Deserializers, InboxSerializers)

    serializer_type = host.serializer_class
    if serializer_type == Host.SerializerClass.THTH:
        return THTHQCRequest(host, Deserializers, InboxSerializers)
    elif serializer_type == Host.SerializerClass.INTERNAL:
        return InternalQCRequest(host, Deserializers, InboxSerializers)
    else:
        raise Exception("Unknown serializer type")


def sync_authors(host: Host):
    """Syncs the authors with the remote API."""
    get_request_class_from_host(host).update_authors()

def sync_posts(author: Author):
    get_request_class_from_host(author.host).update_posts(
        author
    )

def sync_comments(post: Post):
    get_request_class_from_host(post.author.host).update_comments(
        post
    )

def sync_post_likes(post: Post):
    get_request_class_from_host(post.author.host).update_post_likes(
        post
    )

def sync_comment_likes(comment: Comment):
    get_request_class_from_host(comment.post.author.host).update_comment_likes(
        comment
    )

def sync_followers(author: Author):
    get_request_class_from_host(author.host).update_followers(
        author
    )

def import_http_inbox_item(author: Author, item, host):
    return get_request_class_from_host(host).import_inbox_item(
        item
    )

class AuthorDeserializer(serializers.ModelSerializer):
    external_url = serializers.URLField()
    display_name = serializers.CharField()
    profile_image = serializers.URLField(required=False, allow_null=True)
    github = serializers.URLField(required=False, allow_null=True)

    # TODO error catching the save when type does not match
    def save(self, host=None):

        author = Author.objects.filter(external_url=self.validated_data['external_url']).first()
        if author is None:

            # check if the external url is a local author
            # if so, just return that author
            # TODO don't just use id checking, verify that the host is the same too
            if host is None:
                potential_id = self.validated_data['external_url'].split('/')[-1]
                try:
                    author = Author.objects.filter(id=potential_id).first()
                    if author is not None:
                        return author
                except:
                    pass

            author = Author.objects.create(**self.validated_data, host=host)
        else:
            # we can have an author without a host, but if we do have a host, it must match
            assert(author.host is None or host is None or author.host == host)
            author.display_name = self.validated_data['display_name']
            author.profile_image = self.validated_data['profile_image']
            author.github = self.validated_data['github']
            author.external_url = self.validated_data['external_url']
            author.save()

        return author

    class Meta:
        model = Author
        fields = ['external_url', 'display_name', 'profile_image', 'github']

class PostDeserializer(serializers.ModelSerializer):
    external_url = serializers.URLField()
    title = serializers.CharField()
    source = serializers.URLField()
    origin = serializers.URLField()
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
            data = None
            # if content type is image, then we need to turn content base64 into an image
            if self.validated_data['content_type'] == Post.PostType.PNG or self.validated_data['content_type'] == Post.PostType.JPG:
                data = base64.b64decode(self.validated_data['content'])
                self.validated_data['content'] = "Image post"


            post = Post.objects.create(**self.validated_data, author=author)

            if data is not None:

                if post.content_type == Post.PostType.PNG:
                    ext = 'png'
                # elif post.content_type == Post.PostType.JPG:
                else:
                    ext = '.jpg'
                # use random uuid as filename
                filename = uuid.uuid4().__str__() + '.' + ext
                data = ContentFile(data, name=filename)

                image = ImageFile.objects.create(post=post, image=data)
                image.save()

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

            if post.content_type == Post.PostType.PNG or post.content_type == Post.PostType.JPG:

                if post.content_type == Post.PostType.PNG:
                    ext = 'png'
                # elif post.content_type == Post.PostType.JPG:
                else:
                    ext = '.jpg'

                data = base64.b64decode(self.validated_data['content'])
                filename = uuid.uuid4().__str__() + '.' + ext
                data = ContentFile(data, name=filename)

                image = ImageFile.objects.filter(post=post).first()
                if image is None:
                    image = ImageFile.objects.create(post=post, image=data)
                    image.save()
                else:
                    image.image = data
                    image.save()
            else:
                post.content = self.validated_data['content']
                image = ImageFile.objects.filter(post=post).first()
                if image is not None:
                    image.delete()

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

        comment = Comment.objects.filter(external_url=self.validated_data['external_url']).first()
        if comment is None:
            comment = Comment.objects.create(**self.validated_data, post=post, author=author)
        else:
            assert(comment.post == post)
            assert (comment.author == author)
            comment.comment = self.validated_data['comment']
            comment.published = self.validated_data['published']
            comment.contentType = self.validated_data['contentType']
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

class Deserializers:
    author = AuthorDeserializer
    post = PostDeserializer
    comment = CommentDeserializer
    post_like = PostLikeDeserializer
    comment_like = CommentLikeDeserializer
    follower = FollowerDeserializer


class InboxSerializers:
    post = PostActivitySerializer
    comment = CommentActivitySerializer
    post_like = LikeActivitySerializer
    comment_like = CommentLikeActivitySerializer
    follower = FollowActivitySerializer