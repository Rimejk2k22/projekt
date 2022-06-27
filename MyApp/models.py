from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy

# Create your models here.


class DeliveryInfo(models.Model):
    city_from = models.CharField(max_length=64)
    city_to = models.CharField(max_length=64)
    street_from = models.CharField(max_length=64)
    street_to = models.CharField(max_length=64)
    street_from_number = models.IntegerField()
    street_to_number = models.IntegerField()
    extras = models.TextField()

    def __str__(self):
        return self.deliveryoffer.name


class DeliveryOffer(models.Model):
    class IsActive(models.IntegerChoices):
        YES = 1, gettext_lazy('Yes')
        NO = 0, gettext_lazy('No')

    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    wage = models.DecimalField(max_digits=256, decimal_places=2, null=True, blank=True)
    distance = models.DecimalField(max_digits=32, decimal_places=3)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    contractor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contractor", null=True, blank=True)
    delivery_info = models.OneToOneField(DeliveryInfo, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.IntegerField(default=1, choices=IsActive.choices)
    final_bid = models.DecimalField(max_digits=256, decimal_places=2, default=0, null=True, blank=True)

    def __str__(self):
        return self.name


class UserBid(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=256, decimal_places=2)
    delivery_offer = models.ForeignKey(DeliveryOffer, on_delete=models.CASCADE)

    def __str__(self):
        return self.delivery_offer.name


class Room(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    participants = models.ManyToManyField(User, related_name="participants", blank=True)
    delivery_offer = models.ManyToManyField(DeliveryOffer)

    def __str__(self):
        return self.name


class MailBox(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
