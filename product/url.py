from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    ClientReviewViewSet,
    DashboardStatsView,
    OfferViewSet,
    ProductViewSet,
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"offers", OfferViewSet, basename="offer")
router.register(r"client-reviews", ClientReviewViewSet, basename="client-review")

urlpatterns = [
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
] + router.urls
