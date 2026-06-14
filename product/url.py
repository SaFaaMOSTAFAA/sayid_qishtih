from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, CategoryViewSet, ClientReviewViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'client-reviews', ClientReviewViewSet, basename='client-review')

urlpatterns = router.urls
