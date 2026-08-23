from django.urls import path
from . import views

urlpatterns = [
    path('packages/', views.PackageListView.as_view(), name='packages'),
    path('purchase/', views.PurchaseView.as_view(), name='purchase'),
]