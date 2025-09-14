# core/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Dashboard (KYC-gated inside the view)
    path('dashboard/', views.dashboard, name='dashboard'),

    # KYC flow
    path('kyc/start/', views.kyc_start, name='kyc_start'),
    path('kyc/status/', views.kyc_status, name='kyc_status'),

    # Vendors / Trades
    path('p2p-info/', views.p2p_info, name='p2p_info'),
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('trade/<int:vendor_id>/start/', views.start_trade, name='start_trade'),
    path('trade/<int:trade_id>/', views.trade_detail, name='trade_detail'),
    path('staff/chat/<int:trade_id>/', views.staff_trade_chat, name='staff_trade_chat'),

    # Downloads
    path('download-app/', views.download_app, name='download_app'),

    # APIs (DRF)
    path('api/register/', views.RegisterView.as_view(), name='api_register'),
    path('api/login/', views.LoginView.as_view(), name='api_login'),
    path('api/kyc/', views.KYCView.as_view(), name='api_kyc'),
    path('api/change-password/', views.ChangePasswordView.as_view(), name='api_change_password'),
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    #Admin add
    path("link-wallet/", views.link_wallet, name="link_wallet"),
    path('deposits/create/', views.create_deposit, name='create_deposit'),

    # Download CSV
    path('statement.csv', views.export_statement_csv, name='export_statement_csv'),

    # Take Profit and Bonus
    path('take-profit/', views.take_profit, name='take_profit'),
    path('take-bonus/', views.take_bonus, name='take_bonus'),

    # Admin create trade
    path('create-trade/', views.create_trade, name='create_trade'),
    path('close-trade/<int:trade_id>/', views.close_trade, name='close_trade'),
    path('api/watchlist-quotes/', views.watchlist_quotes, name='watchlist_quotes'),
    path('api/recent-activity/', views.recent_activity, name='recent_activity'),

    # Admin from user deposit and withdraw
    path('deposit/submit-proof/', views.submit_deposit_proof, name='submit_deposit_proof'),
    path('withdraw/request/', views.request_withdrawal, name='request_withdrawal'),
    
    # Copy trading 
    path('copy-trading/', views.copy_list, name='copy_list'),
    path('copy-trading/<int:expert_id>/start/', views.copy_start, name='copy_start'),
    path('copy-trading/<int:expert_id>/cancel/', views.copy_cancel, name='copy_cancel'),

    #Upgrade Account
    path("upgrade/", views.upgrade_plans, name="upgrade_plans"),
    path("api/upgrade-status/", views.upgrade_status_json, name="upgrade_status_json"),

    #Extra buttons
    path("api/transactions/recent/", views.api_transactions_recent, name="api_transactions_recent"),
    path("api/withdrawals/recent/", views.api_withdrawals_recent, name="api_withdrawals_recent"),
    path("api/trades/recent/", views.api_trades_recent, name="api_trades_recent"),

    path("me/profile/", views.me_profile, name="me_profile"),        # GET (prefill) + POST (save)
    path("me/password/", views.me_password, name="me_password"),      # POST only
    path("notifications/<int:pk>/read/", views.notification_mark_read, name="notif_mark_read"),  # Broadcast Notification
]
