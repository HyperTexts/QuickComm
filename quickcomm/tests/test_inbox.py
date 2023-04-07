

from django.test import TestCase
from django.contrib.auth.models import User

from quickcomm.models import Author, Comment, Inbox, Post, FollowRequest, Follow, Like, CommentLike


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
        self.author1 = Author.objects.create(user=self.user1,
                                             display_name='My Real Cool Name',
                                             github='abramhindle',
                                             profile_image='https://url.com',
                                             external_url=None)
        self.author1.save()

        self.author2 = Author.objects.create(user=self.user2,
                                             display_name='My Real Cool Name 2',
                                             github='abramhindle',
                                             profile_image='https://url.com',
                                             external_url=None)
        self.author2.save()

        self.author3 = Author.objects.create(user=self.user3,
                                             display_name='My Real Cool Name 3',
                                             github='abramhindle',
                                             profile_image='https://url.com')
        self.author3.save()

    def test_get_inbox(self):
        """Test that the inbox is empty for all users to begin."""
        items = Inbox.objects.all()
        self.assertEqual(len(items), 0)

    def test_follow(self):
        """Test that following a user adds an item to the inbox of the followed user."""
        follow_req = FollowRequest.objects.create(from_user=self.author1, to_user=self.author2)
        follow_req.save()

        follow = Follow.objects.create(follower=follow_req.from_user, following=follow_req.to_user)
        follow.save()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].inbox_type, items[0].InboxType.FOLLOW)
        self.assertEqual(items[0].content_object.to_user, self.author2)
        self.assertEqual(items[0].content_object.from_user, self.author1)
        self.assertEqual(items[0].author, self.author2)

    def test_creating_new_post(self):
        """Test that a new post adds an item to the inboxes of all followers, including itself."""

        follow_req = FollowRequest.objects.create(from_user=self.author1,
                                                  to_user=self.author2)
        follow_req.save()

        follow = Follow.objects.create(follower=follow_req.from_user,
                                       following=follow_req.to_user)
        follow.save()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 1)

        post = Post.objects.create(author=self.author2,
                                   title='My Post',
                                   source='http://someurl.ca',
                                   origin='http://someotherurl.ca',
                                   description='My Post Description',
                                   content_type='text/plain',
                                   content='My Post Content',
                                   visibility='PUBLIC',
                                   unlisted=False,
                                   categories='["test"]')
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

        follow_req = FollowRequest.objects.create(from_user=self.author1,
                                                  to_user=self.author2)
        follow_req.save()

        follow = Follow.objects.create(follower=follow_req.from_user,
                                       following=follow_req.to_user)
        follow.save()

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

    def test_unlisted_post2(self):
        """Test that even being a friend with the author cant get unlisted post in their inbox"""

        follow_req = FollowRequest.objects.create(from_user=self.author1,
                                                  to_user=self.author3)
        follow_req.save()

        follow = Follow.objects.create(follower=follow_req.from_user,
                                       following=follow_req.to_user)
        follow.save()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 1)

        post = Post.objects.create(author=self.author1, title='My Post', source='http://someurl.ca', origin='http://someotherurl.ca', description='My Post Description', content_type='text/plain', content='My Post Content', visibility='FRIEND', unlisted=False, categories='["test"]')
        post.full_clean()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 2)

    def test_liking_comment(self):
        """Test that liking a comment adds an item to the inbox of the author of the post."""

        follow_req = FollowRequest.objects.create(from_user=self.author1,
                                                  to_user=self.author2)
        follow_req.save()

        follow = Follow.objects.create(follower=follow_req.from_user,
                                       following=follow_req.to_user)
        follow.save()

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

        comment_like = CommentLike.objects.create(comment=comment, author=self.author2)
        comment_like.full_clean()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 5)

        self.assertEqual(items[4].inbox_type, items[4].InboxType.COMMENTLIKE)
        self.assertEqual(items[4].content_object, comment_like)
        self.assertEqual(items[4].author, self.author2)

    def test_liking_post(self):
        """Test that liking a post adds an item to the inbox of the author of the post."""

        follow_req = FollowRequest.objects.create(from_user=self.author1,
                                                  to_user=self.author2)
        follow_req.save()

        follow = Follow.objects.create(follower=follow_req.from_user,
                                       following=follow_req.to_user)
        follow.save()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 1)

        post = Post.objects.create(author=self.author2, title='My Post', source='http://someurl.ca', origin='http://someotherurl.ca', description='My Post Description', content_type='text/plain', content='My Post Content', visibility='PUBLIC', unlisted=False, categories='["test"]')
        post.full_clean()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 3)

        like = Like.objects.create(author=self.author1, post=post)
        like.full_clean()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 4)

        self.assertEqual(items[3].inbox_type, items[3].InboxType.LIKE)
        self.assertEqual(items[3].content_object, like)
        self.assertEqual(items[3].author, self.author2)

    def test_unlisted_post(self):
        """Test that creating an unlisted post doesnt add an item to the inbox of anyone"""
        items = Inbox.objects.all()
        self.assertEqual(len(items), 0)

        posts = Post.objects.all()
        self.assertEqual(len(posts),0)

        post = Post.objects.create(author=self.author2,
                                   title='My Post',
                                   source='http://someurl.ca',
                                   origin='http://someotherurl.ca',
                                   description='My Post Description',
                                   content_type='text/plain',
                                   content='My Post Content',
                                   visibility='PUBLIC',
                                   unlisted=True,
                                   categories='["test"]')
        post.full_clean()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 0)

        posts = Post.objects.all()
        self.assertEqual(len(posts),1)


    def test_friend_post(self):
        """Test that creating a friend post only adds an item to the inbox of the author of the post and their friends."""

        follow_req = FollowRequest.objects.create(from_user=self.author1,
                                                  to_user=self.author2)
        follow_req.save()

        follow = Follow.objects.create(follower=follow_req.from_user,
                                       following=follow_req.to_user)
        follow.save()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 1)

        post = Post.objects.create(author=self.author2,
                                   title='My Post',
                                   source='http://someurl.ca',
                                   origin='http://someotherurl.ca',
                                   description='My Post Description',
                                   content_type='text/plain',
                                   content='My Post Content',
                                   visibility='FRIENDS',
                                   unlisted=False,
                                   categories='["test"]')
        post.full_clean()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 2)
        self.assertEqual(items[1].inbox_type, items[1].InboxType.POST)
        self.assertEqual(items[1].content_object, post)
        self.assertEqual(items[1].author, self.author2)

        # now make the two authors true friends
        follow_req = FollowRequest.objects.create(from_user=self.author2,
                                                  to_user=self.author1)
        follow_req.save()

        follow = Follow.objects.create(follower=follow_req.from_user,
                                       following=follow_req.to_user)
        follow.save()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 3)

        # make a new friends post
        post2 = Post.objects.create(author=self.author2,
                                   title='My Second Post',
                                   source='http://someurl.ca',
                                   origin='http://someotherurl.ca',
                                   description='My Post Description',
                                   content_type='text/plain',
                                   content='My Second Post Content',
                                   visibility='FRIENDS',
                                   unlisted=False,
                                   categories='["test"]')
        post2.full_clean()

        items = Inbox.objects.all()
        self.assertEqual(len(items), 5)
        self.assertEqual(items[3].inbox_type, items[3].InboxType.POST)
        self.assertEqual(items[4].inbox_type, items[4].InboxType.POST)

        self.assertEqual(items[3].content_object, post2)
        self.assertEqual(items[4].content_object, post2)

        self.assertEqual(items[3].author, self.author1)
        self.assertEqual(items[4].author, self.author2)

