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

    def get_instance_update(self, **kwargs):
        for attr in self.__dict__:
            if attr and attr in kwargs:
                self.__setattr__(f'{attr}', kwargs[f'{attr}'])
        self.save()


class DeliveryOffer(models.Model):
    class IsActive(models.IntegerChoices):
        YES = 1, gettext_lazy('Yes')
        NO = 0, gettext_lazy('No')

    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    wage = models.DecimalField(max_digits=256, decimal_places=2)
    distance = models.DecimalField(max_digits=32, decimal_places=3)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    contractor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contractor", null=True, blank=True)
    delivery_info = models.OneToOneField(DeliveryInfo, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.IntegerField(default=1, choices=IsActive.choices)
    final_bid = models.DecimalField(max_digits=256, decimal_places=2, default=0, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_instance_update(self, **kwargs):
        for attr in self.__dict__:
            if attr in kwargs:
                self.__setattr__(f'{attr}', kwargs[f'{attr}'])
        self.save()

    def save(self,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None
             ):
        if not self.is_active:
            msg_contractor = f"Twoja oferta zostala zaakceptowana przez {self.owner.username}."
            Notification.objects.create(
                delivery_offer=self,
                user=self.contractor,
                title=msg_contractor
            )

            msg_owner = f"Zaakceptowales oferte uzytkownika {self.contractor.username} ({self.final_bid})."
            Notification.objects.create(
                delivery_offer=self,
                user=self.owner,
                title=msg_owner
            )
        super().save()


class UserBid(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=256, decimal_places=2)
    delivery_offer = models.ForeignKey(DeliveryOffer, on_delete=models.CASCADE)

    def __str__(self):
        return self.delivery_offer.name


class Notification(models.Model):
    delivery_offer = models.ForeignKey(DeliveryOffer, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=256)


class Message(models.Model):
    content = models.TextField()
    delivery_offer = models.ForeignKey(DeliveryOffer, on_delete=models.CASCADE)
    message_from = models.ForeignKey(User, on_delete=models.CASCADE, related_name="message_from")
    message_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name="message_to")
    date = models.DateTimeField(auto_now_add=True)


# class Room(models.Model):
#     name = models.CharField(max_length=128)
#     description = models.TextField(null=True, blank=True)
#     owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
#     participants = models.ManyToManyField(User, related_name="participants", blank=True)
#     delivery_offer = models.ManyToManyField(DeliveryOffer)
#
#     def __str__(self):
#         return self.name

