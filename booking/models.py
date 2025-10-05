from django.db import models
from django.conf import settings
from datetime import timedelta

class Service(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.DurationField()

    def __str__(self):
        return f"{self.name} ({self.duration})"

class Appointment(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='appointments',
        null=True, blank=True
    )
    anonymous_name = models.CharField(max_length=100, null=True, blank=True)
    anonymous_phone = models.CharField(max_length=20, null=True, blank=True)

    master = models.ForeignKey('users.MasterProfile', on_delete=models.CASCADE, related_name='appointments')
    services = models.ManyToManyField(Service)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_duration = models.DurationField()

    def __str__(self):
        # This uses the property below to get the name
        client_name = self.client_display_name
        return f"Запись для {client_name} к {self.master}"

    # ▼▼▼ ADD THESE METHODS ▼▼▼
    @property
    def client_display_name(self):
        """Returns the client's name, whether they are registered or anonymous."""
        if self.client:
            return self.client.get_full_name()
        return self.anonymous_name

    @property
    def client_display_phone(self):
        """Returns the client's phone, whether they are registered or anonymous."""
        if self.client:
            return self.client.phone_number
        return self.anonymous_phone


class Review(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review')
    master = models.ForeignKey('users.MasterProfile', on_delete=models.CASCADE, related_name='reviews')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Отзыв от {self.client} для {self.master} на {self.rating} звезд"