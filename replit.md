# DocTrack - Document Version Control System

## Overview
DocTrack is a GitHub-like document version control system designed for non-technical business teams. It enables users to manage document versions, create pull requests, review changes, and collaborate on files using visual interfaces instead of technical commands.

## Goals
- Provide document version control accessible to marketers, lawyers, designers, and other non-technical users
- Offer visual diff comparison between document versions
- Enable pull request workflows for document approval
- Support team collaboration with role-based access control

## Current State
The application is fully functional with:
- User authentication with 5 roles (Admin, Manager, Reviewer, Contributor, Viewer)
- Project and document management with drag-and-drop uploads
- Document versioning with version history
- Pull request workflow with review/approve/reject/merge
- Side-by-side visual diff comparison
- Work item tracking (tasks, bugs, features, issues)
- Team management and collaboration
- Search functionality
- Activity tracking

## Project Structure
```
doctrack_project/       # Django project settings
doctrack/               # Main application
  models.py            # Data models
  views.py             # View logic
  forms.py             # Form definitions
  urls.py              # URL patterns
  utils/               # Utilities
    file_handlers.py   # File upload/metadata
    comparison.py      # Diff comparison logic
templates/             # HTML templates
  base.html            # Base template with Tailwind CSS
  auth/                # Authentication pages
  projects/            # Project management
  documents/           # Document views
  reviews/             # Pull request views
  workitems/           # Task tracking
  teams/               # Team management
static/                # Static assets
media/                 # Uploaded files
```

## Technology Stack
- **Backend**: Django 5.2.8 with Python
- **Database**: SQLite (development)
- **Frontend**: Tailwind CSS, HTMX, Font Awesome icons
- **File Processing**: PyPDF2, python-docx, Pillow

## Key Models
- **UserProfile**: Extended user with roles
- **Team**: User groups for collaboration
- **Project**: Container for documents
- **Document**: File with metadata and file type
- **Version**: Document version with file and change summary
- **PullRequest**: Review request for document changes
- **Review**: Approval/rejection of pull requests
- **WorkItem**: Tasks, bugs, issues tracking
- **Comment**: Discussion on documents/PRs/work items
- **Activity**: Action logging

## User Roles
1. **Admin**: Full access, manage users and teams
2. **Manager**: Manage projects, approve merges
3. **Reviewer**: Review and approve pull requests
4. **Contributor**: Upload documents and create versions
5. **Viewer**: Read-only access

## Development
- Server runs on port 5000
- Run with: `python manage.py runserver 0.0.0.0:5000`

## Recent Changes
- November 29, 2025: Initial complete implementation
  - Full authentication system
  - Project, document, and version management
  - Pull request workflow
  - Visual diff comparison
  - Work item tracking
  - Team collaboration
  - Responsive UI with Tailwind CSS
