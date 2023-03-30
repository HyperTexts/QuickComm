from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate, APIClient

from django.contrib.auth.models import User
from quickcomm.models import FollowRequest,Author

class Request(TestCase):
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
    def test_get_request(self):
        """Test that the inbox is empty for all users to begin."""
        items = FollowRequest.objects.all()
        self.assertEqual(len(items), 0)
    def test_create_request(self):
        first_request=FollowRequest.objects.create(from_user=self.author1,to_user=self.author2)
        items=FollowRequest.objects.all()
        self.assertEqual(len(items),1)
        self.assertTrue(items[0].from_user,self.author1)
        self.assertTrue(items[0].to_user,self.author2)