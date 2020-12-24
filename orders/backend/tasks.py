from celery import shared_task

# celery -A orders worker --loglevel=info --pool=solo
from django.core.mail import EmailMultiAlternatives

from .models import ConfirmEmailToken
from orders.settings import local


@shared_task
def adding_task(x, y):
    return x + y


@shared_task
def user_changed_email_task(user_id, email, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """
    # send an e-mail to the user
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Password Reset Token for {email}",
        # message:
        token.key,
        # from:
        local.EMAIL_HOST_USER,
        # to:
        [email]
    )
    msg.send()
