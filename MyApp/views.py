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
import MyApp.validators.delivery_offer_validator as dov
import MyApp.validators.user_bid_validator as ubv


# Create your views here.

class IndexView(View):
    def get(self, request):
        return render(request, 'landing_page.html')


class DashboardView(View):
    def get(self, request):
        all_delivery_offers = m.DeliveryOffer.objects.all().order_by('-date_added')
        recent_added = all_delivery_offers.filter(is_active=1)[:3]

        # Search bar query filtering.
        query = request.GET.get('search')
        if query or request.COOKIES.get('search'):
            query = query if query else request.COOKIES.get('search')
            all_delivery_offers = m.DeliveryOffer.filter_searchbar_query(query)

        context = {
            'all_delivery_offers': all_delivery_offers,
            'recent_added': recent_added
        }
        return render(request, 'MyApp/dashboard.html', context=context)


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
            messages.add_message(request,
                                 messages.ERROR,
                                 'Niepoprawny Login lub haslo.')
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
            pv.validate_password(password=password,
                                 password_validators=all_password_validators)
        except ValidationError as password_errors:
            errors.extend(password_errors)

        try:
            # Validate password similarity.
            pev.PasswordEqualValidator.validate(password=password,
                                                password2=password2)
        except ValidationError as password_equal_error:
            errors.extend(password_equal_error)

        try:
            # Validate login and email.
            elv.validate_login_email(
                username=username,
                email=email,
                login_email_validators=all_login_email_validators
            )

        except ValidationError as login_username_errors:
            errors.extend(login_username_errors)

        # If any errors, loop through adding single error to flash messages.
        if errors:
            for error in errors:
                messages.add_message(request, messages.ERROR, error)
            return redirect('register')

        # Create User profile.
        user_profile = m.UserProfile.objects.create()

        # User Instance.
        user = m.User.objects.create_user(email=email,
                                          username=username,
                                          password=password,
                                          profile=user_profile,
                                          )

        # After Successful User creation, automatically login.
        login(request, user)
        return redirect('dashboard')


class UserProfile(View):
    def get(self, request):
        user = request.user
        context = {'user': user}
        return render(request, 'MyApp/user-profile.html', context=context)


class UserProfileUpdate(LoginRequiredMixin, View):
    login_url = '{}?next={}'.format(settings.LOGIN_URL, 'delivery-offer-modify')

    def get(self, request):
        return render(request, 'MyApp/user-profile-update.html')

    def post(self, request):
        data = request.POST
        # Get data from form.
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        avatar = request.FILES.get('avatar')

        errors = []
        email_exists = m.User.objects.all().filter(email=email)
        if email_exists:
            errors.append('Podany e-mail istnieje.')

        if not email:
            errors.append('Podaj e-mail.')

        if errors:
            for error in errors:
                messages.add_message(request, messages.ERROR, error)
                return redirect('user-profile-update')

        # User instance.
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email

        # User profile instance
        user_profile = m.UserProfile.objects.all().filter(user=user).first()
        user_profile.avatar = avatar

        user_profile.save()
        user.save()
        return redirect('user-profile')


class CreateDeliveryOfferView(LoginRequiredMixin, View):
    login_url = '{}?next={}'.format(settings.LOGIN_URL, 'delivery-offer-add')

    def get(self, request):

        # If user passed phrase into search bar, filter delivery offers.
        if query := request.GET.get('search'):
            return m.DeliveryOffer.set_search_cookie_redirect(query)

        recent_added = m.DeliveryOffer.objects.all()[:3]
        context = {'recent_added': recent_added}
        return render(request, 'MyApp/delivery-offer-add.html', context=context)

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

        # Validate Fields.
        if errors := dov.DeliveryOfferValidator.validate(dict(data)):
            for error in errors:
                messages.add_message(request, messages.ERROR, error)
                return redirect('delivery-offer-add')

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

        # If user passed phrase into search bar, filter delivery offers.
        if query := request.GET.get('search'):
            return m.DeliveryOffer.set_search_cookie_redirect(query)

        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)
        bids = delivery_offer.userbid_set.all()

        context = {
            'delivery_offer': delivery_offer,
            'bids': bids
        }
        return render(request,
                      'MyApp/delivery-offer-detail.html',
                      context=context)

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
        # Validate User bid.
        if errors := ubv.UserBidValidator.validate(bid):
            for error in errors:
                messages.add_message(request, messages.ERROR, error)
                return redirect(
                    'delivery-offer-detail', delivery_id=delivery_offer.pk)

        m.UserBid.objects.create(
            owner=request.user,
            value=bid,
            delivery_offer=delivery_offer
        )
        return redirect('delivery-offer-detail', delivery_id=delivery_offer.pk)


