from configrations.views import ConfigrationViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'configrations', ConfigrationViewSet, basename='configration')
urlpatterns = router.urls