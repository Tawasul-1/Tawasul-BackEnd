from django.urls import path
from users import views
from users.views import CancelSubscriptionView, PaymobGetPaymentUrlView, SubscriptionStatusView, UserListView, paymob_success_redirect

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/", views.logout, name="logout"),
    path("profile/", views.UserProfileView.as_view(), name="user-profile"),
    path('activate/<str:token>/', views.ActivateAccountView.as_view(), name='activate-account'),
    path("password-reset/", views.RequestPasswordResetView.as_view(), name="request-password-reset"),
    path("password-reset/<str:token>/", views.ResetPasswordView.as_view(), name="reset-password"),
    path("update-profile/", views.UserUpdateView.as_view(), name="update-profile"),
    path("premium-protected/", views.PremiumProtectedView.as_view(), name="premium-protected"),
    path('payment/init/', PaymobGetPaymentUrlView.as_view(), name='initiate-payment'),
    path('payment/success/', paymob_success_redirect, name='payment-success'),
    path('subscription/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('subscription/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path("all-users/", UserListView.as_view(), name="all-users"),
]
