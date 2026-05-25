from django.contrib import admin
from django.urls import path
from Smarko_App import views
from Smarko_App import views_lgpd

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verificar-2fa/', views.verificar_2fa_view, name='verificar_2fa'),
    path('reset_password/', views.reset_password_view, name="reset_password"),
    path('reset_password_sent/', views.reset_password_sent_view, name="password_reset_done"),
    path('reset_confirm/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('ping/', views.ping_view, name='ping'),
    path('privacy/', views.privacy_policy_view, name='privacy'),
    path('consent/', views.register_consent_view, name='consent'),
    path('update-consent/', views.update_consent_view, name='update_consent'),
    path('user-data/', views.user_data_view, name='user_data'),
    path('data-access-request/', views.export_user_data_view, name='export_data'),
    path('revoke-consent/', views.revoke_consent_view, name='revoke_consent'),
    path('request-deletion/', views.request_account_deletion_view, name='request_deletion'),
    path('cancel-deletion/', views.cancel_account_deletion_view, name='cancel_deletion'),

    # LGPD Compliance Endpoints (SPRINT 3)
    path('api/user/data-export/', views_lgpd.data_export_view, name='lgpd_data_export'),
    path('api/user/account-deletion/', views_lgpd.account_deletion_request_view, name='lgpd_account_deletion'),
    path('api/user/account-deletion/cancel/', views_lgpd.account_deletion_cancel_view, name='lgpd_cancel_deletion'),
    path('api/user/consent/', views_lgpd.consent_records_view, name='lgpd_consent_records'),
    path('api/user/consent/revoke/', views_lgpd.consent_revocation_view, name='lgpd_revoke_consent'),
]