from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, HttpResponse
import django.contrib.auth.password_validation as pv
from django.conf import settings
from django.views import View

from MyApp import models as m
import MyApp.validators.email_login_validation as elv
import MyApp.validators.password_equal_validator as pev


# Create your views here.

class IndexView(View):
    def get(self, request):
        return render(request, 'index.html')


class DashboardView(View):
    def get(self, request):
        all_delivery_offers = m.DeliveryOffer.objects.all()
        context = {'all_delivery_offers': all_delivery_offers}
        return render(request, 'dashboard.html', context=context)


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user:
            # Login User.
            login(request, user)

            # If previous page detected, redirect directly.
            if previous_page := request.GET.get('next'):
                return redirect(previous_page)

            return redirect('dashboard')

        else:
            messages.add_message(request, messages.ERROR, 'Niepoprawny Login lub haslo.')
            return redirect('login')


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


class RegisterView(View):
    def get(self, request):

        return render(request, 'register.html')

    def post(self, request):
        data = request.POST
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        password2 = data.get('password2')

        # All validators needed to validate password, username and email.
        all_password_validators = pv.get_password_validators(settings.AUTH_PASSWORD_VALIDATORS)
        all_login_email_validators = elv.get_login_email_validators(settings.LOGIN_EMAIL_VALIDATORS)

        # Error messages from all try, except blocks.
        errors = []
        try:
            # Validate password.
            pv.validate_password(password=password, password_validators=all_password_validators)
        except ValidationError as password_errors:
            errors.extend(password_errors)

        try:
            # Validate password similarity.
            pev.PasswordEqualValidator.validate(password=password, password2=password2)
        except ValidationError as password_equal_error:
            errors.extend(password_equal_error)

        try:
            # Validate login and email.
            elv.validate_login_email(username=username, email=email, login_email_validators=all_login_email_validators)
        except ValidationError as login_username_errors:
            errors.extend(login_username_errors)

        # If any errors, loop through adding single error to flash messages.
        if errors:
            for error in errors:
                messages.add_message(request, messages.ERROR, error)
            return redirect('register')


        # User Instance.
        user = m.User.objects.create_user(email=email, username=username, password=password)

        # After Successful User creation, automatically login.
        login(request, user)
        return redirect('dashboard')


class UserProfile(View):
    def get(self, request):
        user = request.user
        context = {'user': user}
        return render(request, 'user-profile.html', context=context)


class CreateDeliveryOfferView(LoginRequiredMixin, View):
    login_url = '{}?next={}'.format(settings.LOGIN_URL, 'delivery-offer-add')

    def get(self, request):
        return render(request, 'delivery-offer-add.html')

    def post(self, request):
        data = request.POST

        name = data.get('name')
        description = data.get('description')
        wage = data.get('wage')
        distance = data.get('distance')

        # Pick up place.
        city_from = data.get('city_from')
        street_from = data.get('street_from')
        street_from_number = data.get('street_from_number')

        # Drop place.
        city_to = data.get('city_to')
        street_to = data.get('street_to')
        street_to_number = data.get('street_to_number')
        extras = data.get('extras')

        # Create DeliveryInfo Instance.
        delivery_info = m.DeliveryInfo(
            city_from=city_from,
            street_from=street_from,
            street_from_number=street_from_number,
            city_to=city_to,
            street_to=street_to,
            street_to_number=street_to_number,
            extras=extras
        )
        delivery_info.save()

        # Create DeliveryOffer.
        m.DeliveryOffer.objects.create(
            name=name,
            description=description,
            wage=wage,
            distance=distance,
            owner=request.user,
            delivery_info=delivery_info
        )
        return redirect('dashboard')


class DeliveryOfferDetailView(View):
    def get(self, request, delivery_id):
        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)
        bids = delivery_offer.userbid_set.all()

        context = {
            'delivery_offer': delivery_offer,
            'bids': bids
        }
        return render(request, 'delivery-offer-detail.html', context=context)

    def post(self, request, delivery_id):
        data = request.POST
        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)

        user_bid = m.UserBid.objects.all().filter(pk=data.get('final_bid')).first()
        if user_bid and delivery_offer.is_active:
            delivery_offer.get_instance_update(
                contractor_id=user_bid.owner_id,
                is_active=0,
                final_bid=user_bid.value
            )
            return redirect('user-delivery-offers')

        bid = data.get('bid')
        m.UserBid.objects.create(
            owner=request.user,
            value=bid,
            delivery_offer=delivery_offer
        )
        return redirect('delivery-offer-detail', delivery_id=delivery_offer.pk)


