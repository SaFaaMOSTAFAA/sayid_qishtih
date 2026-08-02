from configrations.serializers import ContactUsSerializer
from configrations.models import ContactUs
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.viewsets import ModelViewSet


class ContactUsViewSet(ModelViewSet):
    queryset = ContactUs.objects.all()
    serializer_class = ContactUsSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "contact_submit"
        return super().get_throttles()

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAdminUser()]
