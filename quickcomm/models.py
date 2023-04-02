import base64
import os
import uuid
from django.db import models
from django.core.validators import URLValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q

from quickcomm.signals import export_http_request_on_inbox_save

def try_all_external_urls(url, object):
    """This method trys to get all objects with the given url with any combination
    of insecure http/trailing slashes."""

    # generate a list of the urls to try
    urls = [url]
    if url[-1] == '/':
        urls.append(url[:-1])
    else:
        urls.append(url + '/')

    for url_new in urls.copy():
        if url_new[:5] == 'https':
            urls.append(url_new.replace('https', 'http'))
        else:
            urls.append(url_new.replace('http', 'https'))

    # try to get the object with each url
    for url_new in urls:
        try:
            return object.objects.filter(external_url=url_new).first()
        except:
            pass

    return None


# TODO we have to delete external objects when they don't show up in the big list. However, we have to be careful not to delete posts if they are private

# NOTE: The models in this file do not take into account how the site will
# interact with other APIs. Ideally, we should be able to reuse the model
# classes, but this logic is to be implemented later.

# Type fields are left out as they can be added later and are redundant. Host
# fields are kept as if these classes are used to represent remote authors,
# the host field is necessary. ID is also left out.

# We used UUIDs for pkeys to be more secure.
# TODO what are the constraints on fields being null?
# TODO make all char sizes huge
class HostAuthenticator(models.Model):
    """A host authenticator is a username and password that can be used to
    authenticate to a host."""

    # Note: passwords are stored in plain-text. They are API keys, so they are
    # not sensitive. If we want to store them in a more secure way, we can
    # hash them, but for now, we will leave them as is.

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    username = models.CharField(max_length=100, help_text="The username to use to authenticate to the host.", verbose_name="Username")
    password = models.CharField(max_length=100, help_text="The password to use to authenticate to the host.", verbose_name="Password")
    nickname = models.CharField(max_length=100, help_text="The nickname of the host authenticator. This is only used for display purposes.", verbose_name="Nickname", null=True, blank=True)


    @property
    def nickname_or_username(self):
        if self.nickname:
            return self.nickname
        return self.username

    @property
    def base64string(self):
        return base64.b64encode(f"{self.username}:{self.password}".encode('ascii')).decode('ascii')

    def check_password(self, password):
        return self.password == password

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return f"{self.username}"

class Host(models.Model):
    """A host is a remote server that hosts authors."""

    class SerializerClass(models.TextChoices):
        """The serializer class to use for the host. This is used to determine
        which serializer to use when interacting with the host.

        Each serializer class is a subset of BaseQCRequest. The serializer
        classes house the information on:
        - how to deserialize the remote host's API
        - how to deserialize the remote host's requests to our inbox
        - how to serialize the local host's requests to their inbox
        """

        THTH = "THTH", "Too Hot To Hindle (Group 2)"
        INTERNAL = "INTERNAL", "Internal Default"
        GROUP1 = "GROUP1", "Group 1"


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    url = models.URLField(validators=[URLValidator], help_text="The URL of the host API. This must be in proper form (e.g. https://example.com/).", verbose_name="Host URL")
    serializer_class = models.CharField(max_length=100, choices=SerializerClass.choices, default=SerializerClass.INTERNAL, help_text="The serializer class to use for the host. This is used to determine which serializer to use when interacting with the host.", verbose_name="Serializer Class")

    username_password_base64 = models.CharField(max_length=100, help_text="The username and password to use to authenticate to the host. This is a base64 encoded string of the form 'username:password'.", verbose_name="Username and Password", null=True, blank=True)

    last_successful_ping = models.DateTimeField(null=True, blank=True)
    last_ping = models.DateTimeField(null=True, blank=True)
    last_ping_result = models.BooleanField(null=True, blank=True)

    nickname = models.CharField(max_length=100, help_text="The nickname of the host. This is only used for display purposes.", verbose_name="Nickname", null=True, blank=True)

    @property
    def nickname_or_url(self):
        if self.nickname:
            return self.nickname
        return self.url

        # TODO delete authors that are no longer on the remote host
        # TODO don't delete posts that were private by accident


    def ping(self):
        """Pings the host to see if it is online. Return True if online, False
        otherwise. This method uses the os.system() method to ping the host."""

        # FIXME ping is not the best way to check if a host is online. We
        # should use a more reliable method.

        # strip the protocol from the url
        clean_url = self.url.split('/')[2]

        # strip the port from the url
        clean_url = clean_url.split(':')[0]

        # ping the host
        req = os.system(f"ping -c 1 {clean_url}")
        success = req == 0

        # last ping is now, set the last ping result
        self.last_ping = timezone.now()
        self.last_ping_result = success
        if success:
            self.last_successful_ping = self.last_ping

        return success

    # TODO move to the receiver mixins
    def save(self, *args, **kwargs):
        """Override save to ping the host before saving."""
        # self.ping()
        super(Host, self).save(*args, **kwargs)

    def __str__(self):
        if self.nickname:
            return f"{self.nickname} ({self.url})"
        return f"{self.url}"

