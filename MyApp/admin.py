from django.contrib import admin
import MyApp.models as m

# Register your models here.

admin.site.register(m.User)
admin.site.register(m.UserProfile)
admin.site.register(m.DeliveryOffer)
admin.site.register(m.DeliveryInfo)
admin.site.register(m.Message)
admin.site.register(m.Notification)
