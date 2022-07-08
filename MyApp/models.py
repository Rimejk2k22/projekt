from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy

# Create your models here.


class User(AbstractUser):

    def save(self, *args, **kwargs):
        UserProfile.objects.create(user=self)
        super().save()


class UserProfile(models.Model):
    avatar = models.ImageField(default='user.svg', null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)


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

    contractor = models.ForeignKey(User,
                                   on_delete=models.CASCADE,
                                   related_name="contractor",
                                   null=True,
                                   blank=True
                                   )

    delivery_info = models.OneToOneField(DeliveryInfo, on_delete=models.CASCADE)
    is_active = models.IntegerField(default=1, choices=IsActive.choices)

    final_bid = models.DecimalField(
        max_digits=256,
        decimal_places=2,
        default=0,
        null=True,
        blank=True
    )
    date_added = models.DateTimeField(auto_now_add=True)

    @classmethod
    def filter_searchbar_query(cls, query):
        return cls.objects.all().filter(
            Q(name__icontains=query) |
            Q(owner__username__icontains=query) |
            Q(delivery_info__city_from__icontains=query) |
            Q(delivery_info__city_to__icontains=query)
        )

    @classmethod
    def set_search_cookie_redirect(cls, query):
        http_request = redirect('dashboard')
        http_request.set_cookie('search', query, max_age=1)
        return http_request

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
            msg_contractor = f"'@{self.name}' Twoja oferta zostala zaakceptowana przez {self.owner.username}."
            Notification.objects.create(
                delivery_offer=self,
                user=self.contractor,
                title=msg_contractor
            )

            msg_owner = f"'@{self.name}' Zaakceptowales oferte uzytkownika {self.contractor.username} ({self.final_bid} zł)."
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

    def save(self,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None
             ):

        msg_owner = f'"@{self.delivery_offer.name}" Użytkownik {self.owner.username} złożył ofertę ({self.value} zł).'
        Notification.objects.create(
            delivery_offer=self.delivery_offer,
            user=self.delivery_offer.owner,
            title=msg_owner
        )
        super().save()


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
