from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            password='pass'
        )

    def test_login(self):
        response = self.client.post('/login/', {
            'display_name': 'user',
            'password': 'pass',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.wsgi_request.user.is_authenticated, response.content)
