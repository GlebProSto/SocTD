from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import TodoPost, Comment, Profile, Repost,SubTask,TaskList

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label='Имя пользователя',
        max_length=150,
        help_text=''
    )
    email = forms.EmailField(
        required=True,
        label='Email'
    )
    password1 = forms.CharField(    
        label='Пароль',
        widget=forms.PasswordInput,
        help_text=''
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput,
        help_text=''
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class TodoPostForm(forms.ModelForm):    
    class Meta:
        model = TodoPost
        fields = ['content']

class RepostForm(forms.ModelForm):
    class Meta:
        model = Repost
        fields = []

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': 'Напишите комментарий...',
                'rows': 2,
                'maxlength': 280
            }),
        }
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields ="__all__"

class TaskListForm(forms.ModelForm):
    class Meta:
        model = TaskList
        fields = ['title', 'date']  # только эти поля из модели
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Название вашего дня...',
                'maxlength': 200
            }),
            'date': forms.DateInput(attrs={
                'type': 'date'  # для выбора даты
            })
        }
class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ['text']  # используй поле 'text' которое уже есть!
        widgets = {
            'text': forms.Textarea(attrs={
                'placeholder': 'Что вы планируете сделать?',
                'rows': 3,
                'maxlength': 280
            })
        }
        
