# premium/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import PremiumPackageSerializer, PurchaseSerializer
from accounts.models import User
from .models import PremiumPackage
from wallet.services import onlineCheckout


class PackageListView(APIView):
    """GET /api/premium/packages/ - List available packages"""

    def get(self, request):
        packages = PremiumPackage.objects.filter(status=PremiumPackage.Status.ACTIVE)
        serializer = PremiumPackageSerializer(packages, many=True)
        return Response(serializer.data)


class PurchaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PurchaseSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        premium_roles = [User.Roles.PREMIUM_STUDENT, User.Roles.PREMIUM_TEACHER]
        if user.role in premium_roles:
            return Response(
                {
                    "message": "You already have an active premium package and cannot purchase another."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Always bind the purchase to the authenticated user.
        # Client-supplied email in payout_info is ignored/overwritten.
        payout_info = dict(serializer.validated_data["payout_info"])
        payout_info["email"] = user.email

        boolStatus, url, meta = onlineCheckout(
            serializer.validated_data["package"].id,
            serializer.validated_data["reference"],
            payout_info,
        )
        if boolStatus:
            return Response(
                {
                    "checkout_url": url,
                    "simulated": meta.get("simulated", True),
                    "message": meta.get("message"),
                    "simulation_outcome": meta.get("simulation_outcome"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "message": meta.get(
                    "message", "Something went wrong try again....."
                ),
                "simulated": meta.get("simulated", False),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
