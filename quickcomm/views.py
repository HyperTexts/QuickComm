from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from quickcomm.forms import CreateMarkdownForm, CreatePlainTextForm, CreateLoginForm, CreateRegisterForm
from quickcomm.models import Author, Post, RegistrationSettings

# Create your views here.


def index(request):
    context = {
        'posts': Post.objects.all()
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
                return redirect('/')
            else:
                form = CreateLoginForm()
    else:
        form = CreateLoginForm()
    return render(request, 'quickcomm/login.html', {'form': form})


@login_required
def logout(request):
    print('test')
    auth_logout(request)
    return redirect('/')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            author = Author(user=user)
            author.save()
            # either log the user in or set their account to inactve
            admin_approved = RegistrationSettings.objects.first().are_new_users_active
            if admin_approved:
                auth_login(request, user)
            else:
                user.is_active = False
                user.save()
            return redirect('/')
        else:
            form = UserCreationForm()
    else:
        form = UserCreationForm()
    context = {
        'form': UserCreationForm()
    }
    return render(request, 'quickcomm/register.html', context)