class Author(models.Model):
    """An author is a person associated with a user account via a one-to-one
    relationship."""

    # Example code for a one-to-one relationship taken from
    # https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
    # Author: Vitor Freitas
    # Site: Simple is Better Than Complex
    # Taken on: Feb 6, 2023

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, help_text="The user associated with this author. This is only used for internal authors. Remote authors will have this field set to null. This field should NOT be set manually.", verbose_name="User")
    # FIXME the user is only null if the author is remote. This should be
    # enforced in the model.
    host = models.ForeignKey(Host, on_delete=models.CASCADE, null=True, blank=True,help_text="The host that this author is associated with. This is only used for remote authors. Internal authors will have this field set to null. This field should NOT be set manually.")
    external_url = models.CharField(max_length=100, blank=True, null=True, help_text="The external URL of the author. This is only used for remote authors. Internal authors will have this field set to null. This field should NOT be set manually.", verbose_name="External URL")
    display_name = models.CharField(max_length=100)
    github = models.URLField(blank=True, null=True, validators=[URLValidator], help_text="The URL of the author's GitHub profile. This must be in proper form (e.g. https://github.com/abramhindle).", verbose_name="GitHub URL")
    profile_image = models.URLField(
        blank=True, null=True, validators=[URLValidator], help_text="The URL of the author's profile image. This must be in proper form (e.g. https://example.com/image.png).", verbose_name="Profile Image URL")

    # TODO determine if admins are authors
    is_admin = models.BooleanField(default=False)


    # TODO always use trailing slash


    @staticmethod
    def get_from_url(url):
        """Returns the author with the given URL."""

        # try to get the author from the database
        author = try_all_external_urls(url, Author)
        if author is not None:
            return author

        try:

            author_id = url.split('/')
            if author_id[-1] == '':
                author_id = author_id[-2]
            else:
                author_id = author_id[-1]
            author = Author.objects.filter(id=author_id).first()
            if author is None:
                return None
        except:
            return None

        if author.host is None:
            return author

        return None


    # This section defines the types of authors that can exist on our server.
    # Since we have to "cache" all author objects to get them to display in
    # the frontend, we will have 3 types of authors:
    #
    # 1. local authors on our own server
    # 2. remote authors on connected servers
    # 3. temporary authors that are on a server that is not connected
    #
    # An example of where a temporary author is used is when looking at the
    # comments of a remote post. To display the comment, we will create a new
    # author object with the information from the comment. This author object
    # will be temporary and for the time being be saved to the database. We can
    # then decide to remove it later if we want to.
    #
    # We will only update these authors based on the information from the remote
    # we are connected to. We will never connect to the temporary server as we
    # do not have access to it.
    #
    # An edge case is when the server that we are connected to has a new user
    # we do not know about. In this case, we will create a temporary author
    # object. When we visit an author page that is temporary, we will run a full
    # scan of all host authors. If then it does not show up, we will display a
    # message saying that the author information is not available.

    @property
    def is_local(self):
        """Returns true if the author is local."""
        return self.external_url is None

    @property
    def is_remote(self):
        """Returns true if the author is remote."""
        return self.external_url is not None

    @property
    def is_temporary(self):
        """Returns true if the author is temporary."""
        return self.host is None

    @property
    def location(self):
        """Returns External or Internal"""
        if self.is_local:
            return "Internal"
        elif self.is_temporary:
            return "External (temporary)"
        return "External"

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
    
    def get_following(self):
        return Follow.objects.filter(follower=self)
    
    def following_count(self):
        return Follow.objects.filter(follower=self).count()

    def posts_count(self):
        return Post.objects.filter(author=self).count()

    def get_requests(self):
        requests =  FollowRequest.objects.filter(to_user=self)
        followers = self.get_followers().values('follower')
        return requests.exclude(from_user__in=followers)
    def requests_count(self):
        """return number of follow requests for author (self) that do not exist in the follow table"""
        return self.get_requests().count()


    def is_bidirectional(self, author):
        """Returns true if this author (self) follows and is followed by the
        given author. In other words, a true friend."""
        return (self.is_following(author) and self.is_followed_by(author)) or self == author

    def follow(self, author):
        """Follows the given author."""
        return Follow.objects.create(follower=self, following=author)

    @property
    def followers(self):
        """Returns a queryset of all followers of this author."""
        return Author.objects.filter(following=self)

    @staticmethod
    def safe_queryset():
        """Returns a safe queryset of authors that excludes all foreign authors"""
        return Author.objects.filter(host=None, external_url=None)

    @staticmethod
    def frontend_queryset():
        """Returns a queryset of authors that excludes all temporary authors"""
        return Author.objects.exclude(Q(host=None), ~Q(external_url=None))

    def __str__(self):
        return f"{self.display_name}"

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


        # If both the follower and following are remote, we do not need to
        # create an inbox post.
        # if self.follower.is_remote and self.following.is_remote:
        #     return saved

        # if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id).exists():
        #     Inbox.objects.create(content_object=self, author=self.following, inbox_type=Inbox.InboxType.FOLLOW)
        return saved

    def delete(self, *args, **kwargs):
        if Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id).exists():
            Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id).delete()
        deleted=super(Follow,self).delete(*args,**kwargs)
        return deleted

    def delete(self, *args, **kwargs):
        # cascade delete inbox items
        print("deleting follow")
        Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id).delete()
        super(Follow, self).delete(*args, **kwargs)

    

    def is_bidirectional(self):
        """Returns true if the follow is bidirectional."""
        return self.following.is_following(self.follower)

    @property
    def context(self):
        return 'https://www.w3.org/ns/activitystreams'

    def __str__(self):
        return f"{self.follower.__str__()} follows {self.following.__str__()}"
    