class DeliveryOfferModifyView(LoginRequiredMixin, View):
    login_url = '{}?next={}'.format(settings.LOGIN_URL, 'delivery-offer-modify')

    def get(self, request, delivery_id):

        # If user passed phrase into search bar, filter delivery offers.
        if query := request.GET.get('search'):
            return m.DeliveryOffer.set_search_cookie_redirect(query)

        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)
        context = {'delivery_offer': delivery_offer}

        # Do not allow to edit proceeded offer.
        if not delivery_offer.is_active:
            return redirect('dashboard')

        # You are not owner, denied.
        if request.user != delivery_offer.owner:
            return redirect('http_405')

        return render(request,
                      'MyApp/delivery-offer-modify.html',
                      context=context)

    def post(self, request, delivery_id):
        data = request.POST
        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)
        delivery_info = m.DeliveryInfo.objects.get(deliveryoffer=delivery_offer)

        # You are not owner, denied.
        if request.user != delivery_offer.owner:
            return redirect('http_405')

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

        # Validate Fields.
        if errors := dov.DeliveryOfferValidator.validate(dict(data)):
            for error in errors:
                messages.add_message(request, messages.ERROR, error)
                return redirect(
                    'delivery-offer-modify', delivery_id=delivery_offer.pk)

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

        # You are not owner, denied.
        if request.user != delivery_offer.owner:
            return redirect('http_405')

        delivery_info = delivery_offer.delivery_info
        delivery_offer.delete()
        delivery_info.delete()
        return redirect('dashboard')


class NotificationDeleteView(View):
    def get(self, request, notification_id):
        notification = m.Notification.objects.get(pk=notification_id)

        if notification.user != request.user:
            return redirect('http_405')

        notification.delete()
        return redirect('dashboard')


class UserDeliveryOffer(View):
    def get(self, request):

        # If user passed phrase into search bar, filter delivery offers.
        if query := request.GET.get('search'):
            return m.DeliveryOffer.set_search_cookie_redirect(query)

        delivery_offers = m.DeliveryOffer.objects.all().filter(
            Q(owner=request.user) | Q(contractor=request.user),
            Q(is_active=1) | Q(is_active=0)
        ).order_by('-date_added')

        context = {'delivery_offers': delivery_offers}
        return render(request,
                      'MyApp/user-delivery-offers.html',
                      context=context
                      )


class UserSendMessageView(View):
    def get(self, request, delivery_id):

        # If user passed phrase into search bar, filter delivery offers.
        if query := request.GET.get('search'):
            return m.DeliveryOffer.set_search_cookie_redirect(query)

        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)

        if request.user != delivery_offer.owner and request.user != delivery_offer.contractor:
            return HttpResponse('<h2>Not allowed</h2>')

        all_messages = delivery_offer.message_set.all().order_by('-date')
        context = {'all_messages': all_messages}
        return render(request, 'MyApp/user-send-message.html', context=context)

    def post(self, request, delivery_id):
        delivery_offer = m.DeliveryOffer.objects.get(pk=delivery_id)

        user = (
            delivery_offer.owner if request.user != delivery_offer.owner else
            delivery_offer.contractor
        )

        content = request.POST.get('content')
        m.Message.objects.create(content=content,
                                 delivery_offer=delivery_offer,
                                 message_from=request.user,
                                 message_to=user)

        return redirect('user-send-message', delivery_id=delivery_offer.pk)


class Http405View(View):
    def get(self, request):
        # If user passed phrase into search bar, filter delivery offers.
        if query := request.GET.get('search'):
            return m.DeliveryOffer.set_search_cookie_redirect(query)

        return render(request, 'MyApp/http_errors/http_405.html')
