from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings


from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/',include('accounts.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/products/', include('products.urls')),
    path('api/notification/',include('notification.urls'))
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)