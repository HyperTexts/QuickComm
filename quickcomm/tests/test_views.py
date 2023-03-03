from django.test import TestCase, Client
from django.contrib.auth.models import User
from quickcomm.models import Author
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

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
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
        
    
