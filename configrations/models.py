from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Configuration(models.Model):
    certificate_image = models.ImageField(_("certificate_image"),
                                          upload_to='configurations/', null=True, blank=True)
    certificate_description = models.TextField(_("certificate_description"), blank=True)
    certificate_description_ar = models.TextField(_("certificate_description_ar"), null=True, blank=True)
    Our_message = models.TextField(_("Our_message"), blank=True)
    Our_message_ar = models.TextField(_("Our_message_ar"), null=True, blank=True)
    Our_vision = models.TextField(_("Our_vision"), blank=True)
    Our_vision_ar = models.TextField(_("Our_vision_ar"), null=True, blank=True)
    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)
    email = models.EmailField(_("email"), max_length=254, blank=True)
    phone_number = models.CharField(_("phone_number"), max_length=20, blank=True)
    address = models.CharField(_("address"), max_length=255, blank=True)
    address_ar = models.CharField(_("address_ar"), max_length=255, null=True, blank=True)
    Technical_innovation = models.TextField(_("Technical_innovation"), blank=True)
    Technical_innovation_ar = models.TextField(_("Technical_innovation_ar"), null=True, blank=True)
    Social_responsibility = models.TextField(_("Social responsibility"), blank=True)
    Social_responsibility_ar = models.TextField(_("Social responsibility_ar"), null=True, blank=True)
    Customer_experience = models.TextField(_("Customer experience"), blank=True)
    Customer_experience_ar = models.TextField(_("Customer experience_ar"), null=True, blank=True)
    About_the_Center = models.TextField(_("About_the_Center"), blank=True)
    About_the_Center_ar = models.TextField(_("About_the_Center_ar"), null=True, blank=True)
    Future_vision = models.TextField(_("Future vision"), blank=True)
    Future_vision_ar = models.TextField(_("Future vision_ar"), null=True, blank=True)


    def __str__(self):
        return "Site Configuration" 
    class Meta:
        verbose_name = _("Configuration")
        verbose_name_plural = _("Configurations")