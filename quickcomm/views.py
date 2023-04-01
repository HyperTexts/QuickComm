import json
from dateutil import parser
from django.db.models import Q, Count
from django.template.defaulttags import register
from django.shortcuts import render, redirect
from django import template
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.core.paginator import Paginator
from quickcomm.external_host_deserializers import sync_comments, sync_post_likes, sync_posts, sync_authors
from quickcomm.forms import CreateImageForm, CreateMarkdownForm, CreatePlainTextForm, CreateLoginForm, CreateCommentForm, EditProfileForm
from quickcomm.models import Author, Host, Post, Like, Comment, RegistrationSettings, Inbox
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.template.loader import render_to_string

from quickcomm.models import Author, Follow, Inbox
from quickcomm.models import Author, Post, Like, Comment, RegistrationSettings, Inbox, CommentLike, Follow, FollowRequest
from django.contrib.auth.forms import UserCreationForm
from .external_requests import get_github_stream
from django.contrib import messages

# Create your views here.

# TODO fix sync_comments and sync_post_likes

def get_current_author(request):
    if request.user.is_authenticated:
        author = Author.objects.get(user_id = request.user.id)
    else:
        author = None
    return author

# This is a decorator that will be used to check if the user is logged in and
# redirect them to the login page if they are not. This will also check if there
# exists some author object for the user, and if not, direct the user to create
# one.
def author_required(func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                author = Author.objects.get(user=request.user)
            except Author.DoesNotExist:
                return render(request, 'quickcomm/noauthorerror.html')
            request.author = author
            return func(request, *args, **kwargs)
        else:
            return redirect('login')
    return wrapper

@author_required
def index(request):

    author = request.author
    inbox = list(Inbox.objects.filter(author=author).order_by('-added'))

    # Get the GitHub stream for all of the author's followed users
    following = [ follow.following for follow in Follow.objects.filter(follower=author) ]
    following.append(author)
    for follow in following:
        try:
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
        except:
            continue


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
        'current_author': author,
    }
    return render(request, 'quickcomm/index.html', context)


@author_required
def create_post(request):
    current_author = request.author
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



@author_required
def create_markdown(request):
    current_author = request.author
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

@author_required
def create_image(request):
    current_author = request.author
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
                username=request.POST['username'], password=request.POST['password'])
            if user is not None:
                auth_login(request, user)
                return redirect('/')
            else:
                form = CreateLoginForm()
    else:
        form = CreateLoginForm()
    return render(request, 'quickcomm/login.html', {'form': form})

@author_required
def post_view(request, post_id, author_id):
    current_author = request.author
    post = get_object_or_404(Post, pk=post_id)
    post_type = post.visibility
    if (post_type == 'FRIENDS'):
        post_comments = Comment.objects.filter(Q(author = current_author) | Q(author = post.author),post=post).order_by("-published")
    else:
        post_comments = Comment.objects.filter(post=post).order_by("-published")
    
    #dictionary with likes for each comment
    result = CommentLike.objects.values('comment__id').annotate(num_authors=Count('author', distinct=True))
    comment_dict = {}
    for item in result:
        comment_dict[item['comment__id']] = item['num_authors']

    #dictionary with each comment and the authors who liked it
    comment_like_list = CommentLike.objects.select_related('author').values('comment_id', 'author__id').annotate(count=Count('author'))
    comment_author_dict = {}
    for item in comment_like_list:
        comment_id = item['comment_id']
        author_id = item['author__id']
        if comment_id not in comment_author_dict:
            comment_author_dict[comment_id] = []
        comment_author_dict[comment_id].append(author_id)

    #dictionary with likes for each post
    result = Like.objects.values('post_id').annotate(num_authors=Count('author', distinct=True))
    post_dict = {}
    for item in result:
        post_dict[item['post_id']] = item['num_authors']

    #dictionary with each post and the authors who liked it
    post_like_list = Like.objects.select_related('author').values('post_id', 'author__id').annotate(count=Count('author'))
    post_author_dict = {}
    for item in post_like_list:
        post_id = item['post_id']
        author_id = item['author__id']
        if post_id not in post_author_dict:
            post_author_dict[post_id] = []
        post_author_dict[post_id].append(author_id)


    context = {"post": post, "post_comments":post_comments, "current_author": current_author,"comment_dict":comment_dict, "comment_author_dict":comment_author_dict,"post_dict":post_dict, "post_author_dict":post_author_dict}

    return render(request, "quickcomm/post.html", context)

@register.filter
def get_item(dictionary, key):
    val = dictionary.get(key)
    if val != None:
        return val
    else:
        return 0

@login_required
def post_like(request, post_id, author_id):
    objects = Post.objects.all()
    post = objects.get(pk=post_id)

    if request.user.is_authenticated:
        if request.method == 'POST':
            author = Author.objects.all().get(user=request.user)
            if Like.objects.filter(post__id=post_id, author=author).exists():
                postlike = Like.objects.filter(post__id=post_id, author=author)
                postlike.delete()
                is_liked = False
            else:
                postlike = Like.objects.create(post=post, author=author)
                is_liked = True
            like_key = f"post_like_{post_id}"
            request.session[like_key] = author == post.author

    like_count = Like.objects.filter(post__id=post_id).count()
    button = render_to_string("quickcomm/likebutton.html", {"is_liked": is_liked, "like_count": like_count }, request=request)
    return JsonResponse({"is_liked": button}) 
    # return redirect("post_view", post_id=post_id, author_id=author_id)

   
