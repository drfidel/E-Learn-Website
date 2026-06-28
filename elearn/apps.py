from django.contrib.admin.apps import AdminConfig


class ElearnAdminConfig(AdminConfig):
    default_site = "elearn.admin.ElearnAdminSite"
