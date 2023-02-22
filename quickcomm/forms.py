from django import forms
from django.contrib.auth.models import User
from .models import Post
from django.core.validators import URLValidator
from martor.fields import MartorFormField


class CreatePlainTextForm(forms.Form):
    title = forms.CharField(max_length=100)
    source = forms.URLField(validators=[URLValidator])
    origin = forms.URLField(validators=[URLValidator])
    description = forms.CharField(max_length=1000)
    content = forms.CharField(widget=forms.Textarea())
    categories = forms.CharField(max_length=1000)
    visibility = forms.ChoiceField(choices=Post.PostVisibility.choices)
    unlisted = forms.BooleanField(required=False)

    def save(self, author):
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
            unlisted=self.cleaned_data['unlisted']
        )
        post.save()
        return post


class CreateMarkdownForm(forms.Form):
    title = forms.CharField(max_length=100)
    source = forms.URLField(validators=[URLValidator])
    origin = forms.URLField(validators=[URLValidator])
    description = forms.CharField(max_length=1000)
    content = MartorFormField()
    categories = forms.CharField(max_length=1000)
    visibility = forms.ChoiceField(choices=Post.PostVisibility.choices)
    unlisted = forms.BooleanField(required=False)

    def save(self, author):
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
            unlisted=self.cleaned_data['unlisted']
        )
        post.save()
        return post


class CreateLoginForm(forms.Form):
    display_name = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())

    def save(self):
        post = Post(
            display_name=self.cleaned_data['display_name'],
            password=self.cleaned_data['password']
        )
        post.save()
        return post


class CreateRegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password']
