from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    UserProfile, Team, Project, Document, Version, 
    PullRequest, WorkItem, Comment
)


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, initial='contributor')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role']
            )
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role', 'avatar', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'team', 'is_public']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['team'].queryset = Team.objects.filter(members=user)
            self.fields['team'].required = False


class DocumentForm(forms.ModelForm):
    file = forms.FileField(required=True)
    
    class Meta:
        model = Document
        fields = ['name', 'description', 'file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = file.name.split('.')[-1].lower()
            allowed_extensions = ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'gif', 'bmp']
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f'File type .{ext} is not supported. Allowed types: {", ".join(allowed_extensions)}'
                )
            if file.size > 52428800:
                raise forms.ValidationError('File size must be less than 50MB.')
        return file


class VersionUploadForm(forms.Form):
    file = forms.FileField(required=True)
    change_summary = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        help_text='Describe what changed in this version'
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = file.name.split('.')[-1].lower()
            allowed_extensions = ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'gif', 'bmp']
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f'File type .{ext} is not supported. Allowed types: {", ".join(allowed_extensions)}'
                )
            if file.size > 52428800:
                raise forms.ValidationError('File size must be less than 50MB.')
        return file


class PullRequestForm(forms.ModelForm):
    class Meta:
        model = PullRequest
        fields = ['title', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ReviewForm(forms.Form):
    STATUS_CHOICES = [
        ('approved', 'Approve'),
        ('rejected', 'Request Changes'),
    ]
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.RadioSelect)
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text='Add your feedback or comments'
    )


class WorkItemForm(forms.ModelForm):
    class Meta:
        model = WorkItem
        fields = ['title', 'description', 'item_type', 'priority', 'status', 'assigned_to', 'due_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            collaborators = project.collaborators.all()
            owner = project.owner
            from django.db.models import Q
            users = User.objects.filter(Q(id=owner.id) | Q(id__in=collaborators))
            self.fields['assigned_to'].queryset = users


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write a comment...'}),
        }