class DeliveryOfferModifyView(LoginRequiredMixin, View):
    login_url = '{}?next={}'.format(settings.LOGIN_URL, 'delivery-offer-modify')

    def get(self, request, delivery_id):
        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)
        context = {'delivery_offer': delivery_offer}

        # Do not allow to edit proceeded offer.
        if not delivery_offer.is_active:
            return redirect('dashboard')

        # You are not owner, denied.
        if request.user != delivery_offer.owner:
            return HttpResponse('Nie masz uprawnien.')

        return render(request, 'delivery-offer-modify.html', context=context)

    def post(self, request, delivery_id):
        data = request.POST
        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)
        delivery_info = m.DeliveryInfo.objects.get(deliveryoffer=delivery_offer)

        # You are not owner, denied.
        if request.user != delivery_offer.owner:
            return HttpResponse('Nie masz uprawnien.')

        name = data.get('name')
        description = data.get('description')
        wage = data.get('wage')
        distance = data.get('distance')

        # Pick up place.
        city_from = data.get('city_from')
        street_from = data.get('street_from')
        street_from_number = data.get('street_from_number')

        # Drop place.
        city_to = data.get('city_to')
        street_to = data.get('street_to')
        street_to_number = data.get('street_to_number')
        extras = data.get('extras')

        # Update DeliveryInfo Instance.
        delivery_info.get_instance_update(
            city_from=city_from,
            street_from=street_from,
            street_from_number=street_from_number,
            city_to=city_to,
            street_to=street_to,
            street_to_number=street_to_number,
            extras=extras
        )

        # Update DeliveryOffer Instance.
        delivery_offer.get_instance_update(
            name=name,
            description=description,
            wage=wage,
            distance=distance,
        )

        return redirect('delivery-offer-detail', delivery_id=delivery_offer.pk)


class DeliveryOfferDeleteView(LoginRequiredMixin, View):
    login_url = '{}?next={}'.format(settings.LOGIN_URL, 'delivery-offer-delete')

    def get(self, request, delivery_id):
        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)

        # Do not allow to edit proceeded offer.
        if not delivery_offer.is_active:
            return redirect('dashboard')

        # You are not owner, denied.
        if request.user != delivery_offer.owner:
            return HttpResponse('Nie masz uprawnien.')

        delivery_info = delivery_offer.delivery_info
        delivery_offer.delete()
        delivery_info.delete()
        return redirect('dashboard')


class NotificationDetailView(View):
    def get(self, request):
        user = request.user
        context = {'user': user}
        return render(request, 'user-notifications.html', context=context)


class NotificationDeleteView(View):
    def get(self, request, notification_id):
        notification = m.Notification.objects.get(pk=notification_id)
        notification.delete()
        return redirect('user-notifications')


class UserDeliveryOffer(View):
    def get(self, request):

        delivery_offers = m.DeliveryOffer.objects.all().filter(Q(owner=request.user) | Q(contractor=request.user), Q(is_active=1) | Q(is_active=0))

        context = {'delivery_offers': delivery_offers}
        return render(request, 'user-delivery-offers.html', context=context)


class UserSendMessageView(View):
    def get(self, request, delivery_id):
        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)

        if request.user != delivery_offer.owner and request.user != delivery_offer.contractor:
            return HttpResponse('<h2>Not allowed</h2>')

        context = {'delivery_offer': delivery_offer}
        return render(request, 'user-send-message.html', context=context)

    def post(self, request, delivery_id):
        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)
        user = delivery_offer.owner if request.user != delivery_offer.owner else delivery_offer.contractor

        content = request.POST.get('content')

        m.Message.objects.create(content=content, delivery_offer=delivery_offer, message_from=request.user, message_to=user)

        return redirect('user-send-message', delivery_id=delivery_offer.pk)
