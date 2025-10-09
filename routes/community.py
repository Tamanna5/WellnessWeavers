"""
Community routes for WellnessWeavers
Support groups, forums, and community features
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json

from models.community import SupportGroup, GroupMembership, GroupPost
from models.user import User
from database import db

community_bp = Blueprint('community', __name__)

@community_bp.route('/')
@login_required
def index():
    """Community homepage"""
    # Get user's groups
    user_groups = SupportGroup.query.join(GroupMembership).filter(
        GroupMembership.user_id == current_user.id,
        GroupMembership.status == 'active'
    ).all()
    
    # Get recommended groups
    recommended_groups = SupportGroup.query.filter(
        SupportGroup.is_public == True,
        SupportGroup.status == 'active'
    ).limit(6).all()
    
    # Get recent posts from user's groups
    recent_posts = GroupPost.query.join(GroupMembership).filter(
        GroupMembership.user_id == current_user.id,
        GroupMembership.status == 'active'
    ).order_by(GroupPost.created_at.desc()).limit(10).all()
    
    return render_template('community/index.html',
                         user_groups=user_groups,
                         recommended_groups=recommended_groups,
                         recent_posts=recent_posts)

@community_bp.route('/groups')
@login_required
def groups():
    """Browse support groups"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    
    # Build query
    query = SupportGroup.query.filter(
        SupportGroup.is_public == True,
        SupportGroup.status == 'active'
    )
    
    if category != 'all':
        query = query.filter(SupportGroup.category == category)
    
    if search:
        query = query.filter(
            SupportGroup.name.contains(search) |
            SupportGroup.description.contains(search)
        )
    
    groups = query.paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Get categories for filter
    categories = db.session.query(SupportGroup.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('community/groups.html',
                         groups=groups,
                         categories=categories,
                         current_category=category,
                         search=search)

@community_bp.route('/groups/<int:group_id>')
@login_required
def group_detail(group_id):
    """View specific support group"""
    group = SupportGroup.query.get_or_404(group_id)
    
    # Check if user is member
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    
    # Get recent posts
    posts = GroupPost.query.filter_by(group_id=group_id)\
                          .order_by(GroupPost.created_at.desc())\
                          .limit(20).all()
    
    # Get group members
    members = User.query.join(GroupMembership).filter(
        GroupMembership.group_id == group_id,
        GroupMembership.status == 'active'
    ).limit(10).all()
    
    return render_template('community/group_detail.html',
                         group=group,
                         membership=membership,
                         posts=posts,
                         members=members)

@community_bp.route('/groups/<int:group_id>/join', methods=['POST'])
@login_required
def join_group(group_id):
    """Join a support group"""
    group = SupportGroup.query.get_or_404(group_id)
    
    # Check if already a member
    existing_membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    
    if existing_membership:
        if existing_membership.status == 'active':
            flash('You are already a member of this group.', 'info')
        elif existing_membership.status == 'pending':
            flash('Your membership request is pending approval.', 'info')
        else:
            # Reactivate membership
            existing_membership.status = 'active'
            existing_membership.joined_at = datetime.utcnow()
            db.session.commit()
            flash('Welcome back to the group!', 'success')
    else:
        # Create new membership
        membership = GroupMembership(
            user_id=current_user.id,
            group_id=group_id,
            status='active' if group.is_public else 'pending',
            joined_at=datetime.utcnow()
        )
        db.session.add(membership)
        db.session.commit()
        
        if group.is_public:
            flash('Successfully joined the group!', 'success')
        else:
            flash('Membership request sent for approval.', 'info')
    
    return redirect(url_for('community.group_detail', group_id=group_id))

@community_bp.route('/groups/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    """Leave a support group"""
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    
    if membership:
        membership.status = 'inactive'
        membership.left_at = datetime.utcnow()
        db.session.commit()
        flash('You have left the group.', 'info')
    else:
        flash('You are not a member of this group.', 'error')
    
    return redirect(url_for('community.groups'))

@community_bp.route('/groups/<int:group_id>/posts', methods=['GET', 'POST'])
@login_required
def group_posts(group_id):
    """View and create posts in a group"""
    group = SupportGroup.query.get_or_404(group_id)
    
    # Check if user is member
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id,
        status='active'
    ).first()
    
    if not membership:
        flash('You must be a member to view posts.', 'error')
        return redirect(url_for('community.group_detail', group_id=group_id))
    
    if request.method == 'POST':
        # Create new post
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        post_type = request.form.get('post_type', 'discussion')
        
        if not title or not content:
            flash('Title and content are required.', 'error')
        else:
            post = GroupPost(
                group_id=group_id,
                user_id=current_user.id,
                title=title,
                content=content,
                post_type=post_type,
                is_anonymous=request.form.get('is_anonymous') == 'on'
            )
            
            db.session.add(post)
            db.session.commit()
            flash('Post created successfully!', 'success')
            return redirect(url_for('community.group_posts', group_id=group_id))
    
    # Get posts
    page = request.args.get('page', 1, type=int)
    posts = GroupPost.query.filter_by(group_id=group_id)\
                          .order_by(GroupPost.created_at.desc())\
                          .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('community/group_posts.html',
                         group=group,
                         posts=posts)

@community_bp.route('/posts/<int:post_id>')
@login_required
def post_detail(post_id):
    """View specific post"""
    post = GroupPost.query.get_or_404(post_id)
    
    # Check if user is member of the group
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=post.group_id,
        status='active'
    ).first()
    
    if not membership:
        flash('You must be a member to view this post.', 'error')
        return redirect(url_for('community.groups'))
    
    # Get comments (if implemented)
    comments = []  # TODO: Implement comments system
    
    return render_template('community/post_detail.html',
                         post=post,
                         comments=comments)

