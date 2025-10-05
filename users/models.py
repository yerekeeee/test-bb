from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg


class CustomUser(AbstractUser):
    phone_number = models.CharField("Телефон", max_length=20, blank=True, null=True)


class MasterProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    photo = models.ImageField(upload_to='masters_photos/', null=True, blank=True, default='masters_photos/default.png')
    bio = models.TextField(blank=True, null=True)
    services = models.ManyToManyField('booking.Service', related_name='masters')

    def __str__(self):
        return self.user.get_full_name()

    @property
    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    @property
    def review_count(self):
        return self.reviews.count()