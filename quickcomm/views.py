from dateutil import parser
from django.shortcuts import render, redirect
from django import template
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from quickcomm.forms import CreateImageForm, CreateMarkdownForm, CreatePlainTextForm, CreateLoginForm, CreateCommentForm, EditProfileForm
from quickcomm.models import Author, Post, Like, Comment, RegistrationSettings, Inbox,Follow,follow_request
from django.contrib.auth.forms import UserCreationForm

from quickcomm.models import Author, Follow, Inbox
from .external_requests import get_github_stream

# Create your views here.

def get_current_author(request):
    if request.user.is_authenticated:
        author = Author.objects.get(user_id = request.user.id)
    else:
        author = None
    return author

@login_required
def index(request):

    current_author = get_current_author(request)

    # Get the author object for the current user
    author = Author.objects.get(user=request.user)
    inbox = list(Inbox.objects.filter(author=current_author).order_by('-added'))

    # Get the GitHub stream for all of the author's followed users
    following = [ follow.following for follow in Follow.objects.filter(follower=author) ]
    following.append(author)
    for follow in following:
        github = get_github_stream(follow.github)
        if 'message' in github:
            if github['message'] == 'Not Found':
                continue
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
        'inbox': inbox,
        'current_author': current_author,
    }
    return render(request, 'quickcomm/index.html', context)


@login_required
def create_post(request):
    current_author = get_current_author(request)
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

r = template.Library()
@r.filter(name='get_image')
def get_image(post, request):
    return Post.get_image_url(post, request)



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

@login_required
def create_image(request):
    current_author = get_current_author(request)
    if request.method == 'POST':
        form = CreateImageForm(request.POST, request.FILES)
        if form.is_valid():
            author = Author.objects.get(user=request.user)
            form.save(author)
            return HttpResponseRedirect('/')
    else:
        form = CreateImageForm()
    return render(request, 'quickcomm/create.html', {'form': form, 'post_type': 'image', 'current_author': current_author,})

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
def post_view(request, post_id, author_id):
    current_author = get_current_author(request)
    post = get_object_or_404(Post, pk=post_id)
    post_comments = Comment.objects.filter(post=post).order_by("-published")
    is_liked = False
    if request.user.is_authenticated:
        # like_key = "post_like_{post_id}"
        # is_liked = request.session.get(like_key, False)
        like = Like.objects.filter(post=post, author=current_author)
        print(like)
        if like:
            is_liked = True

    context = {"post": post, "is_post_liked": is_liked,"post_comments":post_comments, "current_author": current_author}

    return render(request, "quickcomm/post.html", context)

@login_required
def post_like(request, post_id, author_id):
    objects = Post.objects.all()
    post = objects.get(pk=post_id)

    # post = get_object_or_404(Post, pk=post_id)

    if request.user.is_authenticated:
        author = Author.objects.all().get(user=request.user)
        like_obj, created_obj = Like.objects.get_or_create(post=post, author=author)
        if not created_obj:
            like_obj.delete()
        like_key = f"post_like_{post_id}"
        request.session[like_key] = not created_obj

    return redirect("post_view", post_id=post_id, author_id=author_id)

@login_required
def post_comment(request, post_id, author_id):
    post = Post.objects.get(pk=post_id)

    if request.method == 'POST':
        form = CreateCommentForm(request.POST)
        if form.is_valid():
            author = Author.objects.all().get(user=request.user)
            comment = Comment()
            comment.post = post
            comment.author = author
            comment.comment = form.cleaned_data['comment']
            comment.save()
            return redirect('post_comment', post_id=post_id, author_id=author_id)
    return redirect("post_view", post_id=post_id, author_id=author_id)
   

@login_required
def logout(request):
    auth_logout(request)
    return redirect('/')


def register(request):
    if request.method == 'POST':
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                author = Author(user=user, host='http://127.0.0.1:8000', display_name=user, github='https://github.com/', profile_image='https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png')
                author.save()
                # either log the user in or set their account to inactve
                admin_approved = RegistrationSettings.objects.first().are_new_users_active
                if admin_approved:
                    auth_login(request, user)
                else:
                    user.is_active = False
                    user.save()
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
    context = {
            'form': UserCreationForm()
        }
    return render(request, 'quickcomm/register.html', context)

def view_authors(request):
    current_author = get_current_author(request)

    authors = Author.objects.all().order_by('display_name')

    size = request.GET.get('size', '10')
    paginator = Paginator(authors, size)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'size': size,
        'current_author': current_author,
    }
    
    return render(request, 'quickcomm/authors.html', context)

def view_profile(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    current_author = get_current_author(request)
    form = EditProfileForm()

    if not current_author:
        return render(request, 'quickcomm/profile.html', {
                    'author': author,
                    'form': form
                    })
        
    current_attributes = {"display_name": current_author.display_name, "github": current_author.github, "profile_image": current_author.profile_image}
    if current_author.user == author.user:
        if request.method == 'POST':
            form = EditProfileForm(request.POST, initial=current_attributes)
            if form.is_valid():
                form.save(current_author)
            else:
                print(form.errors)
                form = EditProfileForm(initial=current_attributes)
        else:
            form = EditProfileForm(initial=current_attributes)
    current_author = get_current_author(request)
    author = get_object_or_404(Author, pk=author_id)
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

def view_requests(request,author_id):
    author = get_object_or_404(Author, pk=author_id)
    current_author = get_current_author(request)
    return render(request,'quickcomm/requests.html',{
        'current_author': current_author,
        'author':author
    })

@login_required
def send_follow_request(request,author_id):
    from_user=get_current_author(request)
    to_user=get_object_or_404(Author,pk=author_id)


    follow,create=follow_request.objects.get_or_create(from_user=from_user, to_user=to_user)
    if create:
        follow.save()
        # return render(request,'quickcomm/requests.html',{
        #     'current_user':from_user,
        #     'to_user':to_user,
        # })
        return HttpResponse('Friend request sent')
    else:
        return HttpResponse('Friend request was created already')
@login_required
def accept_request(request,author_id):
    target=get_current_author(request)
    follower=get_object_or_404(Author,pk=author_id)
    
    friend_request=follow_request.objects.get(from_user=follower, to_user=target)
    new_follower=Follow.objects.create(follower=follower,following=target)
                # if new_follower.is_bidirectional():
                    
                #     pass
    new_follower.save()
    friend_request.delete()
    return render(request, 'quickcomm/requests.html',{
                    'author':follower,
                    'current_author': target,
    })
@login_required
def decline_request(request,author_id):
    from_user=get_current_author(request)
    to_user=get_object_or_404(Author,pk=author_id)
    pass
                    
def view_author_posts(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    current_author = get_current_author(request)

    posts = Post.objects.filter(author=author)

    size = request.GET.get('size', '10')
    paginator = Paginator(posts, size)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'author': author,
        'page_obj': page_obj,
        'size': size,
        'current_author': current_author,
    }
    
    return render(request, 'quickcomm/posts.html', context)

