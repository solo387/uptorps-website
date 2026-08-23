from django.urls import path
from . import views

urlpatterns = [
    path("detail/", views.WalletDetailView.as_view(), name="wallet-detail"),
    path("transactions/", views.TransactionListView.as_view(), name="transactions"),
    path("withdrawals/", views.WithdrawalListView.as_view(), name="withdrawals"),
    path("withdraw/", views.WithdrawalCreateView.as_view(), name="withdrawal-create"),
    path("stats/", views.WalletStatsView.as_view(), name="wallet-stats"),
    # path(
    #     "simulate-purchase/",
    #     views.SimulatePremiumPurchaseView.as_view(),
    #     name="simulate-premium-purchase",
    # ),
]
