from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.utils import timezone

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


from .models import (
    UserProfile, Team, TeamMembership, Project, Document, 
    Version, PullRequest, Review, WorkItem, Comment, Activity
)
from .forms import (
    UserRegistrationForm, UserProfileForm, TeamForm, ProjectForm,
    DocumentForm, VersionUploadForm, PullRequestForm, ReviewForm,
    WorkItemForm, CommentForm
)
from .utils.file_handlers import get_file_type, get_file_info, format_file_size
from .utils.comparison import compare_documents, get_diff_stats


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to DocTrack! Your account has been created.')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user
    
    projects = Project.objects.filter(
        Q(owner=user) | Q(collaborators=user)
    ).distinct().order_by('-updated_at')[:5]
    
    open_prs = PullRequest.objects.filter(
        Q(created_by=user) | Q(reviewers=user),
        status='open'
    ).distinct().order_by('-created_at')[:5]
    
    my_work_items = WorkItem.objects.filter(
        assigned_to=user,
        status__in=['open', 'in_progress']
    ).order_by('-created_at')[:5]
    
    recent_activities = Activity.objects.filter(
        Q(user=user) | Q(project__owner=user) | Q(project__collaborators=user)
    ).distinct().order_by('-created_at')[:10]
    
    stats = {
        'total_projects': Project.objects.filter(Q(owner=user) | Q(collaborators=user)).distinct().count(),
        'open_prs': PullRequest.objects.filter(Q(created_by=user) | Q(reviewers=user), status='open').distinct().count(),
        'pending_reviews': PullRequest.objects.filter(reviewers=user, status='open').count(),
        'my_tasks': WorkItem.objects.filter(assigned_to=user, status__in=['open', 'in_progress']).count(),
    }
    
    context = {
        'projects': projects,
        'open_prs': open_prs,
        'my_work_items': my_work_items,
        'recent_activities': recent_activities,
        'stats': stats,
    }
    return render(request, 'dashboard.html', context)


@login_required
def profile(request):
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    return render(request, 'accounts/profile.html', {'form': form, 'profile': user_profile})


@login_required
def project_list(request):
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(collaborators=request.user) | Q(is_public=True)
    ).distinct().annotate(
        doc_count=Count('documents'),
        pr_count=Count('pull_requests', filter=Q(pull_requests__status='open'))
    ).order_by('-updated_at')
    
    paginator = Paginator(projects, 12)
    page = request.GET.get('page')
    projects = paginator.get_page(page)
    
    return render(request, 'projects/list.html', {'projects': projects})


@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, user=request.user)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            Activity.objects.create(
                user=request.user,
                action='created',
                target_type='Project',
                target_id=project.id,
                target_name=project.name,
                project=project
            )
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(user=request.user)
    return render(request, 'projects/create.html', {'form': form})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if not (project.is_public or project.owner == request.user or request.user in project.collaborators.all()):
        messages.error(request, 'You do not have access to this project.')
        return redirect('project_list')
    
    documents = project.documents.annotate(
        version_count=Count('versions')
    ).order_by('-updated_at')
    
    open_prs = project.pull_requests.filter(status='open').order_by('-created_at')[:5]
    work_items = project.work_items.filter(status__in=['open', 'in_progress']).order_by('-created_at')[:5]
    activities = project.activities.order_by('-created_at')[:10]
    
    context = {
        'project': project,
        'documents': documents,
        'open_prs': open_prs,
        'work_items': work_items,
        'activities': activities,
    }
    return render(request, 'projects/detail.html', context)


