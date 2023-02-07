from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from quickcomm.forms import CreateMarkdownForm, CreatePlainTextForm
from quickcomm.models import Author, Post

# Create your views here.

def index(request):
    context = {
        'posts': Post.objects.all()
    }
    return render(request, 'quickcomm/index.html', context)

