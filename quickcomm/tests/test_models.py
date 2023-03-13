import uuid
from django.test import TestCase
from django.contrib.auth.models import User
from quickcomm.models import Author, Post
from django.core.exceptions import ValidationError

# Create your tests here.

class AuthorModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a user
        user = User.objects.create_user(username='rajan', password='badpassword')
        user.save()

        # Create an author
        author = Author.objects.create(user=user, host='http://127.0.0.1:8000', display_name='My Real Cool Name', github='rajanmaghera', profile_image='https://avatars.githubusercontent.com/u/16507599?v=4')
        author.full_clean()


    def test_string_name(self):
        """The string representation of the Author model is correct"""

        author = list(Author.objects.all())[0]
        expected_object_name = f'{author.display_name} ({author.user.username})'
        self.assertEquals(expected_object_name, str(author))

    def test_uuid(self):
        """The pk of the Author model is a UUID"""

        author = Author.objects.all()[0]
        self.assertNotEquals(author.id, 1)
        self.assertRaises(Author.DoesNotExist, Author.objects.get, id=1)

        # this would cause an exception if the id is not a valid UUID
        uuid.UUID(str(author.id))
        self.assertRaises(ValueError, uuid.UUID, '1')

    def test_user(self):
        """The user field of the Author model is connected to a user"""

        author = Author.objects.all()[0]
        user = User.objects.all()[0]
        self.assertEquals(author.user, user)
        self.assertEquals(author.user.username, 'rajan')

    def test_fields(self):
        """The fields of the Author model are correct"""

        author = Author.objects.all()[0]
        self.assertEquals(author.host, 'http://127.0.0.1:8000')
        self.assertEquals(author.display_name, 'My Real Cool Name')
        self.assertEquals(author.github, 'rajanmaghera')
        self.assertEquals(author.profile_image, 'https://avatars.githubusercontent.com/u/16507599?v=4')

    def test_author_update(self):
        """The fields of the Author model can be updated"""

        author = Author.objects.all()[0]
        value = 'My Real Cool Name'
        self.assertEquals(author.display_name, value)
        author.display_name = 'My Real Cool Name 2'
        author.full_clean()
        author.save()
        self.assertEquals(author.display_name, 'My Real Cool Name 2')
        author_2 = Author.objects.get(id=author.id)
        self.assertEquals(author_2.display_name, 'My Real Cool Name 2')

    def test_creating_with_empty_fields(self):
        """The fields of the Author model cannot be empty"""

        user = User.objects.create_user(username='rajan2', password='badpassword')
        user.full_clean()

        author = Author.objects.create(user=user)
        self.assertRaises(ValidationError, author.full_clean)

    def test_invalid_url(self):
        """The fields of the Author model must be valid URLs"""

        user = User.objects.create_user(username='rajan3', password='badpassword')
        user.full_clean()

        author = Author.objects.create(user=user, host='not a url', display_name='My Real Cool Name', github='not a url', profile_image='https://avatars.githubusercontent.com/u/16507599?v=4')
        self.assertRaises(ValidationError, author.full_clean)

        author.host = 'https://realurl.com/along'
        author.full_clean()




class PostModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a user
        user = User.objects.create_user(username='rajan', password='badpassword')
        user.save()

        # Create an author
        author = Author.objects.create(user=user, host='http://127.0.0.1:8000', display_name='My Real Cool Name', github='rajanmaghera', profile_image='https://avatars.githubusercontent.com/u/16507599?v=4')
        author.full_clean()

        # Create a post
        post = Post.objects.create(author=author, title='My Post', source='http://someurl.ca', origin='http://someotherurl.ca', description='My Post Description', content_type='text/plain', content='My Post Content', visibility='PUBLIC', unlisted=False, categories='["test"]')
        post.full_clean()

    def test_string_name(self):
        """The string representation of the Post model is correct"""

        post = Post.objects.all()[0]
        expected_object_name = f'{post.title} by {post.author}'
        self.assertEquals(expected_object_name, str(post))

    def test_uuid(self):
        """The pk of the Post model is a UUID"""

        post = Post.objects.all()[0]
        self.assertNotEquals(post.id, 1)
        self.assertRaises(Post.DoesNotExist, Post.objects.get, id=1)

        # this would cause an exception if the id is not a valid UUID
        uuid.UUID(str(post.id))
        self.assertRaises(ValueError, uuid.UUID, '1')

    def test_author(self):
        """The author field of the Post model is connected to an author"""

        post = Post.objects.all()[0]
        author = Author.objects.all()[0]
        self.assertEquals(post.author, author)
        self.assertEquals(post.author.user.username, 'rajan')

    def test_fields(self):
        """The fields of the Post model are correct"""

        post = Post.objects.all()[0]
        self.assertEquals(post.title, 'My Post')
        self.assertEquals(post.source, 'http://someurl.ca')
        self.assertEquals(post.origin, 'http://someotherurl.ca')
        self.assertEquals(post.description, 'My Post Description')
        self.assertEquals(post.content_type, 'text/plain')
        self.assertEquals(post.content, 'My Post Content')
        self.assertEquals(post.visibility, 'PUBLIC')
        self.assertEquals(post.unlisted, False)
        self.assertEquals(post.categories, '["test"]')


    def test_post_update(self):
        """The fields of the Post model can be updated"""

        post = Post.objects.all()[0]
        value = 'My Post'
        self.assertEquals(post.title, value)
        post.title = 'My Post 2'
        post.save()
        self.assertEquals(post.title, 'My Post 2')
        post_2 = Post.objects.get(id=post.id)
        self.assertEquals(post_2.title, 'My Post 2')

    def test_creating_with_empty_fields(self):
        """The fields of the Post model cannot be empty"""

        author = Author.objects.all()[0]
        post = Post.objects.create(author=author)
        self.assertRaises(ValidationError, post.full_clean)

    def test_invalid_url(self):
        """The URL fields of the Post model must be valid URLs"""

        author = Author.objects.all()[0]
        post = Post.objects.create(author=author, title="wowo!", source='not a url', origin='not a url', description='My Post Description', content_type='text/plain', content='My Post Content', visibility='FRIENDS', unlisted=False, categories='["wow"]')
        self.assertRaises(ValidationError, post.full_clean)

        # otherwise it works
        post.origin = 'https://realurl.com/'
        post.source = 'http://realurl.com'

        post.full_clean()



