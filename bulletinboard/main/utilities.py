from django.template.loader import render_to_string
from django.core.signing import Signer
from datetime import datetime
from os.path import splitext

from board.settings import ALLOWED_HOSTS

signer = Signer()

def send_activation_notification(user):
    if ALLOWED_HOSTS:
        host = 'https://' + ALLOWED_HOSTS[0]
        context = {'user': user, 'host': host, 'sign': signer.sign(user.username)}
        subject = render_to_string('email/activation_letter_subject.txt', context)
        body_text = render_to_string('email/activation_letter_body.txt', context)
        user.email_user(subject, body_text)

# Графические файлы, сохраняемые в папке image, будут иметь в качестве имен текущие временные отметки
def get_timestamp_path(instance, filename):
    return '%s%s' % (datetime.now().timestamp(), splitext(filename)[1])

def send_new_comment_notification(comment):
    if ALLOWED_HOSTS:
        host = 'https://' + ALLOWED_HOSTS[0]
        author = comment.ad.author
        context = {'author': author, 'host': host, 'comment': comment}
        subject = render_to_string('email/new_comment_letter_subject.txt', context)
        body_text = render_to_string('email/new_comment_letter_body.txt', context)
        author.email_user(subject, body_text)
