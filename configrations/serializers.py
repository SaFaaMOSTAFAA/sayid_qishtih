from rest_framework import serializers

from configrations.models import ContactUs


class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = (
            "id",
            "name",
            "name_ar",
            "phone_number",
            "message",
            "message_ar",
            "created_at",
        )
        read_only_fields = ("id", "created_at")
