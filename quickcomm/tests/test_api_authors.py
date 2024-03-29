
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate, APIClient

from django.contrib.auth.models import User
from quickcomm.models import Author

class PublicAuthorsTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()

        # setup fake data
        self.user = User.objects.create_user(username='rajan', password='badpassword')
        self.user.save()
        self.author = Author.objects.create(user=self.user, display_name='My Real Cool Name', github='https://github.com/rajanmaghera', profile_image='https://url.com')
        self.author.save()


    def test_get_authors(self):
        """Test that we can get a list of authors"""
        with self.settings(SECURE_SSL_REDIRECT = False):
            self.client.force_login(user=self.user)
            req = self.client.get('/api/authors/')
            self.assertEqual(req.status_code, 200)
            self.assertEqual(req.data['type'], 'authors')
            self.assertNotEquals(req.data['type'], 'author')


    def test_non_allowed_methods(self):
        """Test that we cannot use non-allowed methods"""
        with self.settings(SECURE_SSL_REDIRECT = False):
            req = self.client.post('/api/authors/')
            self.assertEqual(req.status_code, 405)

            req = self.client.put('/api/authors/')
            self.assertEqual(req.status_code, 405)

            req = self.client.patch('/api/authors/')
            self.assertEqual(req.status_code, 405)

            req = self.client.delete('/api/authors/')
            self.assertEqual(req.status_code, 405)

            req = self.client.head('/api/authors/')
            self.assertEqual(req.status_code, 405)

    def test_get_author(self):
        """Test that we can get an author"""
        with self.settings(SECURE_SSL_REDIRECT = False):
            self.client.force_login(user=self.user)
            req = self.client.get('/api/authors/{}/'.format(self.author.id))
            self.assertEqual(req.status_code, 200)
            self.assertEqual(req.data['type'], 'author')
            self.assertNotEquals(req.data['type'], 'authors')

            self.assertEqual(req.data['id'], f"http://testserver/api/authors/{str(self.author.id)}/")
            # self.assertEqual(req.data['host'], self.author.host)
            self.assertEqual(req.data['displayName'], self.author.display_name)
            self.assertEqual(req.data['github'], self.author.github)
            self.assertEqual(req.data['profileImage'], self.author.profile_image)
