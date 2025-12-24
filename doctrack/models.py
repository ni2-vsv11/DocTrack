from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os
import uuid


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('reviewer', 'Reviewer'),
        ('contributor', 'Contributor'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='contributor')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def can_create_project(self):
        return self.role in ['admin', 'manager']
    
    def can_approve_pr(self):
        return self.role in ['admin', 'manager', 'reviewer']
    
    def can_upload_document(self):
        return self.role in ['admin', 'manager', 'reviewer', 'contributor']


class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, through='TeamMembership', related_name='teams')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_teams')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class TeamMembership(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'team']


class Project(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('completed', 'Completed'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    collaborators = models.ManyToManyField(User, related_name='collaborated_projects', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_document_count(self):
        return self.documents.count()
    
    def get_open_pr_count(self):
        return self.pull_requests.filter(status='open').count()


def document_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('documents', str(instance.project.id), unique_filename)


class Document(models.Model):
    TYPE_CHOICES = [
        ('pdf', 'PDF Document'),
        ('word', 'Word Document'),
        ('image', 'Image'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    file_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_latest_version(self):
        return self.versions.order_by('-version_number').first()
    
    def get_version_count(self):
        return self.versions.count()


def version_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('versions', str(instance.document.project.id), str(instance.document.id), unique_filename)


class Version(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField(default=1)
    file = models.FileField(upload_to=version_upload_path)
    file_size = models.PositiveIntegerField(default=0)
    change_summary = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_versions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ['document', 'version_number']
    
    def __str__(self):
        return f"{self.document.name} v{self.version_number}"
    
    def save(self, *args, **kwargs):
        if not self.version_number:
            last_version = Version.objects.filter(document=self.document).order_by('-version_number').first()
            self.version_number = (last_version.version_number + 1) if last_version else 1
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class PullRequest(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('merged', 'Merged'),
        ('closed', 'Closed'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pull_requests')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='pull_requests')
    source_version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='pr_as_source')
    target_version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='pr_as_target', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_prs')
    reviewers = models.ManyToManyField(User, related_name='assigned_prs', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    merged_at = models.DateTimeField(null=True, blank=True)
    merged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='merged_prs')
    
    def __str__(self):
        return self.title
    
    def approve(self, user):
        self.status = 'approved'
        self.save()
        Review.objects.create(
            pull_request=self,
            reviewer=user,
            status='approved',
            comment='Approved'
        )
    
    def reject(self, user, comment=''):
        self.status = 'rejected'
        self.save()
        Review.objects.create(
            pull_request=self,
            reviewer=user,
            status='rejected',
            comment=comment
        )
    
    def merge(self, user):
        self.status = 'merged'
        self.merged_at = timezone.now()
        self.merged_by = user
        self.save()


class Review(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Changes Requested'),
    ]
    
    pull_request = models.ForeignKey(PullRequest, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review by {self.reviewer.username} on {self.pull_request.title}"


class WorkItem(models.Model):
    TYPE_CHOICES = [
        ('task', 'Task'),
        ('issue', 'Issue'),
        ('bug', 'Bug'),
        ('feature', 'Feature Request'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('done', 'Done'),
        ('closed', 'Closed'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='task')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='work_items')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='work_items', null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_work_items')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_work_items')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title


class Comment(models.Model):
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    pull_request = models.ForeignKey(PullRequest, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    work_item = models.ForeignKey(WorkItem, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username}"


class Activity(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('uploaded', 'Uploaded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('merged', 'Merged'),
        ('commented', 'Commented'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=50)
    target_id = models.PositiveIntegerField()
    target_name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.user.username} {self.action} {self.target_name}"
