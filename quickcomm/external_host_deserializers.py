

# This file deals with desearializing data from other servers. All of the
# requests will have their data "cached" in our database, so we can just
# access that data instead of making a request to the other server. The calls
# to other servers can then be made independently of our internal calls.

# TODO make sure that our API only return local hosts
# TODO what do we do when we see authors that aren't on any of our servers or a host we know about?
# TODO handle case where looking at an author's liked items returns a post or comment that doesn't exist on our server
# in that case, we don't want to represent the post or comment on our end



from rest_framework import serializers
from quickcomm.external_host_requests import THTHQCRequest
from quickcomm.models import Author, Comment, CommentLike, Follow, ImageFile, Like, Post
import base64

# TODO use forms from creating items to validate data? that way we don't have duplicate information

def sync_authors(self):
    """Syncs the authors with the remote API."""
    THTHQCRequest(self, Deserializers).update_authors()

def sync_posts(self):
    THTHQCRequest(self.host, Deserializers).update_posts(
        self
    )

def sync_comments(self):
    THTHQCRequest(self.author.host, Deserializers).update_comments(
        self
    )

def sync_post_likes(self):
    THTHQCRequest(self.author.host, Deserializers).update_post_likes(
        self
    )

def sync_comment_likes(self):
    THTHQCRequest(self.author.host, Deserializers).update_comment_likes(
        self
    )

def sync_followers(self):
    THTHQCRequest(self.host, Deserializers).update_followers(
        self
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
                image = ImageFile(post=post, image=data)
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
                data = base64.b64decode(self.validated_data['content'])

                image = ImageFile.objects.filter(post=post).first()
                if image is None:
                    image = ImageFile(post=post, image=data)
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
    external_url = serializers.URLField()
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

    def save(self, author=None, following=None):
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

