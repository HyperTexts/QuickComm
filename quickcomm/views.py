from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from quickcomm.forms import CreateMarkdownForm, CreatePlainTextForm, CreateLoginForm, CreateCommentForm, CreateRegisterForm
from quickcomm.models import Author, Post, Like, Comment

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
                return HttpResponse('Login Page')
            else:
                form = CreateLoginForm()
    else:
        form = CreateLoginForm()
    return render(request, 'quickcomm/login.html', {'form': form})

@login_required
def post_view(request, post_id):
    objects = Post.objects.all()
    post = objects.get(pk=post_id)
    post_comments = Comment.objects.filter(post=post).order_by("-published")
    is_liked = False
    if request.user.is_authenticated:
        like_key = "post_like_{post_id}"
        is_liked = request.session.get(like_key, False)

    context = {"id": post.id, "title": post.title, "author": post.author, "description": post.description, "content": post.content, "is_post_liked": is_liked,"post_comments":post_comments}

    return render(request, "quickcomm/post.html", context)

@login_required
def post_like(request, post_id):
    objects = Post.objects.all()
    post = objects.get(pk=post_id)

    if request.user.is_authenticated:
        print("comes in here?")
        author = Author.objects.all().get(user=request.user)
        like_obj, created_obj = Like.objects.get_or_create(post=post, author=author)
        if not created_obj:
            like_obj.delete()
        like_key = f"post_like_{post_id}"
        request.session[like_key] = not created_obj

    return redirect("post_view", post_id=post_id)

@login_required
def post_comment(request, post_id):
    objects = Post.objects.all()
    post = objects.get(pk=post_id)
    if request.method == 'POST':
        form = CreateCommentForm(request.POST)
        if form.is_valid():
            author = Author.objects.all().get(user=request.user)
            comment = Comment()
            comment.post = post
            comment.author = author
            comment.comment = form.cleaned_data['comment']
            comment.save()
            return HttpResponseRedirect(reverse('post_comment', args=[post.pk]))
        
    else:
        form = CreateCommentForm()
    return redirect("post_view", post_id=post_id)
   

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
