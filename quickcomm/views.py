from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from quickcomm.forms import CreateMarkdownForm, CreatePlainTextForm, CreateLoginForm, EditProfileForm
from quickcomm.models import Author, Post

# Create your views here.

def get_current_author(request):
    if request.user.is_authenticated:
        author = Author.objects.get(user_id = request.user.id)
    else:
        author = None
    return author

def index(request):
    current_author = get_current_author(request)
    context = {
        'posts': Post.objects.all(),
        'current_author': current_author
    }
    return render(request, 'quickcomm/index.html', context)


@login_required
def create_post(request):
    current_author = get_current_author(request)
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
    return render(request, 'quickcomm/create.html', {'form': form, 'post_type': 'plain text', 'current_author': current_author,})


@login_required
def create_markdown(request):
    current_author = get_current_author(request)
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
    return render(request, 'quickcomm/create.html', {'form': form, 'post_type': 'CommonMark Markdown', 'current_author': current_author,})


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
    # TODO implement register
    return HttpResponse('Register Page')

def view_authors(request):
    current_author = get_current_author(request)
    page = request.GET.get('page', '1')
    size = request.GET.get('size', '10')
    context = {
        'authors': Author.objects.all().order_by('display_name'),
        'page': page,
        'size': size,
        'current_author': current_author,
    }
    
    return render(request, 'quickcomm/authors.html', context)

def view_profile(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    current_author = get_current_author(request)
    if not current_author:
        return render(request, 'quickcomm/profile.html', {
                    'author': author,
                    'form': EditProfileForm()
                    })
    if request.method == 'POST':
        form = EditProfileForm(request.POST, initial={"display_name": current_author.display_name, "github": current_author.github, "profile_image": current_author.profile_image})
        if form.is_valid():
            form.save(author)
        else:
            form = EditProfileForm( initial={"display_name": current_author.display_name, "github": current_author.github, "profile_image": current_author.profile_image})
    else:
        form = EditProfileForm( initial={"display_name": current_author.display_name, "github": current_author.github, "profile_image": current_author.profile_image})
        
    current_author = get_current_author(request)
    return render(request, 'quickcomm/profile.html', {
                    'author': author,
                    'current_author': current_author,
                    'form': form,
                    })
    
def view_followers(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    current_author = get_current_author(request)
    
    return render(request, 'quickcomm/followers.html', {
                    'author': author,
                    'current_author': current_author,
                    })
