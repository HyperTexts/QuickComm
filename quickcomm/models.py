import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator

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
    github = models.URLField(blank=True, null=True, validators=[URLValidator])
    profile_image = models.URLField(
        blank=True, null=True, validators=[URLValidator])

    # TODO determine if admins are authors
    is_admin = models.BooleanField(default=False)

    def follows(self, author):
        """Returns true if this author (self) follows the given author."""
        return Follow.objects.filter(follower=self, following=author).exists()

    def following(self, author):
        """Returns true if this author (self) is followed by the given author."""
        return Follow.objects.filter(follower=author, following=self).exists()

    def is_bidirectional(self, author):
        """Returns true if this author (self) follows and is followed by the
        given author. In other words, a true friend."""
        return self.follows(author) and self.following(author)

    def __str__(self):
        return f"{self.display_name} ({self.user.username})"


class Follow(models.Model):
    """A follow is is a many-to-many relationship between authors representing a
    follow."""

    follower = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name='follower')
    following = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name='following')

    def is_bidirectional(self):
        """Returns true if the follow is bidirectional."""
        return self.following.follows(self.follower)

    def __str__(self):
        return f"{self.follower.__str__()} follows {self.following.__str__()}"


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


class Inbox(models.Model):
    """The inbox is a relationship between an author and a post."""

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.author.__str__()}'s inbox contains {self.post.__str__()}"


class Like(models.Model):
    """A like is a relationship between an author and a post."""

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.author.__str__()} likes {self.post.__str__()}"


class RegistrationSettings(models.Model):
    """A flag for admin users to determine if new users are active or not by default.
    Should only have 1 value in database"""
    are_new_users_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.are_new_users_active.__str__()}"
