from rest_framework.routers import DefaultRouter

from configrations.views import ContactUsViewSet

router = DefaultRouter()
router.register(r"contact-us", ContactUsViewSet, basename="contact-us")

urlpatterns = router.urls
