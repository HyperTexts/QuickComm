import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quickcomm.settings")

from django.test import TestCase, Client
from django.contrib.auth.models import User
from quickcomm.models import Author,Follow, follow_request
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
        
        self.user = User.objects.create_user(
            username='user',
            password='pass'
        )

        
        self.author = Author.objects.create(user=self.user, host='http://127.0.0.1:8000', display_name='First Name', github='https://github.com/', profile_image='https://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg')
        self.author.save()
        
        
    def test_edit_not_logged_in(self):
        pass
    
    
    def test_edit_name(self):
        c = Client()
        author = Author.objects.all()[0]
        
        c.post('/login/', {
            'display_name': 'user',
            'password': 'pass',
        })  

        response = c.post('/authors/'+str(author.id)+"/", {
            'display_name': 'Second Name',
            'github': 'http://github.com/please',
            'profile_image': 'http://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg'
        })
        
        c.get('/authors/'+str(author.id)+"/")
        
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(author.display_name, "First Name")
    
class FollowersTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username='user',
            password='pass'
        )
        user.save()
        
        second_user=User.objects.create_user(
            username='user2',
            password='pass2'
        )
        second_user.save()
    def test_follower(self):
        pass

class ViewFollowersTest(TestCase):
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

        self.follow = Follow.objects.create(follower=self.author2, following=self.author1)

    def testViewFollowers(self):
        c = Client()
        
        response = self.client.get('/authors/'+str(self.author1.id)+'/followers/')
        self.assertEqual(response.status_code, 200)

        # check to make sure it is user 1's page and user 2 appears as a follower
        find_user_2 = str(response.content).find('<h3 class=""> user2 </h3>')
        self.assertTrue(find_user_2 > -1)
        
        find_user_1 = str(response.content).find('<h1>user1\\\'s Followers</h1>')
        self.assertTrue(find_user_1 > -1, response.content)

        miss_user_2 = str(response.content).find('<h1>user2\\\'s Followers</h1>')
        self.assertTrue(miss_user_2 == -1)
        
        miss_user_1 = str(response.content).find('<h3 class=""> user1 </h3>')
        self.assertTrue(miss_user_1 == -1)
class ViewRequestsTest(TestCase):
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

        self.request=follow_request.objects.create(from_user=self.author1, to_user=self.author2)
    
    def testViewRequest(self):
        c=Client()

        response=self.client.get('/authors/'+str(self.author1.id)+'/requests/')
        self.assertEqual(response.status_code,200)

        find_user_1=str(response.content).find('<h3 class=""> user1 </h3>')
        self.assertTrue(find_user_1>-1)

        
    
