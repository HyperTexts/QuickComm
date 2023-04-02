import base64
from django import forms
from quickcomm.validators import validate_image_upload_format
from .models import ImageFile, Post, Author, Comment
from django.core.validators import URLValidator
from martor.fields import MartorFormField
from django.urls import reverse

# This file contains all the form resposes that the API wil uses.


class CreatePlainTextForm(forms.Form):
    """A form for creating a plain text post."""

    title = forms.CharField(max_length=100)
    description = forms.CharField(max_length=1000)
    content = forms.CharField(widget=forms.Textarea())
    categories = forms.CharField(max_length=1000)
    visibility = forms.ChoiceField(choices=Post.PostVisibility.choices)
    unlisted = forms.BooleanField(required=False)
    source = forms.URLField(widget=forms.HiddenInput, required=False)
    origin = forms.URLField(widget=forms.HiddenInput, required=False)

    def save(self, author, request=None):
        post = Post(
            title=self.cleaned_data['title'],
            description=self.cleaned_data['description'],
            content_type="text/plain",
            content=self.cleaned_data['content'],
            categories=self.cleaned_data['categories'],
            author=author,
            visibility=self.cleaned_data['visibility'],
            unlisted=self.cleaned_data['unlisted']
        )
        post.save()
        try:
            uri = request.build_absolute_uri(reverse('api:post-detail', kwargs={'authors_pk': author.id, 'pk': post.id}))
            post.source = uri
            post.origin = uri
            post.save()
        except Exception as e:
            print(e)
            pass
        
        return post
    
    def update_info(self,author,post_id):
        post = Post(
        title=self.cleaned_data['title'],
        source=self.cleaned_data['source'],
        origin=self.cleaned_data['origin'],
        description=self.cleaned_data['description'],
        content_type="text/plain",
        content=self.cleaned_data['content'],
        categories=self.cleaned_data['categories'],
        author=author,
        visibility=self.cleaned_data['visibility'],
        unlisted=self.cleaned_data['unlisted'])
        post.update_info(post,post_id)
        return post

class CreateMarkdownForm(forms.Form):
    """A form for creating a markdown post."""

    title = forms.CharField(max_length=100)
    description = forms.CharField(max_length=1000)
    content = MartorFormField()
    categories = forms.CharField(max_length=1000)
    visibility = forms.ChoiceField(choices=Post.PostVisibility.choices)
    unlisted = forms.BooleanField(required=False)
    source = forms.URLField(widget=forms.HiddenInput, required=False)
    origin = forms.URLField(widget=forms.HiddenInput, required=False)

    def save(self, author, request):
        post = Post(
            title=self.cleaned_data['title'],
            description=self.cleaned_data['description'],
            content_type="text/markdown",
            content=self.cleaned_data['content'],
            categories=self.cleaned_data['categories'],
            author=author,
            visibility=self.cleaned_data['visibility'],
            unlisted=self.cleaned_data['unlisted']
        )
        post.save()
        try:
            uri = request.build_absolute_uri(reverse('api:post-detail', kwargs={'authors_pk': author.id, 'pk': post.id}))
            post.source = uri
            post.origin = uri
            post.save()
        except Exception as e:
            print(e)
            pass
        
        return post
    
    def update_info(self,author,post_id):
        post = Post(
        title=self.cleaned_data['title'],
        source=self.cleaned_data['source'],
        origin=self.cleaned_data['origin'],
        description=self.cleaned_data['description'],
        content_type="text/markdown",
        content=self.cleaned_data['content'],
        categories=self.cleaned_data['categories'],
        author=author,
        visibility=self.cleaned_data['visibility'],
        unlisted=self.cleaned_data['unlisted'])
        post.update_info(post,post_id)
        return post

class CreateImageForm(forms.Form):
    """A form for creating an image post."""

    title = forms.CharField(max_length=100)
    description = forms.CharField(max_length=1000)
    content = forms.ImageField(validators=[validate_image_upload_format])
    categories = forms.CharField(max_length=1000)
    visibility = forms.ChoiceField(choices=Post.PostVisibility.choices)
    unlisted = forms.BooleanField(required=False)
    source = forms.URLField(widget=forms.HiddenInput, required=False)
    origin = forms.URLField(widget=forms.HiddenInput, required=False)    

    def get_content_type(self):
        ct_raw = self.cleaned_data['content'].content_type
        if ct_raw == "image/jpeg" or ct_raw == "image/jpg":
            return Post.PostType.JPG
        elif ct_raw == "image/png":
            return Post.PostType.PNG
        return None

    def save(self, author, request):

        post = Post(
            title=self.cleaned_data['title'],
            description=self.cleaned_data['description'],
            content_type=self.get_content_type(),
            content="",
            categories=self.cleaned_data['categories'],
            author=author,
            visibility=self.cleaned_data['visibility'],
            unlisted=self.cleaned_data['unlisted']
        )
        post.save()
        try:
            uri = request.build_absolute_uri(reverse('api:post-detail', kwargs={'authors_pk': author.id, 'pk': post.id}))
            post.source = uri
            post.origin = uri
            post.save()
        except Exception as e:
            print(e)
            pass

        # Save the image to the media folder
        image = ImageFile(
            post=post,
            image=self.cleaned_data['content']
        )
        image.save()

        return post

class CreateLoginForm(forms.Form):
    """A form for logging in."""

    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())
        
class EditProfileForm(forms.Form):
    display_name = forms.CharField(max_length=100, required=False)
    github = forms.URLField(required=False)
    profile_image = forms.URLField(validators=[URLValidator], required=False)
        
    def save(self, author):
        author.display_name = self.cleaned_data['display_name']
        author.github = self.cleaned_data['github']
        author.profile_image = self.cleaned_data['profile_image']
        author.save()
        return author
    
class CreateCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']

    


