import pytest
from MyApp import models as m


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


@pytest.fixture
def random_delivery_offer(random_user):
    user = random_user
    delivery_info = m.DeliveryInfo.objects.create(
        city_from='Kozia wolka',
        street_from='Budapren',
        street_from_number=15,

        city_to='Kozia wolka',
        street_to='Pawulon',
        street_to_number=99,
        extras='Blok naprzeciwko lidla.',
    )

    return m.DeliveryOffer.objects.create(
        owner=user,
        delivery_info=delivery_info,
        name='Transport Mebli',
        description='Szafa, biurko, stol.',
        wage=67.59,
        distance=2,
    )


@pytest.fixture
def random_user_notification(random_user, random_delivery_offer):
    return m.Notification.objects.create(
        delivery_offer=random_delivery_offer,
        user=random_user,
        title="Random test text."
    )


@pytest.fixture
def random_user_message(random_user, random_user2, random_delivery_offer):
    return m.Message.objects.create(
        content=f'Hello, {random_user2.username}',
        delivery_offer=random_delivery_offer,
        message_from=random_user,
        message_to=random_user2
    )


@pytest.fixture
def random_user2_bid(random_user2, random_delivery_offer):
    delivery_offer = random_delivery_offer
    user = random_user2

    return m.UserBid.objects.create(
        owner=user,
        value=45.99,
        delivery_offer=delivery_offer,
    )
