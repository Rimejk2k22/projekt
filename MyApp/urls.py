from django.urls import path
from MyApp import views as v

# MyApp urls.
urlpatterns = [
    path('', v.DashboardView.as_view(), name="dashboard"),
    path('user/profile/', v.UserProfile.as_view(), name="user-profile"),
    path('user/profile/update/', v.UserProfileUpdate.as_view(), name="user-profile-update"),
    path('add-delivery-offer/', v.CreateDeliveryOfferView.as_view(), name="delivery-offer-add"),
    path('delivery-detail/<int:delivery_id>/', v.DeliveryOfferDetailView.as_view(), name="delivery-offer-detail"),
    path('delivery-detail/modify/<int:delivery_id>/', v.DeliveryOfferModifyView.as_view(), name="delivery-offer-modify"),
    path('delivery-detail/delete/<int:delivery_id>/', v.DeliveryOfferDeleteView.as_view(), name="delivery-offer-delete"),
    path('user/notifications/<int:notification_id>/delete/', v.NotificationDeleteView.as_view(), name="user-notification-delete"),
    path('user/delivery-offers/', v.UserDeliveryOffer.as_view(), name="user-delivery-offers"),
    path('user/delivery-offers/<int:delivery_id>/contact/', v.UserSendMessageView.as_view(), name="user-send-message"),

    # Errors
    path('Not-allowed/', v.Http405View.as_view(), name="http_405"),
]
