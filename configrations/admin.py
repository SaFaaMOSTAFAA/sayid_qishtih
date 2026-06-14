from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Configuration


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('certificate_image', 'certificate_description_summary', 'Our_message_summary', 'Our_vision_summary', 'created_at', 'email', 'phone_number', 'address', 'Technical_innovation_summary', 'Social_responsibility_summary', 'Customer_experience_summary') # noqa

    def certificate_description_summary(self, obj):
        return obj.certificate_description[:50] + '...' if len(obj.certificate_description) > 50 else obj.certificate_description # noqa
    certificate_description_summary.short_description = _('certificate_description')

    def Our_message_summary(self, obj):
        return obj.Our_message[:50] + '...' if len(obj.Our_message) > 50 else obj.Our_message # noqa
    Our_message_summary.short_description = _('Our message')

    def Our_vision_summary(self, obj):
        return obj.Our_vision[:50] + '...' if len(obj.Our_vision) > 50 else obj.Our_vision # noqa
    Our_vision_summary.short_description = _('Our vision')

    def Technical_innovation_summary(self, obj):
        return obj.Our_vision[:50] + '...' if len(obj.Our_vision) > 50 else obj.Our_vision # noqa
    Technical_innovation_summary.short_description = _('Technical innovation')
    def Social_responsibility_summary(self, obj):
        return obj.Social_responsibility[:50] + '...' if len(obj.Social_responsibility) > 50 else obj.Social_responsibility # noqa
    Social_responsibility_summary.short_description = _('Social responsibility')
    def Customer_experience_summary(self, obj):
        return obj.Customer_experience[:50] + '...' if len(obj.Customer_experience) > 50 else obj.Customer_experience # noqa
    Customer_experience_summary.short_description = _('Customer experience')
    def certificate_image(self, obj):
        if obj.certificate_image:
            return format_html(
                '<img src="{}" width="50" height="50" '
                'style="object-fit: cover; border-radius: 5px;" />',
                obj.certificate_image.url)
        return "No Image"
    certificate_image.short_description = _('certificate_image')
    def Future_vision_summary(self, obj):
        return obj.Future_vision[:50] + '...' if len(obj.Future_vision) > 50 else obj.Future_vision # noqa
    Future_vision_summary.short_description = _('Future vision')

    def About_the_Center_summary(self, obj):
        return obj.About_the_Center[:50] + '...' if len(obj.About_the_Center) > 50 else obj.About_the_Center # noqa
    About_the_Center_summary.short_description = _('About the Center')

