from django.test import TestCase, Client
from django.contrib.auth.models import User
from quickcomm.models import Author, Post, RegistrationSettings, Comment

class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            password='pass'
        )

    def test_login(self):
        response = self.client.post('/login/', {
            'username': 'user',
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
            'username': 'user',
            'password': 'pass',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.wsgi_request.user.is_authenticated)

        response = self.client.get('/logout/', {})
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

        
        self.author1 = Author.objects.create(user=self.user1, display_name='user1', github='https://github.com/', profile_image='https://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg')
        self.author1.save()

        self.author2 = Author.objects.create(user=self.user2, display_name='user2', github='https://github.com/', profile_image='https://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg')
        self.author2.save()

        self.post = Post.objects.create(author=self.author1, title='My Post', source='http://someurl.ca', origin='http://someotherurl.ca', description='My Post Description', content_type='text/plain', content='My Post Content', visibility='PUBLIC', unlisted=False, categories='["test"]')
        self.post.full_clean()
        self.post.save()

    def test_viewing_post(self):
        c = Client()
        c.login(username='user1', password='pass1')
        response = c.get('/authors/'+str(self.author1.id)+'/posts/'+str(self.post.id)+"/")
        self.assertEqual(response.status_code, 200)

    def test_like(self):
        c = Client()
        c.login(username='user2', password='pass2')
        response = c.get('/authors/'+str(self.author1.id)+'/posts/'+str(self.post.id)+"/"+"post_liked")
        self.assertEqual(response.status_code, 302)

class LikeCommentTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass1'
        )

        self.user2 = User.objects.create_user(
            username='user2',
            password='pass2'
        )

        self.author1 = Author.objects.create(user=self.user1, display_name='user1', github='https://github.com/test', profile_image='https://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg')
        self.author1.save()

        self.author2 = Author.objects.create(user=self.user2, display_name='user2', github='https://github.com/test', profile_image='https://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg')
        self.author2.save()

        self.post = Post.objects.create(author=self.author1, title='My Post', source='http://someurl.ca', origin='http://someotherurl.ca', description='My Post Description', content_type='text/plain', content='My Post Content', visibility='PUBLIC', unlisted=False, categories='["test"]')
        self.post.full_clean()
        self.post.save()

        self.comment = Comment.objects.create(post=self.post, author=self.author2, comment='Comment trial', content_type='text/plain')
        self.comment.full_clean()
        self.comment.save()

    def test_viewing_comment(self):
        c = Client()
        c.login(username='user1', password='pass1')
        response = c.get('/authors/'+str(self.author1.id)+'/posts/'+str(self.post.id)+"/")
        self.assertEqual(response.status_code, 200)

    def test_like(self):
        c = Client()
        c.login(username='user2', password='pass2')
        response = c.get('/authors/'+str(self.author1.id)+'/posts/'+str(self.post.id)+"/" + str(self.comment.id) +"/like_comment")
        self.assertEqual(response.status_code, 302)


class EditProfileViewTest(TestCase):
    def setUp(self):
        
        user = User.objects.create_user(
            username='user',
            password='pass'
        )
        
        user.save()
        
        author = Author.objects.create(user=user, display_name='First Name', github='https://github.com/test', profile_image='https://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg')
        author.full_clean()
        author.save()
        
    # TODO currently you must be logged in to view a profile so you get a 302 if you try this, not sure if you should be able to see profiles unauthenticated or not
    def test_edit_not_logged_in(self):
        c = Client()
        author = Author.objects.all()[0]
        response = c.post('/authors/'+str(author.id)+"/", {
            'display_name': 'Second Name',
            'github': 'https://github.com/test',
            'profile_image': 'http://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg'
        })
        # self.assertEqual(response.status_code, 200)
        self.assertEqual(author.display_name, Author.objects.all()[0].display_name)
        self.assertEqual(author.github, Author.objects.all()[0].github)
        self.assertEqual(author.profile_image, Author.objects.all()[0].profile_image)
    
    
    def test_edit_name(self):
        c = Client()
        author = Author.objects.all()[0]
        
        c.login(username='user', password='pass')

        response = c.post('/authors/'+str(author.id)+"/", {
            'display_name': 'Second Name',
        })

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(author.display_name, Author.objects.all()[0].display_name)

    def test_edit_github(self):
        c = Client()
        author = Author.objects.all()[0]
        
        c.login(username='user', password='pass')

        response = c.post('/authors/'+str(author.id)+"/", {
            'github': 'https://github.com/newTest',
        })

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(author.github, Author.objects.all()[0].github)

    def test_edit_profile_image(self):
            c = Client()
            author = Author.objects.all()[0]
            
            c.login(username='user', password='pass')

            response = c.post('/authors/'+str(author.id)+"/", {
                'profile_image': 'http://www.history.com/.image/c_fit%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_620/MTU3ODc5MDg2NDM2NjU2NDU3/reagan_flags.jpg'
            })

            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(author.profile_image, Author.objects.all()[0].profile_image)
