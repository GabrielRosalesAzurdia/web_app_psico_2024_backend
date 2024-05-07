from django.db import models
from django.contrib.auth import get_user_model

def create_profile_image_path(instance, filename: str):
    filename = filename.lower().replace(' ', '_').replace('-', '_')

    return f'profiles/{instance.user.username}/{filename}'


class Profile(models.Model):
    user = models.OneToOneField(
        get_user_model(),
        related_name='profile',
        on_delete=models.CASCADE)

    completed = models.BooleanField(default=False)

    image = models.ImageField(upload_to=create_profile_image_path, blank=True)
    phone_number = models.CharField(max_length=25, blank=True, default='')

    def __str__(self) -> str:
        return f"{self.user.username}'s Profile"