@login_required
def like_comment(request, post_id, author_id, comment_id):
    if request.method == 'POST':
        if request.user.is_authenticated:
            author = Author.objects.all().get(user=request.user)
            main_comment = get_object_or_404(Comment, id=comment_id)
            if CommentLike.objects.filter(comment__id=comment_id, author=author).exists():
                comment = CommentLike.objects.filter(comment__id=comment_id, author=author)
                comment.delete()

            else:
                comment = CommentLike.objects.create(comment=main_comment, author=author)
            comment_like_key = f"comment_like_{comment_id}"
            request.session[comment_like_key] = author == main_comment.author
    return redirect("post_view", post_id=post_id, author_id=author_id)

@author_required
def post_comment(request, post_id, author_id):
    post = Post.objects.get(pk=post_id)
    if request.method == 'POST':
        
        text = json.loads(request.body)["comment"]
        if text:
            author = request.author
            comment = Comment()
            comment.post = post
            comment.author = author
            comment.comment = text
            comment.save()
            
            new_comment = render_to_string("quickcomm/comments.html", { "comment": comment }, request=request)
            return JsonResponse({"comments": new_comment}) 
        # return redirect('post_comment', post_id=post_id, author_id=author_id)

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
            return redirect('/')
    else:
            form = UserCreationForm()
    context = {
            'form': UserCreationForm()
        }
    return render(request, 'quickcomm/register.html', context)

@author_required
def view_authors(request):
    current_author = request.author

    all_hosts = Host.objects.all()
    for host in all_hosts:
        # update the author list
        sync_authors(host)

    authors = Author.frontend_queryset().order_by('display_name')

    size = request.GET.get('size', '30')
    paginator = Paginator(authors, size)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'size': size,
        'current_author': current_author,
    }

    return render(request, 'quickcomm/authors.html', context)

@author_required
def view_profile(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    current_author = request.author
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
                messages.success(request, "Profile successfully changed!")
                form.save(current_author)
            else:
                form = EditProfileForm(initial=current_attributes)
        else:
            form = EditProfileForm(initial=current_attributes)
    current_author = request.author
    author = get_object_or_404(Author, pk=author_id)
    
    return render(request, 'quickcomm/profile.html', {
                    'author': author,
                    'current_author': current_author,
                    'form': form,
                    'is_following': current_author.is_following(author),
                    'is_requested': FollowRequest.objects.filter(from_user=current_author, to_user=author).exists(),
                    })

@author_required
def follow(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    current_author = request.author

    if author != current_author:
        # create or update the follow
        follow_obj, created_obj = Follow.objects.get_or_create(follower=current_author, following=author)


    return redirect('view_profile', author_id=author_id)

@author_required
def view_followers(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    current_author = request.author

    return render(request, 'quickcomm/followers.html', {
                    'author': author,
                    'current_author': current_author,
                    })
@author_required
def view_following(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    current_author = get_current_author(request)
    
    return render(request, 'quickcomm/following.html', {
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

    
    follow,create=FollowRequest.objects.get_or_create(from_user=from_user, to_user=to_user)
    if create:
        follow.save()
        messages.success(request, "Request to "+to_user.display_name+" sent successfully!")
        return redirect("view_profile", author_id=author_id)
    elif to_user.is_followed_by(from_user):
        messages.info(request, "Already following this author.")
        return redirect("view_profile", author_id=author_id)
    else:
        messages.error(request, "Could not process request.")
        return redirect("view_profile", author_id=author_id)
    
@login_required    
def accept_request(request,author_id):
    target=get_current_author(request)
    follower=get_object_or_404(Author,pk=author_id)
    
    friend_request=FollowRequest.objects.get(from_user=follower, to_user=target)
    new_follower=Follow.objects.create(follower=follower,following=target)
    new_follower.save()
    friend_request.delete()
    messages.success(request, "Request from "+follower.display_name+" accepted!")
    return redirect("view_requests", author_id=author_id)

@login_required
def unfriend(request,author_id):
    current_author=get_current_author(request)
    following=get_object_or_404(Author,pk=author_id)
    unfriended_person=Follow.objects.get(follower=current_author,following=following)
    unfriended_person.delete()

    messages.success(request, "Unfollowed "+following.display_name)
    return redirect("view_profile", author_id=author_id)

@login_required
def decline_request(request,author_id):
    from_user=get_current_author(request)
    to_user=get_object_or_404(Author,pk=author_id)
    pass

@author_required            
def view_author_posts(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    current_author = request.author

    if author.is_remote and not author.is_temporary:
        sync_posts(author)

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

def share_post(request,author_id):
    author=get_object_or_404(Author,pk=author_id)
    current_author=get_current_author(request)

    posts = Post.objects.filter(author=author)
    
    size=request.GET.get('size','10')
    pass

