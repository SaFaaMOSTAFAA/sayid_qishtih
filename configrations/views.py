from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.viewsets import ModelViewSet

from configrations.models import ContactUs
from configrations.serializers import ContactUsSerializer


class ContactUsViewSet(ModelViewSet):
    """
    Public can submit contact messages (POST).
    Staff can list / retrieve / delete messages.
    """

    queryset = ContactUs.objects.all().order_by("-created_at")
    serializer_class = ContactUsSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAdminUser()]
