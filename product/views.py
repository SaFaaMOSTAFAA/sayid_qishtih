from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.deletion import ProtectedError
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView, GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import SAFE_METHODS, AllowAny, BasePermission, IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from .auth_serializers import ClientSerializer, RegisterSerializer
from .image_utils import (
    apply_product_image_update,
    create_product_images,
    get_remove_image_ids,
    validate_product_image_update,
    validate_uploaded_product_images,
)
from .models import Category, Client_review, Offer, Product
from .serializer import (
    CategorySerializer,
    ClientReviewSerializer,
    DashboardStatsSerializer,
    OfferSerializer,
    ProductMultipartRequestSerializer,
    ProductSerializer,
    UserSummarySerializer,
)


def parse_boolean_query_param(field_name, value):
    normalized = str(value).lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValidationError({field_name: ["Enter a valid boolean value."]})


class StaffWriteOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return bool(
            request.user
            and request.user.is_authenticated
            and (obj.user == request.user or request.user.is_staff)
        )


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth_register"


class LoginView(TokenObtainPairView):
    throttle_scope = "auth_login"


class MeView(RetrieveAPIView):
    serializer_class = UserSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ClientListView(ListAPIView):
    serializer_class = ClientSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ["first_name", "last_name", "email", "username"]

    def get_queryset(self):
        return (
            get_user_model()
            .objects.filter(is_staff=False, is_superuser=False)
            .exclude(username="legacy_client")
            .order_by("-date_joined", "-id")
        )


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [StaffWriteOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "This category cannot be deleted because it contains products."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [StaffWriteOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @extend_schema(
        request=ProductMultipartRequestSerializer,
        responses=ProductSerializer,
        description=(
            'Upload product images by repeating multipart field "images". '
            'Remove existing images by repeating multipart field "remove_image_ids". '
            "A product can have at most five images; images[0] is the primary image."
        ),
    )
    def create(self, request, *args, **kwargs):
        uploaded_images = request.FILES.getlist("images")
        validate_uploaded_product_images(uploaded_images)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.perform_create(serializer)
            create_product_images(serializer.instance, uploaded_images)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        request=ProductMultipartRequestSerializer,
        responses=ProductSerializer,
        description=(
            'Upload product images by repeating multipart field "images". '
            'Remove existing images by repeating multipart field "remove_image_ids". '
            "Omitted image fields preserve existing images."
        ),
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        uploaded_images = request.FILES.getlist("images")
        remove_image_ids = get_remove_image_ids(request)
        validate_uploaded_product_images(uploaded_images)
        validate_product_image_update(instance, uploaded_images, remove_image_ids)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.perform_update(serializer)
            apply_product_image_update(serializer.instance, uploaded_images, remove_image_ids)
        if getattr(serializer.instance, "_prefetched_objects_cache", None):
            serializer.instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    @extend_schema(
        request=ProductMultipartRequestSerializer,
        responses=ProductSerializer,
        description=(
            'Upload product images by repeating multipart field "images". '
            'Remove existing images by repeating multipart field "remove_image_ids". '
            "Omitted image fields preserve existing images."
        ),
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("category", int, OpenApiParameter.QUERY),
            OpenApiParameter("category_id", int, OpenApiParameter.QUERY),
            OpenApiParameter("category_name", str, OpenApiParameter.QUERY),
            OpenApiParameter("is_available", bool, OpenApiParameter.QUERY),
            OpenApiParameter("is_visible", bool, OpenApiParameter.QUERY),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Product.objects.select_related("category").prefetch_related("images").all()
        is_staff = bool(self.request.user and self.request.user.is_staff)

        if not is_staff:
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
                raise ValidationError({"category": ["A valid integer is required."]})

        if category_name:
            queryset = queryset.filter(category__name__iexact=category_name)

        if is_available is not None:
            queryset = queryset.filter(is_available=parse_boolean_query_param("is_available", is_available))

        if is_visible is not None:
            parsed_is_visible = parse_boolean_query_param("is_visible", is_visible)
            if not is_staff and parsed_is_visible is False:
                raise PermissionDenied("Only staff users can list hidden products.")
            queryset = queryset.filter(is_visible=parsed_is_visible)

        return queryset


class OfferViewSet(ModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [StaffWriteOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @extend_schema(
        parameters=[
            OpenApiParameter("is_active", bool, OpenApiParameter.QUERY),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Offer.objects.all()
        is_staff = bool(self.request.user and self.request.user.is_staff)
        if not is_staff:
            return queryset.filter(*Offer.currently_active_filter())

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=parse_boolean_query_param("is_active", is_active))
        return queryset


class DashboardStatsView(GenericAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = DashboardStatsSerializer

    @extend_schema(responses=DashboardStatsSerializer)
    def get(self, request):
        current_offers = Offer.objects.filter(*Offer.currently_active_filter()).count()
        total_products = Product.objects.count()
        available_products = Product.objects.filter(is_available=True).count()

        serializer = self.get_serializer({
            "total_products": total_products,
            "available_products": available_products,
            "unavailable_products": total_products - available_products,
            "current_offers": current_offers,
        })
        return Response(serializer.data)


class ClientReviewViewSet(ModelViewSet):
    queryset = Client_review.objects.select_related("user").all()
    serializer_class = ClientReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "review_create"
        return super().get_throttles()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
