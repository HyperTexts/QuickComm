from dateutil import parser
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User

from quickcomm.forms import CreateMarkdownForm, CreatePlainTextForm, CreateLoginForm, CreateRegisterForm
from quickcomm.models import Author, Follow, Inbox
from .external_requests import get_github_stream

# Create your views here.

@login_required
def index(request):

    # Get the author object for the current user
    author = Author.objects.get(user=request.user)
    inbox = list(Inbox.objects.filter(author=author).order_by('-added'))

    # Get the GitHub stream for all of the author's followed users
    following = [ follow.following for follow in Follow.objects.filter(follower=author) ]
    following.append(author)
    for follow in following:
        github = get_github_stream(follow.github)
        github = [dict(item, **{
            'format': 'github',
            'localAuthor': Author.objects.all()[0],
            'added': parser.parse(item["created_at"])
                                }) for item in github]
        inbox.extend(github)

    def get_date(item):
        """Get the date of the item, regardless of whether it's a dict or an object."""
        if isinstance(item, dict):
            return item['added']
        else:
            return item.added

    # Sort the inbox by date, most recent first
    inbox.sort(key=lambda x: get_date(x), reverse=True)

    context = {
        'inbox': inbox,
    }
    return render(request, 'quickcomm/index.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = CreatePlainTextForm(request.POST)
        if form.is_valid():
            author = Author.objects.get(user=request.user)
            form.save(author)
            return HttpResponseRedirect('/')
        else:
            form = CreatePlainTextForm()
    else:
        form = CreatePlainTextForm()
    return render(request, 'quickcomm/create.html', {'form': form, 'post_type': 'plain text'})


@login_required
def create_markdown(request):
    if request.method == 'POST':
        form = CreateMarkdownForm(request.POST)
        if form.is_valid():
            author = Author.objects.get(user=request.user)
            form.save(author)
            return HttpResponseRedirect('/')
        else:
            form = CreateMarkdownForm()
    else:
        form = CreateMarkdownForm()
    return render(request, 'quickcomm/create.html', {'form': form, 'post_type': 'CommonMark Markdown'})


def login(request):
    if request.method == 'POST':
        form = CreateLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=request.POST['display_name'], password=request.POST['password'])
            if user is not None:
                auth_login(request, user)
                return HttpResponse('Login Page')
            else:
                form = CreateLoginForm()
    else:
        form = CreateLoginForm()
    return render(request, 'quickcomm/login.html', {'form': form})


@login_required
def logout(request):
    auth_logout(request)
    return redirect('/')


def register(request):
    if request.method == 'POST':
        form = CreateRegisterForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            if username and password:
                user = User.objects.create_user(
                    username=username, password=password)
                author = Author(user=user)
                author.save()
                auth_login(request, user)
                return redirect('/')
            else:
                form = CreateRegisterForm()
    else:
        form = CreateRegisterForm()
    return render(request, 'quickcomm/login.html', {'form': form})
