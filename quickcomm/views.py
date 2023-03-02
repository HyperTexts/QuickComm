from django import template
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from quickcomm.forms import CreateImageForm, CreateMarkdownForm, CreatePlainTextForm, CreateLoginForm
from quickcomm.models import Author, Post

# Create your views here.


def index(request):
    context = {
        'posts': Post.objects.all(),
        'request': request
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

r = template.Library()
@r.filter(name='get_image')
def get_image(post, request):
    return Post.get_image_url(post, request)



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

@login_required
def create_image(request):
    if request.method == 'POST':
        form = CreateImageForm(request.POST, request.FILES)
        if form.is_valid():
            author = Author.objects.get(user=request.user)
            form.save(author)
            return HttpResponseRedirect('/')
    else:
        form = CreateImageForm()
    return render(request, 'quickcomm/create.html', {'form': form, 'post_type': 'image'})

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
    print('test')
    auth_logout(request)
    return redirect('/')


def register(request):
    # TODO implement register
    return HttpResponse('Register Page')
