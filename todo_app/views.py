from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import TodoPost, Comment, Profile, Repost
from .forms import CustomUserCreationForm, TodoPostForm, CommentForm, ProfileForm, RepostForm

def home(request):
    posts = TodoPost.objects.all().order_by('-created_at')
    if request.user.is_authenticated:
        form = TodoPostForm()
        return render(request, 'home.html', {
            'form': form,
            'posts': posts
        })
    else:
        return render(request, 'home.html',{
            'posts' : posts
        }) 

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def profile(request):
    section = request.GET.get('section', 'posts')
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if section == 'posts':
        posts = TodoPost.objects.filter(author=request.user).order_by('-created_at')
    elif section == 'repost':
        reposted_posts = TodoPost.objects.filter(
            repost__user=request.user
        ).order_by('-repost__created_at')
        
        own_posts = TodoPost.objects.filter(author=request.user)
        
        posts = (reposted_posts | own_posts).distinct().order_by('-created_at')
        posts = TodoPost.objects.filter(author=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile) 
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'profile.html', {
        'form': form, 
        'profile': profile,
        'posts': posts,
        'section': section,
    })

@login_required
def create_post(request):
    if request.method == 'POST':
        form = TodoPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('home')
    return redirect('home')

@login_required
def like_post(request, post_id):
    post = get_object_or_404(TodoPost, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'likes_count': post.likes.count()})

@login_required
def repost_post(request, post_id):
    post = get_object_or_404(TodoPost, id=post_id)
    if Repost.objects.filter(user=request.user, post=post).exists():
        Repost.objects.filter(user=request.user, post=post).delete()
        reposted = False
    else:
        Repost.objects.create(user=request.user, post=post)
        reposted = True
    
    return JsonResponse({
        'reposted': reposted, 
        'reposts_count': post.reposts.count()
    })

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(TodoPost, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('home')
    return redirect('home')