from django.contrib import admin
from django.urls import path, include
from django.conf import settings                  # <-- YE WAPAS CHECK KARO
from django.conf.urls.static import static        # <-- YE WAPAS CHECK KARO

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), 
    path('',include('app.urls')),
    path('',include('dashboard.urls'))


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)