class FollowRequest(models.Model):
    """A request is a prompt for a user to accept a follower"""
    from_user=models.ForeignKey(Author, on_delete=models.CASCADE,related_name='from_user')
    to_user=models.ForeignKey(Author,on_delete=models.CASCADE,related_name='to_user')

    @property
    def context(self):
        return 'https://www.w3.org/ns/activitystreams'

    def save(self, *args, **kwargs):
        saved = super(FollowRequest, self).save(*args, **kwargs)
        # When we save a follow, we also need to create an inbox post for the
        # author being followed.

        if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id).exists():
            Inbox.objects.create(content_object=self, author=self.to_user, inbox_type=Inbox.InboxType.FOLLOW)

        return saved

    def __str__(self):
        return f"{self.from_user.__str__()} requests to follow {self.to_user.__str__()}"

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
    content = models.CharField(max_length=1000000000)
    # FIXME categories has to be a list of strings of some sort
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    categories = models.CharField(max_length=1000)
    published = models.DateTimeField(auto_now_add=True)
    visibility = models.CharField(
        max_length=50)
    unlisted = models.BooleanField(default=False)
    external_url = models.URLField(blank=True, null=True, validators=[URLValidator])
    likes = models.ManyToManyField(User, related_name='post_likes')
    recipient = models.UUIDField(editable=False, null=True)

    def save(self, *args, **kwargs):
        print('starting post save')
        saved = super(Post, self).save(*args, **kwargs)

        # FIXME move saving image logic here?

        # skip inbox logic for remote authors
        if self.author.is_remote:
            return saved

        # skip inbox if post is unlisted
        if self.unlisted:
            print('unlisted')
            return saved
        
        # if visibility is private, we only send to the inbox of the recipient and the author of the post
        elif self.visibility == 'PRIVATE':
            try:
                print('private')
                print(self.author.id, self.recipient)
                author = Author.objects.get(id=self.recipient)
                if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id, author=author).exists():
                    Inbox.objects.create(content_object=self, author=author, inbox_type=Inbox.InboxType.POST)

                # We also include the author as a follower of themselves to simplify
                # the inbox logic.
                if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id, author=self.author).exists():
                    Inbox.objects.create(content_object=self, author=self.author, inbox_type=Inbox.InboxType.POST)
            except:
                print(f'Failed to find author with id {self.recipient}')

            return saved
            
        else:
            print('public or follower')
            # When we save a post, we also need to create an inbox post for each
            # follower of the author.

            followers = Follow.objects.filter(following=self.author)

            for follower in followers:
                # If this is a friend post, only create the post for true friends
                if (self.visibility == 'FRIENDS' and follower.is_bidirectional()) or self.visibility == 'PUBLIC':
                    if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id, author=follower.follower).exists():
                        Inbox.objects.create(content_object=self, author=follower.follower, inbox_type=Inbox.InboxType.POST)

            # We also include the author as a follower of themselves to simplify
            # the inbox logic.
            if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id, author=self.author).exists():
                Inbox.objects.create(content_object=self, author=self.author, inbox_type=Inbox.InboxType.POST)

        return saved
    
    def update_info(self,post_info,post_id):
        post = Post.objects.filter(id=post_id, author=self.author)
        post.update(title=self.title,
        source=self.source,
        origin=self.origin,
        description=self.description,
        content_type=self.content_type,
        content=self.content,
        categories=self.categories,
        author=self.author,
        visibility=self.visibility,
        unlisted=self.unlisted)
        return post

    def delete(self, *args, **kwargs):
        # cascade delete inbox items
        Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id).delete()
        super(Post, self).delete(*args, **kwargs)


    def delete(self, *args, **kwargs):
        # cascade delete inbox items
        Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id).delete()
        super(Post, self).delete(*args, **kwargs)


    @property
    def content_formatted(self):
        """Returns the content of the post as either base64 or plain text."""
        return self.content

    @content_formatted.setter
    def content_formatted(self, value):
        """Sets the content of the post from either base64 or plain text."""
        self.content = value

    def get_image_url(self, request):
        """Returns the absolute URL of the image associated with the post."""
        return request.build_absolute_uri("/api/authors/"+self.author_id.__str__()+"/posts/"+self.id.__str__()+"/image/")
    def __str__(self):
        return f"{self.title} by {self.author.__str__()}"

    @property
    def comments(self):
        """Returns the comments for this post."""
        return Comment.objects.filter(post=self)

    @property
    def count(self):
        """Returns the number of comments for this post."""
        return self.comments.count()

    @property
    def likes(self):
        """Returns the likes for this post."""
        return Like.objects.filter(post=self)

    @property
    def context(self):
        """Returns the context for this post."""
        return 'https://www.w3.org/ns/activitystreams'

    # TODO use request here to get the url
    @staticmethod
    def get_from_url(url):
        """Returns the post with the given URL."""

        post = Post.objects.filter(external_url=url).first()
        if post is not None:
            return Post

        if url[-1] == '/':
            url = url[:-1]

            post = Post.objects.filter(external_url=url).first()
            if post is not None:
                return Post


        post_id= url.split('/')[-1]
        try:
            post = Post.objects.get(id=post_id)
        except:
            return None

        if post.author.host is None:
            return post

        return None


