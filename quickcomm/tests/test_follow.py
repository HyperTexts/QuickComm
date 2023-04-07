

from django.test import TestCase
from django.contrib.auth.models import User

from quickcomm.models import Author, Comment, Inbox, Post, FollowRequest, Follow, Like, CommentLike


class FollowerTests(TestCase):
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

    def test_get_request(self):
        """Test that the requests is empty for all users to begin."""
        items = FollowRequest.objects.all()
        self.assertEqual(len(items), 0)

    def test_create_request(self):
        
        first_request=FollowRequest.objects.create(from_user=self.author1,to_user=self.author2)
        items=FollowRequest.objects.all()
        inbox=Inbox.objects.all()
        self.assertEqual(len(items),1)
        self.assertEqual(items[0],first_request)
        self.assertTrue(items[0].from_user,self.author1)
        self.assertTrue(items[0].to_user,self.author2)
        self.assertEqual(len(inbox),1)

    def test_bidirectional(self):
        request=FollowRequest.objects.filter(from_user=self.author1, to_user=self.author2)
        request.delete()
        self.assertEqual(len(FollowRequest.objects.all()),0)
        first_follow=Follow.objects.create(follower=self.author1,following=self.author2)
        second_follow=Follow.objects.create(follower=self.author2,following=self.author1)
        self.assertTrue(self.author1.is_bidirectional(self.author2))
        self.assertTrue(self.author2.is_bidirectional(self.author1))