@community_bp.route('/create-group', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create a new support group"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'general')
        is_public = request.form.get('is_public') == 'on'
        rules = request.form.get('rules', '')
        
        if not name or not description:
            flash('Name and description are required.', 'error')
        else:
            group = SupportGroup(
                name=name,
                description=description,
                category=category,
                is_public=is_public,
                rules=rules,
                created_by=current_user.id,
                status='active'
            )
            
            db.session.add(group)
            db.session.commit()
            
            # Add creator as admin member
            membership = GroupMembership(
                user_id=current_user.id,
                group_id=group.id,
                status='active',
                role='admin',
                joined_at=datetime.utcnow()
            )
            db.session.add(membership)
            db.session.commit()
            
            flash('Support group created successfully!', 'success')
            return redirect(url_for('community.group_detail', group_id=group.id))
    
    return render_template('community/create_group.html')

@community_bp.route('/my-groups')
@login_required
def my_groups():
    """User's groups"""
    # Get user's memberships
    memberships = GroupMembership.query.filter_by(
        user_id=current_user.id
    ).order_by(GroupMembership.joined_at.desc()).all()
    
    return render_template('community/my_groups.html',
                         memberships=memberships)

@community_bp.route('/api/group-stats/<int:group_id>')
@login_required
def group_stats(group_id):
    """Get group statistics"""
    group = SupportGroup.query.get_or_404(group_id)
    
    # Check if user is member
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id,
        status='active'
    ).first()
    
    if not membership:
        return jsonify({'error': 'Not a member'}), 403
    
    # Get statistics
    member_count = GroupMembership.query.filter_by(
        group_id=group_id,
        status='active'
    ).count()
    
    post_count = GroupPost.query.filter_by(group_id=group_id).count()
    
    recent_activity = GroupPost.query.filter_by(group_id=group_id)\
                                   .order_by(GroupPost.created_at.desc())\
                                   .limit(5).all()
    
    return jsonify({
        'member_count': member_count,
        'post_count': post_count,
        'recent_activity': [post.to_dict() for post in recent_activity]
    })

@community_bp.route('/api/search-groups')
@login_required
def search_groups():
    """Search groups via API"""
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    
    if not query:
        return jsonify([])
    
    # Build search query
    search_query = SupportGroup.query.filter(
        SupportGroup.is_public == True,
        SupportGroup.status == 'active',
        SupportGroup.name.contains(query)
    )
    
    if category != 'all':
        search_query = search_query.filter(SupportGroup.category == category)
    
    groups = search_query.limit(10).all()
    
    return jsonify([group.to_dict() for group in groups])
