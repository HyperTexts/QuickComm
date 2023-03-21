import base64
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# NOTE: The models in this file do not take into account how the site will
# interact with other APIs. Ideally, we should be able to reuse the model
# classes, but this logic is to be implemented later.

# Type fields are left out as they can be added later and are redundant. Host
# fields are kept as if these classes are used to represent remote authors,
# the host field is necessary. ID is also left out.

# We used UUIDs for pkeys to be more secure.
# TODO what are the constraints on fields being null?


class Author(models.Model):
    """An author is a person associated with a user account via a one-to-one
    relationship."""

    # Example code for a one-to-one relationship taken from
    # https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
    # Author: Vitor Freitas
    # Site: Simple is Better Than Complex
    # Taken on: Feb 6, 2023

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    host = models.URLField(validators=[URLValidator])
    display_name = models.CharField(max_length=100)
    github = models.CharField(max_length=50, blank=True, null=True)
    profile_image = models.URLField(blank=True, null=True, validators=[URLValidator])

    # TODO determine if admins are authors
    is_admin = models.BooleanField(default=False)

    def is_following(self, author):
        """Returns true if this author (self) follows the given author."""
        return Follow.objects.filter(follower=self, following=author).exists()

    def is_followed_by(self, author):
        """Returns true if this author (self) is followed by the given author."""
        return Follow.objects.filter(follower=author, following=self).exists()
    
    def follower_count(self):
        """return number of profiles following author (self)"""
        return Follow.objects.filter(following=self).count()
    
    def get_followers(self):
        return Follow.objects.filter(following=self)
    
    def get_requests(self):
        return follow_request.objects.filter(to_user=self)
    def requests_count(self):
        return follow_request.objects.filter(to_user=self).count()
    

    def is_bidirectional(self, author):
        """Returns true if this author (self) follows and is followed by the
        given author. In other words, a true friend."""
        return self.is_following(author) and self.is_followed_by(author)

    def follow(self, author):
        """Follows the given author."""
        return Follow.objects.create(follower=self, following=author)


    def __str__(self):
        return f"{self.display_name} ({self.user.username})"


class Follow(models.Model):
    """A follow is is a many-to-many relationship between authors representing a
    follow."""

    follower = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name='follower')
    following = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name='following')

    def save(self, *args, **kwargs):
        saved = super(Follow, self).save(*args, **kwargs)
        # When we save a follow, we also need to create an inbox post for the
        # author being followed.

        if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id).exists():
            Inbox.objects.create(content_object=self, author=self.following, inbox_type=Inbox.InboxType.FOLLOW)

        return saved


    def is_bidirectional(self):
        """Returns true if the follow is bidirectional."""
        return self.following.is_following(self.follower)

    def __str__(self):
        return f"{self.follower.__str__()} follows {self.following.__str__()}"
class follow_request(models.Model):
    """A request is a prompt for a user to accept a follower"""
    from_user=models.ForeignKey(Author, on_delete=models.CASCADE,related_name='from_user')
    to_user=models.ForeignKey(Author,on_delete=models.CASCADE,related_name='to_user')


