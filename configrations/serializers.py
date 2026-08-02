from configrations.models import ContactUs
from rest_framework import serializers

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

    def validate_phone_number(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value
