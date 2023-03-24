

from django.test import TestCase
from django.contrib.auth.models import User

from quickcomm.models import Author, Comment, Inbox, Post


class InternalInboxTests(TestCase):
    """This set of tests checks if the inbox works correcly when non-foreign
    users perform tasks."""

    def setUp(self):

        # create sample users
        self.user1 = User.objects.create_user(username='user1', password='badpassword')
        self.user1.save()
        self.user2 = User.objects.create_user(username='user2', password='badpassword')
        self.user2.save()
        self.user3 = User.objects.create_user(username='user3', password='badpassword')

        # create sample authors
        self.author1 = Author.objects.create(user=self.user1, host='http://127.0.0.1:8000', display_name='My Real Cool Name', github='abramhindle', profile_image='https://url.com')
        self.author1.save()
        self.author2 = Author.objects.create(user=self.user2, host='http://127.0.0.1:8000', display_name='My Real Cool Name 2', github='abramhindle', profile_image='https://url.com')
        self.author2.save()
        self.author3 = Author.objects.create(user=self.user3, host='http://127.0.0.1:8000', display_name='My Real Cool Name 3', github='abramhindle', profile_image='https://url.com')
        self.author3.save()

    def test_get_inbox(self):
        """Test that the inbox is empty for all users to begin."""
        items = Inbox.objects.all()
        self.assertEqual(len(items), 0)

    def test_follow(self):
        """Test that following a user adds an item to the inbox of the followed user."""
        self.author1.follow(self.author2)
        items = Inbox.objects.all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].inbox_type, items[0].InboxType.FOLLOW)
        self.assertEqual(items[0].content_object.following, self.author2)
        self.assertEqual(items[0].content_object.follower, self.author1)
        self.assertEqual(items[0].author, self.author2)

    def test_creating_new_post(self):
        """Test that a new post adds an item to the inboxes of all followers, including itself."""

        self.author1.follow(self.author2).full_clean()
        items = Inbox.objects.all()

        self.assertEqual(len(items), 1)

        post = Post.objects.create(author=self.author2, title='My Post', source='http://someurl.ca', origin='http://someotherurl.ca', description='My Post Description', content_type='text/plain', content='My Post Content', visibility='PUBLIC', unlisted=False, categories='["test"]')
        post.full_clean()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].inbox_type, items[0].InboxType.FOLLOW)
        self.assertEqual(items[1].inbox_type, items[1].InboxType.POST)
        self.assertEqual(items[2].inbox_type, items[2].InboxType.POST)

        self.assertEqual(items[1].content_object, post)
        self.assertEqual(items[2].content_object, post)

        self.assertEqual(items[1].author, self.author1)
        self.assertEqual(items[2].author, self.author2)

    def test_commenting_on_post(self):
        """Test that commenting on a post adds an item to the inbox of the author of the post."""

        self.author1.follow(self.author2).full_clean()
        items = Inbox.objects.all()

        self.assertEqual(len(items), 1)

        post = Post.objects.create(author=self.author2, title='My Post', source='http://someurl.ca', origin='http://someotherurl.ca', description='My Post Description', content_type='text/plain', content='My Post Content', visibility='PUBLIC', unlisted=False, categories='["test"]')
        post.full_clean()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 3)

        comment = Comment.objects.create(author=self.author1,   content_type='text/plain', comment='My Comment Content', post=post)
        comment.full_clean()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 4)

        self.assertEqual(items[3].inbox_type, items[3].InboxType.COMMENT)
        self.assertEqual(items[3].content_object, comment)
        self.assertEqual(items[3].author, self.author2)

