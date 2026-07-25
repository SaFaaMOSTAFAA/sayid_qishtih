from django.db.models import Q
from django.utils import timezone
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    BasePermission,
    IsAdminUser,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .auth_serializers import RegisterSerializer
from .models import Category, Client_review, Offer, Product
from .permissions import IsAdminOrReadOnly
from .serializer import (
    CategorySerializer,
    ClientReviewSerializer,
    DashboardStatsSerializer,
    OfferSerializer,
    ProductSerializer,
    UserSummarySerializer,
)


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return obj.user == request.user or request.user.is_staff


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(RetrieveAPIView):
    serializer_class = UserSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return Category.objects.all().order_by("display_order", "id")


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Product.objects.select_related("category").all().order_by(
            "display_order", "-created_at"
        )

        if not (self.request.user and self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(is_visible=True)

        category = self.request.query_params.get("category")
        category_id = self.request.query_params.get("category_id")
        category_name = self.request.query_params.get("category_name")
        is_available = self.request.query_params.get("is_available")
        is_visible = self.request.query_params.get("is_visible")

        selected_category_id = category_id or category

        if selected_category_id:
            if selected_category_id.isdigit():
                queryset = queryset.filter(category_id=int(selected_category_id))
            else:
                queryset = queryset.none()

        if category_name:
            queryset = queryset.filter(category__name__iexact=category_name)

        if is_available is not None:
            value = is_available.lower()
            if value in ("true", "1"):
                queryset = queryset.filter(is_available=True)
            elif value in ("false", "0"):
                queryset = queryset.filter(is_available=False)

        if (
            is_visible is not None
            and self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_staff
        ):
            value = is_visible.lower()
            if value in ("true", "1"):
                queryset = queryset.filter(is_visible=True)
            elif value in ("false", "0"):
                queryset = queryset.filter(is_visible=False)

        return queryset


class OfferViewSet(ModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Offer.objects.all().order_by("-created_at")

        if not (self.request.user and self.request.user.is_authenticated and self.request.user.is_staff):
            today = timezone.localdate()
            queryset = (
                queryset.filter(is_active=True)
                .filter(Q(start_date__isnull=True) | Q(start_date__lte=today))
                .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
            )

        is_active = self.request.query_params.get("is_active")
        if (
            is_active is not None
            and self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_staff
        ):
            value = is_active.lower()
            if value in ("true", "1"):
                queryset = queryset.filter(is_active=True)
            elif value in ("false", "0"):
                queryset = queryset.filter(is_active=False)

        return queryset


class ClientReviewViewSet(ModelViewSet):
    queryset = Client_review.objects.select_related("user").all().order_by("-created_at")
    serializer_class = ClientReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DashboardStatsView(APIView):
    """Quick dashboard counters for staff."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.localdate()
        current_offers = (
            Offer.objects.filter(is_active=True)
            .filter(Q(start_date__isnull=True) | Q(start_date__lte=today))
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
            .count()
        )
        data = {
            "total_products": Product.objects.count(),
            "available_products": Product.objects.filter(is_available=True).count(),
            "unavailable_products": Product.objects.filter(is_available=False).count(),
            "current_offers": current_offers,
        }
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)
