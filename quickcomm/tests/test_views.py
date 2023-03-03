from django.test import TestCase, Client
from django.contrib.auth.models import User
from quickcomm.models import Author, Post, Like
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

        self.assertEqual(response.status_code, 302)
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
            'password1': 'pass1',
            'password2': 'pass1',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.wsgi_request.user.is_authenticated, response.content)

    def test_duplicate_register(self):
        response = self.client.post('/register/', {
            'username': 'user',
            'password1': 'pass',
            'password2': 'pass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.wsgi_request.user.is_authenticated, response.content)

    def test_admin_denied_registration(self):
        self.registration_settings.are_new_users_active = False
        self.registration_settings.save()

        response = self.client.post('/register/', {
            'username': 'user2',
            'password1': 'pass2',
            'password2': 'pass2',
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

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.wsgi_request.user.is_authenticated)

        response = self.client.post('/logout/', {})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        

class LikePostTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass1'
        )

        self.user2 = User.objects.create_user(
            username='user2',
            password='pass2'
        )

        
        self.author1 = Author.objects.create(user=self.user1, host='http://127.0.0.1:8000', display_name='user1', github='https://github.com/', profile_image='https://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg')
        self.author1.save()

        self.author2 = Author.objects.create(user=self.user2, host='http://127.0.0.1:8000', display_name='user2', github='https://github.com/', profile_image='https://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg')
        self.author2.save()

    def test_viewing_post(self):
        author1 = Author.objects.all()[0]
        c = Client()
        response = c.post('/post/'+str(author1.id)+"/",)
        c.get('/post/'+str(author1.id)+"/",)
        self.assertEqual(response.status_code, 302)
    def test_like(self):
        c = Client()
        author1 = Author.objects.all()[0]
        author2 = Author.objects.all()[1]
        post = Post.objects.create(author=author1, title='My Post', source='http://someurl.ca', origin='http://someotherurl.ca', description='My Post Description', content_type='text/plain', content='My Post Content', visibility='PUBLIC', unlisted=False, categories='["test"]')
        post.full_clean()
        response = c.get('/post/'+str(author2.id)+"/"+'post_liked')
        self.assertEqual(response.status_code, 302)
class EditProfileViewTest(TestCase):
    def setUp(self):
        
        user = User.objects.create_user(
            username='user',
            password='pass'
        )
        
        user.save()
        
        author = Author.objects.create(user=user, host='http://127.0.0.1:8000', display_name='First Name', github='https://github.com/', profile_image='https://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg')
        author.full_clean()
        
        
    def test_edit_not_logged_in(self):
        pass
    
    
    def test_edit_name(self):
        # c = Client()
        # author = Author.objects.all()[0]
        
        # c.post('/login/', {
        #     'display_name': 'user',
        #     'password': 'pass',
        # })  

        # response = c.post('/authors/'+str(author.id)+"/", {
        #     'display_name': 'Second Name',
        #     'github': 'http://github.com/please',
        #     'profile_image': 'http://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg'
        # })
        
        # c.get('/authors/'+str(author.id)+"/")
        
        # self.assertEqual(response.status_code, 200)
        # self.assertNotEqual(author.display_name, "First Name")
        pass
        
    
        # self.assertEqual(response.status_code, 200)
