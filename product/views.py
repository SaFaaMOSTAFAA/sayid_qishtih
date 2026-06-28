from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import SAFE_METHODS, AllowAny, BasePermission, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet

from .auth_serializers import RegisterSerializer
from .models import Category, Client_review, Product
from .serializer import CategorySerializer, ClientReviewSerializer, ProductSerializer, UserSummarySerializer


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
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.select_related("category").all().order_by("-created_at")

        category = self.request.query_params.get("category")
        category_id = self.request.query_params.get("category_id")
        category_name = self.request.query_params.get("category_name")

        selected_category_id = category_id or category

        if selected_category_id:
            if selected_category_id.isdigit():
                queryset = queryset.filter(category_id=int(selected_category_id))
            else:
                queryset = queryset.none()

        if category_name:
            queryset = queryset.filter(category__name__iexact=category_name)

        return queryset


class ClientReviewViewSet(ModelViewSet):
    queryset = Client_review.objects.select_related("user").all().order_by("-created_at")
    serializer_class = ClientReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
