import pytest

from MyApp import models as m

from MyApp import views as v

# Create your tests here.

# Delivery Offer.
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

    assert (
            m.DeliveryOffer.objects.all().first().delivery_info
            ==
            m.DeliveryInfo.objects.all().first()
    )

    assert view.post(request).url == '/dashboard/'


@pytest.mark.django_db
def test_create_delivery_offer_not_logged_in(client):
    request = client.get('/dashboard/add-delivery-offer/')
    assert '/login/' in request.url


@pytest.mark.django_db
def test_create_bid(rf, random_delivery_offer, random_user2):
    url = f'/dashboard/delivery-detail/{random_delivery_offer.id}/'
    data = {
        'bid': 359.99,
    }
    post_request = rf.post(url, data=data)
    view = v.DeliveryOfferDetailView()
    post_request.user = random_user2
    response = view.post(post_request, random_delivery_offer.id)

    assert random_delivery_offer.userbid_set.all().first().owner == random_user2

    assert (
            random_delivery_offer.userbid_set.all().first().delivery_offer
            ==
            random_delivery_offer
    )

    assert random_delivery_offer.userbid_set.all().count() > 0

    assert (
            float(random_delivery_offer.userbid_set.all().first().value)
            ==
            data['bid']
    )

    assert response.status_code == 302
    assert response.url == url


@pytest.mark.django_db
def test_create_bid_auction_close(rf,
                                  random_delivery_offer,
                                  random_user,
                                  random_user2,
                                  random_user2_bid):
    url = f'/dashboard/delivery-detail/{random_delivery_offer.id}/'
    data = {
        'final_bid': random_user2_bid.id,
    }

    post_request = rf.post(url, data=data)
    view = v.DeliveryOfferDetailView()
    post_request.user = random_delivery_offer.owner

    response = view.post(post_request, random_delivery_offer.id)

    random_delivery_offer.get_instance_update(
        contractor_id=random_user2_bid.owner_id,
        is_active=0,
        final_bid=random_user2_bid.value
    )

    assert response.url == '/dashboard/user/delivery-offers/'
    assert response.status_code == 302
    assert random_delivery_offer.contractor == random_user2_bid.owner

    assert (
            random_delivery_offer.contractor.userbid_set.all().first().id
            ==
            data['final_bid']
    )

    assert random_delivery_offer.is_active == 0
    assert random_delivery_offer.final_bid == random_user2_bid.value
    assert random_user.notification_set.all().count() > 0
    assert random_user2.notification_set.all().count() > 0
    assert random_delivery_offer.notification_set.all().count() >= 2


@pytest.mark.django_db
def test_modify_delivery_offer_not_logged_in(client, random_delivery_offer):
    request = client.get(
        f'/dashboard/delivery-detail/modify/{random_delivery_offer.id}/'
    )

    assert '/login/' in request.url


@pytest.mark.django_db
def test_modify_delivery_offer(client, random_delivery_offer, random_user):
    client.force_login(random_user)
    data = {
        **WOOD_TRANSPORT
    }
    name = 'Transport starej maszyny do szycia.'
    wage = 79.99
    data['name'] = name
    data['wage'] = wage

    response = client.post(
        f'/dashboard/delivery-detail/modify/{random_delivery_offer.id}/', data
    )
    random_delivery_offer.get_instance_update(**data)

    assert (
            response.url
            ==
            f"/dashboard/delivery-detail/{random_delivery_offer.id}/"
    )

    assert response.status_code == 302
    assert random_delivery_offer.name == name
    assert random_delivery_offer.wage == wage


@pytest.mark.django_db
def test_delivery_offer_delete_not_logged_in(client, random_delivery_offer):
    request = client.get(
        f'/dashboard/delivery-detail/delete/{random_delivery_offer.id}/'
    )

    assert '/login/' in request.url
    assert m.DeliveryOffer.objects.all().count() > 0


@pytest.mark.django_db
def test_delivery_offer_delete(client, random_delivery_offer, random_user):
    offers_count = m.DeliveryOffer.objects.all().count()
    client.force_login(random_user)
    request = client.get(
        f'/dashboard/delivery-detail/delete/{random_delivery_offer.id}/')

    assert offers_count - 1 == m.DeliveryOffer.objects.all().count()
    assert request.status_code == 302
    assert request.url == '/dashboard/'


@pytest.mark.django_db
def test_notification_delete(client,
                             random_user,
                             random_delivery_offer,
                             random_user_notification):
    user_nots = random_user.notification_set.all().count()
    delivery_nots = random_delivery_offer.notification_set.all().count()
    assert user_nots >= 1
    assert delivery_nots == random_delivery_offer.notification_set.all().count()

    request = client.get(
        f'/dashboard/user/notifications/{random_user_notification.id}/delete/'
    )

    # assert user_nots - 1 == random_user.notification_set.all().count()

    # assert (
    #         delivery_nots - 1
    #         ==
    #         random_delivery_offer.notification_set.all().count()
    # )

    assert request.status_code == 302
    assert request.url == '/dashboard/Not-allowed/'


@pytest.mark.django_db
def test_user_send_message_not_logged_in(client, random_delivery_offer):
    client.get(
        f'/dashboard/user/delivery-offers/{random_delivery_offer.id}/contact/'
    )
    assert not 'sessionid' in client.__dict__['cookies']


@pytest.mark.django_db
def test_user_send_message(rf,
                           random_user,
                           random_user2,
                           random_user_message,
                           random_delivery_offer):

    assert random_user2.message_to.all().first().message_from == random_user

    assert (
            random_user2.message_to.all().first().delivery_offer
            ==
            random_delivery_offer
    )
