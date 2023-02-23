from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from ..models import RegistrationSettings


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


class RegisterViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            password='pass'
        )

        self.registration_settings = RegistrationSettings(
            are_new_users_active=True)
        self.registration_settings.save()

    def test_register(self):
        response = self.client.post('/register/', {
            'username': 'user1',
            'password': 'pass1',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.wsgi_request.user.is_authenticated, response.content)

    def test_duplicate_register(self):
        response = self.client.post('/register/', {
            'username': 'user',
            'password': 'pass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.wsgi_request.user.is_authenticated, response.content)

    def test_admin_denied_registration(self):
        self.registration_settings.are_new_users_active = False
        self.registration_settings.save()

        response = self.client.post('/register/', {
            'username': 'user2',
            'password': 'pass2',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            response.wsgi_request.user.is_authenticated, response.content)


class LogoutViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            password='pass'
        )

    def test_logout(self):
        response = self.client.post('/login/', {
            'display_name': 'user',
            'password': 'pass',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.wsgi_request.user.is_authenticated)

        response = self.client.post('/logout/', {})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
