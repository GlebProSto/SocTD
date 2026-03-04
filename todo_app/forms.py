from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

# Убедитесь, что эти модели есть в todo_app/models.py
from .models import (
    TodoPost,
    Comment,
    Profile,
    Repost,
    SubTask,
    TaskList,
    Message,
)

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")


class TodoPostForm(forms.ModelForm):
    # only content should be editable by user
    content = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 3,
        'maxlength': 280,
        'placeholder': 'Что вы планируете сделать?'
    }))

    class Meta:
        model = TodoPost
        fields = ['content']


class CommentForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 2,
        'maxlength': 280,
        'placeholder': 'Напишите комментарий...'
    }))

    class Meta:
        model = Comment
        fields = ['content']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'О себе...'})
        }


class RepostForm(forms.ModelForm):
    class Meta:
        model = Repost
        fields = ['post']  # user filled automatically if ever used


class SubTaskForm(forms.ModelForm):
    text = forms.CharField(widget=forms.TextInput(attrs={'maxlength': 280, 'placeholder': 'Добавить подзадачу'}))
    class Meta:
        model = SubTask
        fields = ['text']


class TaskListForm(forms.ModelForm):
    # use HTML5 date picker widget for convenience
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'required': 'required'}))
    title = forms.CharField(widget=forms.TextInput(attrs={'required': 'required'}))

    class Meta:
        model = TaskList
        fields = ['title', 'date']


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = "__all__"


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = "__all__"


# form used in the user search page
class UserSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Поиск пользователей',
            'class': 'search-input'
        })
    )

