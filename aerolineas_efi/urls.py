"""
URL configuration for aerolineas_efi project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

# URLs sin traducir
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

# URLs con traducción
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('gestion.urls')),
    prefix_default_language=False
)
