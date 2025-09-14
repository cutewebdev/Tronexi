from django.contrib import admin
from django.urls import path, include, re_path
from core import views
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

# Redirect function for blocking default admin URL
def redirect_home(request):
    return redirect("/")  # Homepage

urlpatterns = [
    # Your custom admin login URL
    path("backofficecuteweb/", admin.site.urls),

    # Redirect anything starting with 'admin' to home
    re_path(r"^admin.*$", redirect_home),

    # Your main site routes
    path('', include('core.urls')),
    path('p2p/', views.p2p_info, name='p2p'),

    # ✅ NEW: alias so /staff/chat/<id>/ loads the trade detail page
    path('staff/chat/<int:trade_id>/', views.trade_detail, name='staff_chat'),

    path("staff/chat/<int:trade_id>/", views.staff_trade_chat, name="staff_chat"),
]

# Language support
urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('i18n/setlang/', set_language, name='set_language'),

    # (Optional) language-prefixed alias (e.g., /en/staff/chat/9/)
    path('staff/chat/<int:trade_id>/', views.trade_detail, name='staff_chat_i18n'),
)

# ✅ Serve user-uploaded media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
