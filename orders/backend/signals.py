from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Sum, F
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created

from .models import ConfirmEmailToken, User, Order
from .serializers import OrderSerializer

new_user_registered = Signal(
    providing_args=['user_id'],
)

new_order = Signal(
    providing_args=['user_id'],
)

user_changed_email = Signal(
    providing_args=['user_id', 'email'],
)

new_waybill = Signal(
    providing_args=['shop_user_id', 'order_id'],
)


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """
    Отправляем письмо с токеном для сброса пароля
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param kwargs:
    :return:
    """
    # send an e-mail to the user

    msg = EmailMultiAlternatives(
        # title:
        f"Password Reset Token for {reset_password_token.user}",
        # message:
        reset_password_token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [reset_password_token.user.email]
    )
    msg.send()


@receiver(new_user_registered)
def new_user_registered_signal(user_id, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """
    # send an e-mail to the user
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Password Reset Token for {token.user.email}",
        # message:
        token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [token.user.email]
    )
    msg.send()


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    """
    отправяем письмо при изменении статуса заказа
    """
    # send an e-mail to the user
    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Обновление статуса заказа",
        # message:
        'Заказ сформирован',
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user.email]
    )
    msg.send()


@receiver(user_changed_email)
def user_changed_email_signal(user_id, email, **kwargs):
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
        settings.EMAIL_HOST_USER,
        # to:
        [email]
    )
    msg.send()


@receiver(new_waybill)
def new_waybill_signal(shop_user_id, order_id, **kwargs):
    """
    отправяем письмо при изменении статуса заказа
    """
    # send an e-mail to the user
    shop_user = User.objects.get(id=shop_user_id)

    order = Order.objects.filter(id=order_id).annotate(
        total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price')))
    order_serializer = OrderSerializer(order, many=True)

    msg = EmailMultiAlternatives(
        # title:
        f"Поступил новый заказ",
        # message:
        f"Новый заказ: {order_serializer.data}",
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [shop_user.email]
    )
    msg.send()
