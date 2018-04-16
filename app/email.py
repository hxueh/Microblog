from flask_mail import Message
from flask import current_app, render_template
from . import mail
from .decorators import async_task


def sendmail(to, subject='TEST', template=None, **kwargs):
    # https://stackoverflow.com/questions/40326651/flask-mail-sending-email-asynchronously-based-on-flask-cookiecutter
    app = current_app._get_current_object()
    msg = Message()
    # kwargs are arguments, like username
    msg.subject = current_app.config['MAIL_SUBJECT_PREFIX'] + subject
    msg.sender = ('Microblog', current_app.config['MAIL_USERNAME'])
    if template is not None:
        msg.body = render_template(template + '.txt', **kwargs)
        msg.html = render_template(template + '.html', **kwargs)
    else:
        msg.body = 'TEST'
    msg.add_recipient(to)
    _send_async_email(app, msg)


@async_task
def _send_async_email(flask_app, msg):
    """ Sends an send_email asynchronously
    Args:
        flask_app (flask.Flask): Current flask instance
        msg (Message): Message to send
    Returns:
        None
    """
    with flask_app.app_context():
        mail.send(msg)