class Post(models.Model):
    """A post is a post made by an author."""

    class PostType(models.TextChoices):
        TEXT = 'text/plain'
        MD = 'text/markdown'
        PNG = 'image/png;base64'
        JPG = 'image/jpeg;base64'
        APP = 'application/base64'

    class PostVisibility(models.TextChoices):
        PUBLIC = 'PUBLIC'
        FRIENDS = 'FRIENDS'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    source = models.URLField(blank=True, null=True, validators=[URLValidator])
    origin = models.URLField(blank=True, null=True, validators=[URLValidator])
    description = models.CharField(max_length=1000)
    content_type = models.CharField(max_length=50, choices=PostType.choices)
    content = models.CharField(max_length=10000)
    # FIXME categories has to be a list of strings of some sort
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    categories = models.CharField(max_length=1000)
    published = models.DateTimeField(auto_now_add=True)
    visibility = models.CharField(
        max_length=50, choices=PostVisibility.choices)
    unlisted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        saved = super(Post, self).save(*args, **kwargs)
        # When we save a post, we also need to create an inbox post for each
        # follower of the author.

        followers = Follow.objects.filter(following=self.author)

        for follower in followers:
            if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id, author=follower.following).exists():
                Inbox.objects.create(content_object=self, author=follower.follower, inbox_type=Inbox.InboxType.POST)


        # We also include the author as a follower of themselves to simplify
        # the inbox logic.
        if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id, author=self.author).exists():
            Inbox.objects.create(content_object=self, author=self.author, inbox_type=Inbox.InboxType.POST)

        return saved

    @property
    def content_formatted(self):
        """Returns the content of the post as either base64 or plain text."""
        if self.content_type == self.PostType.PNG or self.content_type == self.PostType.JPG:
            file = ImageFile.objects.get(post=self).image.read()
            return base64.b64encode(file).decode('utf-8')
        return self.content

    @content_formatted.setter
    def content_formatted(self, value):
        """Sets the content of the post from either base64 or plain text."""
        if self.content_type == self.PostType.PNG or self.content_type == self.PostType.JPG:
            ImageFile.objects.get(post=self).delete()
            ImageFile.objects.create(post=self, image=base64.b64decode(value)).save()
        else:
            self.content = value

    def get_image_url(self, request):
        """Returns the absolute URL of the image associated with the post."""
        return request.build_absolute_uri("/api/authors/"+self.author_id.__str__()+"/posts/"+self.id.__str__()+"/image/")
    def __str__(self):
        return f"{self.title} by {self.author.__str__()}"


class Comment(models.Model):
    """A comment is a comment made by an author on a post."""

    class CommentType(models.TextChoices):
        TEXT = 'text/plain'
        MD = 'text/markdown'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    comment = models.CharField(max_length=1000)
    content_type = models.CharField(max_length=50, choices=CommentType.choices)
    published = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        saved = super(Comment, self).save(*args, **kwargs)
        # When we save a comment, we also need to create an inbox post for the
        # author of the post.

        Inbox.objects.create(content_object=self, author=self.post.author, inbox_type=Inbox.InboxType.COMMENT)

        return saved

    def __str__(self):
        return f"{self.author.__str__()} commented on {self.post.__str__()}"

class ImageFile(models.Model):
    """An image file is a file that is an image. This is used so our internal
    representation is a file and not a base64 string."""
    post = models.OneToOneField(Post, on_delete=models.CASCADE, primary_key=True)
    image = models.ImageField(upload_to='images/')


class Inbox(models.Model):
    """The inbox is a relationship between an author and either a like, comment,
    post, or friend request.

    This is the way our inbox works: every time an item is added to the inbox,
    it must be associated with an object of the appropriate type. If that item
    does not exist (like in the case of a foreign author), we create it and
    and associate it wth the inbox post, so we can have an internal representation
    of the item. If the item does exist, we just associate it with the inbox
    post.
    """

    # TODO the exact behaviour of this is pending on an eClass form post. For
    # now, we will assume that the inbox only works internally and creates a
    # copy every time.

    # To add an item to the inbox, we do the following:
    #
    # Inbox.objects.create(
    #     inbox_type=InboxType.POST,
    #     author=some_author,
    #     content_object=some_post,
    # )
    @property
    def format(self): return "inbox"

    class InboxType(models.TextChoices):
        POST = 'post'
        COMMENT = 'comment'
        FOLLOW = 'follow'
        LIKE = 'like'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # The author is the author who owns the inbox.
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    
    # The inbox type is the type of item in the inbox.
    inbox_type = models.CharField(max_length=50, choices=InboxType.choices)

    # The date the item was added to the inbox.
    added = models.DateTimeField(auto_now_add=True)

    # We use a generic foreign key to associate the inbox with the appropriate
    # object. This is a bit of a hack, but it works.

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"{self.author.__str__()}'s inbox contains {self.content_object.__str__()}"


class Like(models.Model):
    """A like is a relationship between an author and a post."""

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        saved = super(Like, self).save(*args, **kwargs)
        # When we save a like, we also need to create an inbox post for the
        # author of the post.

        Inbox.objects.create(content_object=self, author=self.post.author, inbox_type=Inbox.InboxType.LIKE)

        return saved

    def __str__(self):
        return f"{self.author.__str__()} likes {self.post.__str__()}"

class RegistrationSettings(models.Model):
    """A flag for admin users to determine if new users are active or not by default.
    Should only have 1 value in database"""
    are_new_users_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.are_new_users_active.__str__()}"
