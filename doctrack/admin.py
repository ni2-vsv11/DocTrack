from django.contrib import admin
from .models import (UserProfile, Team, TeamMembership, Project, Document,
                     Version, PullRequest, Review, WorkItem, Comment, Activity)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    search_fields = ['name']


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role', 'joined_at']
    list_filter = ['role']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'status', 'is_public', 'created_at']
    list_filter = ['status', 'is_public']
    search_fields = ['name', 'description']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'file_type', 'created_by', 'created_at']
    list_filter = ['file_type']
    search_fields = ['name', 'description']


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ['document', 'version_number', 'uploaded_by', 'created_at']
    list_filter = ['created_at']


@admin.register(PullRequest)
class PullRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'status', 'created_by', 'created_at']
    list_filter = ['status']
    search_fields = ['title', 'description']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['pull_request', 'reviewer', 'status', 'created_at']
    list_filter = ['status']


@admin.register(WorkItem)
class WorkItemAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'project', 'item_type', 'priority', 'status', 'assigned_to'
    ]
    list_filter = ['item_type', 'priority', 'status']
    search_fields = ['title', 'description']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'content', 'created_at']
    list_filter = ['created_at']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'action', 'target_type', 'target_name', 'created_at'
    ]
    list_filter = ['action', 'target_type']