class Comment(models.Model):
    """A comment is a comment made by an author on a post."""

    class CommentType(models.TextChoices):
        TEXT = 'text/plain'
        MD = 'text/markdown'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    comment = models.CharField(max_length=1000)
    content_type = models.CharField(max_length=50, choices=CommentType.choices, default=CommentType.TEXT)
    published = models.DateTimeField(auto_now_add=True)
    external_url = models.URLField(blank=True, null=True, validators=[URLValidator])

    def save(self, *args, **kwargs):
        saved = super(Comment, self).save(*args, **kwargs)
        # When we save a comment, we also need to create an inbox post for the
        # author of the post.

        # skip inbox logic for remote authors
        if self.author.is_remote:
            return saved

        if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id, author=self.post.author).exists():
            Inbox.objects.create(content_object=self, author=self.post.author, inbox_type=Inbox.InboxType.COMMENT)

        return saved

    def delete(self, *args, **kwargs):
        # cascade delete inbox items
        Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id).delete()
        super(Comment, self).delete(*args, **kwargs)


    @staticmethod
    def get_from_url(url):
        """Returns the comment with the given URL."""

        comment = Comment.objects.filter(external_url=url).first()
        if comment is not None:
            return Comment

        if url[-1] == '/':
            url = url[:-1]

            comment = Comment.objects.filter(external_url=url).first()
            if comment is not None:
                return Comment


        comment_id = url.split('/')[-1]
        try:
            comment = Comment.objects.get(id=comment_id)
        except:
            return None

        if comment.post.author.host is None:
            return comment

        return None

    @property
    def context(self):
        """Returns the context for this post."""
        return 'https://www.w3.org/ns/activitystreams'

    def like_count(self):
        """Returns the number of likes for this comment."""
        return CommentLike.objects.filter(comment=self).count()

    def like_ids(self):
        """Returns the ids of authors who have liked this comment."""
        return [like.author.id for like in CommentLike.objects.filter(comment=self)]

    def __str__(self):
        return f"{self.author.__str__()} commented on {self.post.__str__()}"
    

