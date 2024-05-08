# from django.contrib.auth.models import Group
# from django.contrib.auth import get_user_model
# from django.dispatch import receiver
# from django.db.models.signals import post_save

# from psico_auth.enums import GroupName
# from profiles.models import Profile


# @receiver(post_save, sender=get_user_model())
# def post_create_user(sender, instance, created, **kwargs):
#     if created:
#         customer_group, _ = Group.objects.get_or_create(
#             name=GroupName.CUSTOMER.value)

#         instance.groups.add(customer_group)
#         Profile.objects.create(user=instance)
