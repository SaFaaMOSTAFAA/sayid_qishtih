from configrations.serializers import ContactUsSerializer
from configrations.models import ContactUs
from rest_framework.viewsets import ModelViewSet


class ContactUsViewSet(ModelViewSet):
    queryset = ContactUs.objects.all()
    serializer_class = ContactUsSerializer