class ImageFile(models.Model):
    """An image file is a file that is an image. This is used so our internal
    representation is a file and not a base64 string."""
    post = models.OneToOneField(Post, on_delete=models.CASCADE, primary_key=True)
    image = models.ImageField(upload_to='images/')

    def save(self, *args, **kwargs):
        res = super(ImageFile, self).save(*args, **kwargs)
        print('image should be saved')
        self.post.save()
        print('second post save should have started')
        return res

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
        COMMENTLIKE = 'commentlike'

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

    def save(self, *args, **kwargs):
        sel = super(Inbox, self).save(*args, **kwargs)
        # skip inbox logic if we are updating the inbox
        # if self.id:
        #     return sel

        # call remote method:
        export_http_request_on_inbox_save(self)

        return sel

    def __str__(self):
        return f"{self.author.__str__()}'s inbox contains {self.content_object.__str__()}"

class CommentLike(models.Model):
    """A comment like is a relationship between an author and a comment."""

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        saved = super(CommentLike, self).save(*args, **kwargs)
        # When we save a comment like, we also need to create an inbox post for the
        # author of the post.

        # skip inbox logic for remote authors
        #if self.author.is_remote:
         #   return saved

        Inbox.objects.create(content_object=self, author=self.comment.author, inbox_type=Inbox.InboxType.COMMENTLIKE)

        return saved


    @property
    def context(self):
        return "https://www.w3.org/ns/activitystreams"

    def __str__(self):
        return f"{self.author.__str__()} likes {self.comment.__str__()}"
    


class Like(models.Model):
    """A like is a relationship between an author and a post."""

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        saved = super(Like, self).save(*args, **kwargs)
        # When we save a like, we also need to create an inbox post for the
        # author of the post.

        # skip inbox logic for remote authors
        if self.author.is_remote:
            return saved

        if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id, author=self.post.author).exists():
            Inbox.objects.create(content_object=self, author=self.post.author, inbox_type=Inbox.InboxType.LIKE)

        return saved

    def delete(self, *args, **kwargs):
        # cascade delete inbox items
        Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id).delete()
        super(Like, self).delete(*args, **kwargs)

    @property
    def context(self):
        return "https://www.w3.org/ns/activitystreams"

    def __str__(self):
        return f"{self.author.__str__()} likes {self.post.__str__()}"

class CommentLike(models.Model):
    """A comment like is a relationship between an author and a comment."""

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        saved = super(CommentLike, self).save(*args, **kwargs)
        # When we save a comment like, we also need to create an inbox post for the
        # author of the post.

        # skip inbox logic for remote authors
        if self.author.is_remote:
            return saved

        if not Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id, author=self.comment.post.author).exists():
            Inbox.objects.create(content_object=self, author=self.comment.post.author, inbox_type=Inbox.InboxType.COMMENTLIKE)

        return saved

    def delete(self, *args, **kwargs):
        # cascade delete inbox items
        Inbox.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id).delete()
        super(CommentLike, self).delete(*args, **kwargs)

    @property
    def context(self):
        return "https://www.w3.org/ns/activitystreams"

    def __str__(self):
        return f"{self.author.__str__()} likes {self.comment.__str__()}"

class RegistrationSettings(models.Model):
    """A flag for admin users to determine if new users are active or not by default.
    Should only have 1 value in database"""
    are_new_users_active = models.BooleanField(default=True)
    allow_api_access_without_login = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.are_new_users_active.__str__()}"


class RawInboxItem(models.Model):
    """A raw inbox item is a straight JSON object that is either received from
    a remote author or sent to a remote author."""

    class RawInboxDirection(models.TextChoices):
        IN = 'in'
        OUT = 'out'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.URLField()
    direction = models.CharField(max_length=50, choices=RawInboxDirection.choices)
    data = models.JSONField()

    def __str__(self):
        return f"Raw inbox item {self.direction} {self.endpoint}"
