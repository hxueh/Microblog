from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from .form import LoginForm, SignupForm, ChangeEmailForm, ChangePasswordForm, \
    ResetPasswordForm, ResetPasswordRequestForm, \
    TwoFactorAuthenticatorForm, DeleteUserForm
from ..email import sendmail
from ..models import User


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Initialize form
    form = LoginForm()
    title = 'Log In'
    header = title

    if form.validate_on_submit():
        # We can user username or email address as identification
        user = User.query.filter_by(username=form.user.data).first() \
               or User.query.filter_by(email=form.user.data).first()
        if user is None:
            flash('User not exists.')
            return redirect(url_for('auth.login'))
        if user.verify_password(form.password.data):
            if user.twofa_enable:
                if not user.verify_twofa(form.token.data):
                    flash('2FA verification fail.')
                    return redirect('auth.login')

            login_user(user, remember=form.remember.data)
            # http://flask.pocoo.org/docs/0.12/api/#flask.Request.args
            # Redirect back to where they were before login.
            next_url = request.args.get('next')
            if next_url is None:
                next_url = url_for('main.index')
            return redirect(next_url)

    return render_template('form.html', form=form, header=header, title=title)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    title = 'Sign Up'
    header = title

    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_email_token()
        sendmail(user.email, 'Confirm your account.', 'email', user=user,
                 token=token, arg='confirm')
        flash('A confirmation email has been sent to your inbox.')
        return redirect(url_for('auth.login'))

    return render_template('form.html', form=form, header=header, title=title)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        # If the user is confirmed
        return redirect(url_for('main.index'))

    if current_user.verify_email_token(token):
        flash('Enjoy.')
    else:
        flash('The confirmation email is invalid or has expired.')
    
    return redirect(url_for('main.index'))


@auth.route('/resend-confirm-email')
@login_required
def resend_confirm_email():
    if current_user.confirmed:
        flash('You have been confirmed.')
        return redirect(url_for('main.index'))
    
    else:
        token = current_user.generate_email_token()
        sendmail(current_user.email, 'Confirm your account.', 'email',
                 user=current_user, token=token, arg='confirm')
        flash('A confirmation email has been sent to your email.')
        return redirect(url_for('auth.login'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    title = 'Change Password'
    header = 'Change Your Password'

    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Password has been updated.')
            return redirect(url_for('main.index'))

    return render_template('form.html', form=form, header=header, title=title)


@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    form = ResetPasswordRequestForm()
    title = 'Reset Password'
    header = 'Reset Your Password'

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            token = user.generate_password_reset_token()
            sendmail(user.email, 'Reset your password.', 'email',
                     user=user, token=token, arg='reset')
            flash('An email has been sent to you.')
        else:
            flash('User not exists.')
        return redirect(url_for('main.index'))

    return render_template('form.html', form=form, header=header, title=title)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPasswordForm()
    title = 'Reset Password'
    header = 'Reset Your Password'

    if form.validate_on_submit():
        if User.verity_password_reset_token(token, form.password.data):
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            flash('Not valid token.')
            return redirect(url_for('main.index'))

    return render_template('form.html', form=form, header=header, title=title)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    title = 'Change Email'
    header = 'Change Your Email'

    if form.validate_on_submit():
        token = current_user.generate_email_changing_token(form.email.data)
        sendmail(form.email.data, 'Changing Email Address.', 'email',
                 user=current_user, token=token, arg='change')
        flash('A confirmation email has been sent to your new email account.')
        return redirect(url_for('main.index'))

    return render_template('form.html', form=form, header=header, title=title)


@auth.route('/change-email/<token>', methods=['GET', 'POST'])
@login_required
def change_email(token):
    if current_user.verify_email_changing_token(token):
        flash('Your email address has been updated.')
    else:
        flash('Invalid token.')
    return redirect(url_for('main.index'))


@auth.route('/two-factor-authenticator/', methods=['GET', 'POST'])
@login_required
def twofa():
    form = TwoFactorAuthenticatorForm()
    if not current_user.twofa_enable:
        twofa_url = current_user.create_twofa()

        if form.validate_on_submit():
            if current_user.verify_twofa(form.token.data):
                current_user.twofa_enable = True
                db.session.add(current_user)
                db.session.commit()
                flash('You have successfully '
                      'enable two factor authentication.')
            else:
                flash('Token verification fail.')
                db.session.rollback()
            return redirect(url_for('main.index'))

        return render_template('twofa.html', title='2FA',
                               header='Setup Two Factor Authentication',
                               twofa_url=twofa_url, form=form)
    
    else:
        if form.validate_on_submit():
            if current_user.verify_twofa(form.token.data):
                current_user.disable_twofa()
                flash('You have successfully '
                      'disable two factor authentication.')
            return redirect(url_for('main.index'))
        return render_template('twofa.html', title='2FA',
                               header='Disable Two Factor Authentication',
                               form=form)


@auth.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    form = DeleteUserForm()
    title = 'Delete Account'
    header = 'Delete Your Account'

    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            current_user.delete_user()
            flash('Your data has been permanently deleted.')
        
        return redirect(url_for('main.index'))
    
    return render_template('form.html', form=form, header=header, title=title)