@login_required
def project_settings(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project settings updated.')
            return redirect('project_detail', pk=pk)
    else:
        form = ProjectForm(instance=project, user=request.user)
    
    collaborators = project.collaborators.all()
    all_users = User.objects.exclude(pk=request.user.pk).exclude(pk__in=collaborators)
    
    context = {
        'project': project,
        'form': form,
        'collaborators': collaborators,
        'all_users': all_users,
    }
    return render(request, 'projects/settings.html', context)


@login_required
@require_POST
def project_add_collaborator(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    user_id = request.POST.get('user_id')
    
    if user_id:
        user = get_object_or_404(User, pk=user_id)
        project.collaborators.add(user)
        messages.success(request, f'{user.username} added as collaborator.')
    
    return redirect('project_settings', pk=pk)


@login_required
@require_POST
def project_remove_collaborator(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    user = get_object_or_404(User, pk=user_id)
    project.collaborators.remove(user)
    messages.success(request, f'{user.username} removed from project.')
    return redirect('project_settings', pk=pk)


@login_required
def document_upload(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    
    if not (project.owner == request.user or request.user in project.collaborators.all()):
        messages.error(request, 'You do not have permission to upload documents.')
        return redirect('project_detail', pk=project_pk)
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            file_type = get_file_type(file.name)
            
            document = Document.objects.create(
                name=form.cleaned_data['name'],
                description=form.cleaned_data.get('description', ''),
                project=project,
                file_type=file_type,
                created_by=request.user
            )
            
            Version.objects.create(
                document=document,
                version_number=1,
                file=file,
                change_summary='Initial version',
                uploaded_by=request.user
            )
            
            Activity.objects.create(
                user=request.user,
                action='uploaded',
                target_type='Document',
                target_id=document.id,
                target_name=document.name,
                project=project
            )
            
            messages.success(request, f'Document "{document.name}" uploaded successfully!')
            return redirect('document_detail', pk=document.pk)
    else:
        form = DocumentForm()
    
    return render(request, 'documents/upload.html', {'form': form, 'project': project})


@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    project = document.project
    
    if not (project.is_public or project.owner == request.user or request.user in project.collaborators.all()):
        messages.error(request, 'You do not have access to this document.')
        return redirect('project_list')
    
    versions = document.versions.all()
    latest_version = versions.first()
    comments = document.comments.filter(parent__isnull=True).order_by('-created_at')
    pull_requests = document.pull_requests.order_by('-created_at')[:5]
    
    file_info = None
    if latest_version and latest_version.file:
        try:
            file_info = get_file_info(latest_version.file.path, document.file_type)
        except Exception:
            file_info = {'size_formatted': format_file_size(latest_version.file_size)}
    
    context = {
        'document': document,
        'project': project,
        'versions': versions,
        'latest_version': latest_version,
        'comments': comments,
        'pull_requests': pull_requests,
        'file_info': file_info,
        'comment_form': CommentForm(),
    }
    return render(request, 'documents/detail.html', context)


@login_required
def document_upload_version(request, pk):
    document = get_object_or_404(Document, pk=pk)
    project = document.project
    
    if not (project.owner == request.user or request.user in project.collaborators.all()):
        messages.error(request, 'You do not have permission to upload versions.')
        return redirect('document_detail', pk=pk)
    
    if request.method == 'POST':
        form = VersionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            
            last_version = document.versions.order_by('-version_number').first()
            new_version_number = (last_version.version_number + 1) if last_version else 1
            
            version = Version.objects.create(
                document=document,
                version_number=new_version_number,
                file=file,
                change_summary=form.cleaned_data.get('change_summary', ''),
                uploaded_by=request.user
            )
            
            document.updated_at = timezone.now()
            document.save()
            
            Activity.objects.create(
                user=request.user,
                action='uploaded',
                target_type='Version',
                target_id=version.id,
                target_name=f'{document.name} v{version.version_number}',
                project=project
            )
            
            messages.success(request, f'Version {version.version_number} uploaded successfully!')
            return redirect('document_detail', pk=pk)
    else:
        form = VersionUploadForm()
    
    return render(request, 'documents/upload_version.html', {
        'form': form,
        'document': document,
        'project': project
    })


@login_required
def document_compare(request, pk):
    document = get_object_or_404(Document, pk=pk)
    project = document.project
    
    if not (project.is_public or project.owner == request.user or request.user in project.collaborators.all()):
        messages.error(request, 'You do not have access to this document.')
        return redirect('project_list')
    
    versions = document.versions.all()
    
    v1_id = request.GET.get('v1')
    v2_id = request.GET.get('v2')
    
    comparison = None
    version1 = None
    version2 = None
    
    if v1_id and v2_id:
        version1 = get_object_or_404(Version, pk=v1_id, document=document)
        version2 = get_object_or_404(Version, pk=v2_id, document=document)
        
        try:
            comparison = compare_documents(
                version1.file.path,
                version2.file.path,
                document.file_type
            )
        except Exception as e:
            comparison = {'error': str(e), 'can_compare': False}
    
    context = {
        'document': document,
        'project': project,
        'versions': versions,
        'version1': version1,
        'version2': version2,
        'comparison': comparison,
    }
    return render(request, 'documents/compare.html', context)


@login_required
def pull_request_list(request):
    prs = PullRequest.objects.filter(
        Q(created_by=request.user) | Q(reviewers=request.user) | 
        Q(project__owner=request.user) | Q(project__collaborators=request.user)
    ).distinct().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        prs = prs.filter(status=status_filter)
    
    paginator = Paginator(prs, 10)
    page = request.GET.get('page')
    prs = paginator.get_page(page)
    
    return render(request, 'reviews/pr_list.html', {'pull_requests': prs})


@login_required
def pull_request_create(request, document_pk):
    document = get_object_or_404(Document, pk=document_pk)
    project = document.project
    
    if not (project.owner == request.user or request.user in project.collaborators.all()):
        messages.error(request, 'You do not have permission to create pull requests.')
        return redirect('document_detail', pk=document_pk)
    
    versions = document.versions.all()
    if versions.count() < 1:
        messages.error(request, 'You need at least one version to create a pull request.')
        return redirect('document_detail', pk=document_pk)
    
    if request.method == 'POST':
        form = PullRequestForm(request.POST)
        source_version_id = request.POST.get('source_version')
        target_version_id = request.POST.get('target_version')
        
        if form.is_valid() and source_version_id:
            source_version = get_object_or_404(Version, pk=source_version_id, document=document)
            target_version = None
            if target_version_id:
                target_version = get_object_or_404(Version, pk=target_version_id, document=document)
            
            pr = PullRequest.objects.create(
                title=form.cleaned_data['title'],
                description=form.cleaned_data.get('description', ''),
                project=project,
                document=document,
                source_version=source_version,
                target_version=target_version,
                created_by=request.user
            )
            
            Activity.objects.create(
                user=request.user,
                action='created',
                target_type='PullRequest',
                target_id=pr.id,
                target_name=pr.title,
                project=project
            )
            
            messages.success(request, f'Pull request "{pr.title}" created successfully!')
            return redirect('pull_request_detail', pk=pr.pk)
    else:
        form = PullRequestForm()
    
    context = {
        'form': form,
        'document': document,
        'project': project,
        'versions': versions,
    }
    return render(request, 'reviews/pr_create.html', context)


@login_required
def pull_request_detail(request, pk):
    pr = get_object_or_404(PullRequest, pk=pk)
    project = pr.project
    
    if not (project.is_public or project.owner == request.user or 
            request.user in project.collaborators.all() or
            request.user in pr.reviewers.all()):
        messages.error(request, 'You do not have access to this pull request.')
        return redirect('pull_request_list')
    
    comparison = None
    if pr.target_version:
        try:
            comparison = compare_documents(
                pr.target_version.file.path,
                pr.source_version.file.path,
                pr.document.file_type
            )
        except Exception as e:
            comparison = {'error': str(e), 'can_compare': False}
    
    reviews = pr.reviews.order_by('-created_at')
    comments = pr.comments.filter(parent__isnull=True).order_by('-created_at')
    
    can_review = (
        pr.status == 'open' and 
        request.user != pr.created_by and
        (project.owner == request.user or request.user in project.collaborators.all() or request.user in pr.reviewers.all())
    )
    
    can_merge = (
        pr.status == 'approved' and
        (project.owner == request.user or request.user == pr.created_by)
    )
    
    context = {
        'pr': pr,
        'project': project,
        'comparison': comparison,
        'reviews': reviews,
        'comments': comments,
        'can_review': can_review,
        'can_merge': can_merge,
        'review_form': ReviewForm(),
        'comment_form': CommentForm(),
    }
    return render(request, 'reviews/pr_detail.html', context)


@login_required
@require_POST
def pull_request_review(request, pk):
    pr = get_object_or_404(PullRequest, pk=pk)
    project = pr.project
    
    if not (project.owner == request.user or request.user in project.collaborators.all() or request.user in pr.reviewers.all()):
        messages.error(request, 'You do not have permission to review this pull request.')
        return redirect('pull_request_detail', pk=pk)
    
    form = ReviewForm(request.POST)
    if form.is_valid():
        status = form.cleaned_data['status']
        comment = form.cleaned_data.get('comment', '')
        
        if status == 'approved':
            pr.approve(request.user)
            Activity.objects.create(
                user=request.user,
                action='approved',
                target_type='PullRequest',
                target_id=pr.id,
                target_name=pr.title,
                project=project
            )
            messages.success(request, 'Pull request approved!')
        else:
            pr.reject(request.user, comment)
            Activity.objects.create(
                user=request.user,
                action='rejected',
                target_type='PullRequest',
                target_id=pr.id,
                target_name=pr.title,
                project=project
            )
            messages.info(request, 'Changes requested on pull request.')
    
    return redirect('pull_request_detail', pk=pk)


@login_required
@require_POST
def pull_request_merge(request, pk):
    pr = get_object_or_404(PullRequest, pk=pk)
    project = pr.project
    
    if pr.status != 'approved':
        messages.error(request, 'Pull request must be approved before merging.')
        return redirect('pull_request_detail', pk=pk)
    
    if not (project.owner == request.user or request.user == pr.created_by):
        messages.error(request, 'You do not have permission to merge this pull request.')
        return redirect('pull_request_detail', pk=pk)
    
    pr.merge(request.user)
    
    Activity.objects.create(
        user=request.user,
        action='merged',
        target_type='PullRequest',
        target_id=pr.id,
        target_name=pr.title,
        project=project
    )
    
    messages.success(request, 'Pull request merged successfully!')
    return redirect('pull_request_detail', pk=pk)


@login_required
def work_item_list(request, project_pk=None):
    if project_pk:
        project = get_object_or_404(Project, pk=project_pk)
        work_items = project.work_items.all()
    else:
        work_items = WorkItem.objects.filter(
            Q(assigned_to=request.user) | Q(created_by=request.user) |
            Q(project__owner=request.user) | Q(project__collaborators=request.user)
        ).distinct()
    
    status_filter = request.GET.get('status')
    if status_filter:
        work_items = work_items.filter(status=status_filter)
    
    work_items = work_items.order_by('-created_at')
    
    paginator = Paginator(work_items, 10)
    page = request.GET.get('page')
    work_items = paginator.get_page(page)
    
    context = {
        'work_items': work_items,
        'project': project if project_pk else None,
    }
    return render(request, 'workitems/list.html', context)


@login_required
def work_item_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    
    if not (project.owner == request.user or request.user in project.collaborators.all()):
        messages.error(request, 'You do not have permission to create work items.')
        return redirect('project_detail', pk=project_pk)
    
    if request.method == 'POST':
        form = WorkItemForm(request.POST, project=project)
        if form.is_valid():
            work_item = form.save(commit=False)
            work_item.project = project
            work_item.created_by = request.user
            work_item.save()
            
            Activity.objects.create(
                user=request.user,
                action='created',
                target_type='WorkItem',
                target_id=work_item.id,
                target_name=work_item.title,
                project=project
            )
            
            messages.success(request, f'Work item "{work_item.title}" created!')
            return redirect('work_item_detail', pk=work_item.pk)
    else:
        form = WorkItemForm(project=project)
    
    return render(request, 'workitems/create.html', {'form': form, 'project': project})


@login_required
def work_item_detail(request, pk):
    work_item = get_object_or_404(WorkItem, pk=pk)
    project = work_item.project
    
    if not (project.is_public or project.owner == request.user or request.user in project.collaborators.all()):
        messages.error(request, 'You do not have access to this work item.')
        return redirect('project_list')
    
    comments = work_item.comments.filter(parent__isnull=True).order_by('-created_at')
    
    context = {
        'work_item': work_item,
        'project': project,
        'comments': comments,
        'comment_form': CommentForm(),
    }
    return render(request, 'workitems/detail.html', context)


@login_required
@require_POST
def work_item_update_status(request, pk):
    work_item = get_object_or_404(WorkItem, pk=pk)
    project = work_item.project
    
    if not (project.owner == request.user or request.user in project.collaborators.all()):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    new_status = request.POST.get('status')
    if new_status in dict(WorkItem.STATUS_CHOICES):
        work_item.status = new_status
        work_item.save()
        
        Activity.objects.create(
            user=request.user,
            action='updated',
            target_type='WorkItem',
            target_id=work_item.id,
            target_name=work_item.title,
            project=project
        )
        
        return JsonResponse({'success': True, 'status': new_status})
    
    return JsonResponse({'error': 'Invalid status'}, status=400)


@login_required
@require_POST
def add_comment(request):
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        
        document_id = request.POST.get('document_id')
        pr_id = request.POST.get('pr_id')
        work_item_id = request.POST.get('work_item_id')
        parent_id = request.POST.get('parent_id')
        
        if document_id:
            comment.document = get_object_or_404(Document, pk=document_id)
            project = comment.document.project
        elif pr_id:
            comment.pull_request = get_object_or_404(PullRequest, pk=pr_id)
            project = comment.pull_request.project
        elif work_item_id:
            comment.work_item = get_object_or_404(WorkItem, pk=work_item_id)
            project = comment.work_item.project
        
        if parent_id:
            comment.parent = get_object_or_404(Comment, pk=parent_id)
        
        comment.save()
        
        Activity.objects.create(
            user=request.user,
            action='commented',
            target_type='Comment',
            target_id=comment.id,
            target_name=comment.content[:50],
            project=project
        )
        
        messages.success(request, 'Comment added.')
    
    redirect_url = request.POST.get('redirect_url', '/')
    return redirect(redirect_url)


@login_required
def team_list(request):
    teams = Team.objects.filter(members=request.user).order_by('-created_at')
    return render(request, 'teams/list.html', {'teams': teams})


@login_required
def team_create(request):
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.created_by = request.user
            team.save()
            TeamMembership.objects.create(user=request.user, team=team, role='owner')
            messages.success(request, f'Team "{team.name}" created!')
            return redirect('team_detail', pk=team.pk)
    else:
        form = TeamForm()
    return render(request, 'teams/create.html', {'form': form})


@login_required
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    
    if request.user not in team.members.all():
        messages.error(request, 'You are not a member of this team.')
        return redirect('team_list')
    
    memberships = TeamMembership.objects.filter(team=team).select_related('user')
    projects = team.projects.all()
    
    context = {
        'team': team,
        'memberships': memberships,
        'projects': projects,
    }
    return render(request, 'teams/detail.html', context)


def search(request):
    query = request.GET.get('q', '')
    
    if not query:
        return render(request, 'search.html', {'query': query})
    
    projects = Project.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query),
        Q(owner=request.user) | Q(collaborators=request.user) | Q(is_public=True)
    ).distinct()[:10]
    
    documents = Document.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query),
        Q(project__owner=request.user) | Q(project__collaborators=request.user) | Q(project__is_public=True)
    ).distinct()[:10]
    
    prs = PullRequest.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        Q(project__owner=request.user) | Q(project__collaborators=request.user)
    ).distinct()[:10]
    
    context = {
        'query': query,
        'projects': projects,
        'documents': documents,
        'pull_requests': prs,
    }
    return render(request, 'search.html', context)

@login_required
def logout_view(request):
    logout(request)           # clears the session
    return redirect('login')  # send user to login page
