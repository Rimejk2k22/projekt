import django.test
import pytest
from django.test import TestCase
from MyApp import models as m
from MyApp import views as v


# Create your tests here.

WOOD_TRANSPORT = {
    'name': 'Transport Drewna.',
    'description': 'Okolo 200kg.',
    'wage': 59.99,
    'distance': 2,
    'city_from': 'Kozia wolka',
    'street_from': 'Polna',
    'street_from_number': 45,
    'city_to': 'Kozia wolka',
    'street_to': 'Kielbasiana',
    'street_to_number': 22,
    'extras': 'x=54.234523, y=23.53424',
}


@pytest.fixture
def random_user():
    return m.User.objects.create_user(
        username='Draven',
        email='draven@axe.com',
        password='random123'
    )


@pytest.fixture
def random_user2():
    return m.User.objects.create_user(
        username='Pietaszek',
        email='Pietaszek@bialy.com',
        password='random123'
    )


@pytest.mark.django_db
def test_login_user(rf, client, random_user, django_user_model):
    request = rf.get('/login/')
    get_response = v.LoginView()
    request.user = django_user_model
    post_response = client.post('/login/',
                                {'username': f'{random_user.username}',
                                 'password': f'{random_user.password}'})

    assert not client.login(username='Pietaszsek', password='qwerty')
    assert random_user.is_authenticated
    assert client.login(username='Draven', password='random123')
    assert get_response.get(request).status_code == 302
    assert post_response.status_code == 302


@pytest.mark.django_db
def test_register_user(client, django_user_model):
    get_response = client.get('/register/')
    post_response = client.post('/register/',
                                {'email': 'random@wp.pl',
                                 'username': 'Klojda',
                                 'password': 'kaka1234',
                                 'password2': 'kaka1234'})

    assert get_response.status_code == 200
    assert post_response.status_code == 302
    assert django_user_model.objects.all().count() > 0


@pytest.mark.django_db
def test_register_failure_user(client, django_user_model):
    post_response = client.post('/register/',
                                {'email': 'random12@wp.pl',
                                 'username': 'gb',
                                 'password': 'qwert',
                                 'password2': 'zxcvb'})

    assert post_response.url == '/register/'
    assert django_user_model.objects.all().count() == 0


@pytest.mark.django_db
def test_create_delivery_offer(rf, client, random_user):
    request = rf.post('/dashboard/add-delivery-offer/', data=WOOD_TRANSPORT)
    view = v.CreateDeliveryOfferView()
    request.user = random_user
    view.post(request)

    assert m.DeliveryOffer.objects.all().count() > 0
    assert m.DeliveryInfo.objects.all().count() > 0
    assert m.DeliveryOffer.objects.all().first().delivery_info == m.DeliveryInfo.objects.all().first()
    assert view.post(request).url == '/dashboard/'
