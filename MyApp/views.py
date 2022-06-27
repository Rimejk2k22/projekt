from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Permission
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect, HttpResponse
from django.conf import settings
from django.views import View

from MyApp import models as m


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
            return redirect('/dashboard/')
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('/dashboard/')

        else:
            return HttpResponse('<h2>Blad</h2><button><a href="/login/">Wroc</a></button>')


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('/login/')


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Passwords vary.
        if password != password2:
            return redirect('/register/')

        # User Instance.
        user = m.User.objects.create_user(username=username, password=password)
        user.user_permisions.add(Permission.objects.get(codename='add_deliveryoffer'))

        # After Successful User creation, automatically login.
        login(request, user)
        return redirect('/dashboard/')


class CreateDeliveryOfferView(PermissionRequiredMixin, View):
    login_url = settings.LOGIN_URL
    permission_required = ['MyApp.add_deliveryoffer']
    def get(self, request):
        return render(request, 'add-delivery-offer.html')

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

        # Create DeliveryInfo Instance.
        delivery_info = m.DeliveryInfo(
            city_from=city_from,
            street_from=street_from,
            street_from_number=street_from_number,
            city_to=city_to,
            street_to=street_to,
            street_to_number=street_to_number
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
        return redirect('/dashboard/')

















