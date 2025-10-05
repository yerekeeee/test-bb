# booking/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Appointment
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@receiver(post_save, sender=Appointment)
def appointment_created(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        if channel_layer is not None:
            # Готовим подробное сообщение со всеми деталями
            full_message = (
                f"От: {instance.client_display_name}\n"
                f"К: {instance.master.user.get_full_name()}\n"
                f"Дата: {instance.start_time.strftime('%d.%m.%Y в %H:%M')}"
            )

            message_data = {
                'title': '🔔 Новая запись!',
                'body': full_message,
            }

            async_to_sync(channel_layer.group_send)(
                'admin_notifications',
                {
                    'type': 'send_notification',
                    'message': message_data
                }
            )