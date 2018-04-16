from flask import redirect, render_template, url_for, flash, request, current_app
from flask_login import login_required, current_user

from . import main
from .form import EditProfileForm, AdminEditProfileForm, PostForm, CommentForm
from ..models import Permission, Role, User, Post, Comment, Follow
from .. import db
from ..decorators import admin_required


@main.route('/explore')
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.time.desc()).\
        paginate(page, current_app.config['POSTS_PER_PAGE'], True)
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', posts=posts.items, next_url=next_url, prev_url=prev_url)


@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.index'))
    # Join will combine two table, then filter by follower.
    own = Post.query.filter_by(author=current_user._get_current_object())
    page = request.args.get('page', 1, type=int)
    others = Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == current_user.id)
    posts = others.union(own).order_by(Post.time.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], True)
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', posts=posts.items, form=form, next_url=next_url, prev_url=prev_url)
    

@main.route('/profile/<username>')
def profile(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.time.desc()).\
        paginate(page, current_app.config['POSTS_PER_PAGE'], True)
    next_url = url_for('main.profile', username=username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.profile', username=username, page=posts.prev_num) if posts.has_prev else None

    return render_template('profile.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    header = 'Edit Your Profile'
    title = 'Edit Profile'

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.nickname = form.nickname.data
        current_user.location = form.location.data
        current_user.about = form.about.data
        db.session.add(current_user)
        db.session.commit()
        return redirect(url_for('main.index'))

    form.username.data = current_user.username
    form.nickname.data = current_user.nickname
    form.location.data = current_user.location
    form.about.data = current_user.about

    return render_template('form.html', form=form, title=title, header=header)


@main.route('/admin-edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_profile(id):
    user = User.query.get_or_404(id)
    form = AdminEditProfileForm(user=user)
    header = 'Edit ' + user.username + "'s Profile"
    title = 'Admin Edit Profile'

    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.nickname = form.nickname.data
        user.location = form.location.data
        user.about = form.about.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('main.profile', username=user.username))

    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.nickname.data = user.nickname
    form.location.data = user.location
    form.about.data = user.about
    return render_template('form.html', form=form, header=header, title=title)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(post=post).order_by(Comment.time.desc()).\
        paginate(page, current_app.config['COMMENTS_PER_PAGE'], True)
    next_url = url_for('main.post', id=id, page=comments.next_num) if comments.has_next else None
    prev_url = url_for('main.post', id=id, page=comments.prev_num) if comments.has_prev else None

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post, author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been commited.')
        return redirect(url_for('main.post', id=post.id))

    return render_template('post.html', post=post, form=form, comments=comments.items,
                           next_url=next_url, prev_url=prev_url)


@main.route('/post/<int:id>/delete')
@login_required
def post_delete(id):
    if current_user.can(Permission.MODERATE) or current_user._get_current_object() is Post.query.get_or_404(id).author:
        Post.query.get(id).delete_post()
        flash('Post deleted.')
    
    else:
        flash('Permission not allowed.')
    
    return redirect(url_for('main.index'))


@main.route('/comment/<int:id>/delete')
@login_required
def comment_delete(id):
    if current_user.can(Permission.MODERATE) \
            or current_user._get_current_object() is Comment.query.get_or_404(id).author \
            or current_user._get_current_object() is Comment.query.get_or_404(id).post.author:
        Comment.query.get(id).delete_comment()
        flash('Comment deleted.')
    
    else:
        flash('Permission not allowed.')
    
    return redirect(url_for('main.index'))


@main.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if current_user.can(Permission.FOLLOW) and user is not None and not current_user.is_following(user):
        current_user.follow(user)
        flash('Followed')
    
    return redirect(url_for('main.profile', username=username))


@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is not None and current_user.is_following(user):
        current_user.unfollow(user)
        flash('Unfollowed')

    return redirect(url_for('main.profile', username=username))


@main.route('/following/<username>')
def following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)

    follow = Follow.query.filter_by(follower=user).filter(Follow.followed_id != user.id).order_by(Follow.time.desc()).\
        paginate(page, current_app.config['FOLLOW_PER_PAGE'], True)

    next_url = url_for('main.following', username=username, page=follow.next_num) if follow.has_next else None
    prev_url = url_for('main.following', username=username, page=follow.prev_num) if follow.has_prev else None

    return render_template('follow.html', user=user, follow=follow.items, title='Following',
                           next_url=next_url, prev_url=prev_url)


@main.route('/follower/<username>')
def follower(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)

    follow = Follow.query.filter_by(followed=user).filter(Follow.follower_id != user.id).order_by(Follow.time.desc()).\
        paginate(page, current_app.config['FOLLOW_PER_PAGE'], True)

    next_url = url_for('main.following', username=username, page=follow.next_num) if follow.has_next else None
    prev_url = url_for('main.following', username=username, page=follow.prev_num) if follow.has_prev else None

    return render_template('follow.html', user=user, follow=follow.items, title='Follower',
                           next_url=next_url, prev_url=prev_url)
