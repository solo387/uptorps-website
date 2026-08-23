# wallets/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Wallet, Transaction, Withdrawal
from .permissions import IsWalletOwnerOrAdmin
from .serializers import (
    WalletSerializer,
    TransactionSerializer,
    WithdrawalListSerializer,
    WithdrawalSerializer,
)

# from wallet.services import confirm_premium_purchase

User = get_user_model()


class WalletDetailView(APIView):
    permission_classes = [IsAuthenticated, IsWalletOwnerOrAdmin]

    def get(self, request):
        """GET wallet balance & stats"""
        wallet = get_object_or_404(Wallet, user=request.user)
        self.check_object_permissions(request, wallet)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)


class TransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET user transactions"""
        transactions = Transaction.objects.filter(wallet=request.user.wallet).order_by(
            "-created_at"
        )
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class WithdrawalListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET user withdrawals"""
        withdrawals = Withdrawal.objects.filter(wallet=request.user.wallet).order_by(
            "-created_at"
        )
        serializer = WithdrawalListSerializer(withdrawals, many=True)
        return Response(serializer.data)


class WithdrawalCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """POST new withdrawal request"""
        serializer = WithdrawalSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            withdrawal = serializer.save()  # ✅ Triggers signals
            return Response(
                {
                    "id": str(withdrawal.id),
                    "message": "Withdrawal request created",
                    "status": withdrawal.status,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WalletStatsView(APIView):
    """Wallet stats with object-level permission checks.

    - No query param → caller's wallet
    - ``?username=`` → resolve that user's wallet, then
      ``IsWalletOwnerOrAdmin.has_object_permission`` decides access

    Ownership is by user PK, not username string equality, so a matching
    username alone cannot unlock someone else's wallet.
    """

    permission_classes = [IsAuthenticated, IsWalletOwnerOrAdmin]

    def get(self, request):
        username = request.query_params.get("username")

        if username:
            wallet = get_object_or_404(Wallet, user__username=username)
        else:
            wallet = get_object_or_404(Wallet, user=request.user)

        self.check_object_permissions(request, wallet)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)


# Service purchase view
# class HubtelWebhookView(APIView):
#     permission_classes = []  # webhooks are not user authenticated

#     def post(self, request):
#         # step 1 — verify the webhook is genuinely from Hubtel
#         # Hubtel sends a signature header you validate here
#         payload = request.data

#         if payload.get("Status") == "Success":
#             user_id = payload["ClientReference"]  # you set this when initiating payment
#             amount = payload["Amount"]
#             reference = payload["TransactionId"]

#             user = User.objects.get(id=user_id)
#             confirm_premium_purchase(user, reference, amount)

#         return Response({"message": "ok"}, status=200)


# class SimulatePremiumPurchaseView(APIView):
#     """
#     Simulates a successful or failed payment gateway webhook.
#     FOR TESTING ONLY — remove or protect this endpoint in production.
#     """

#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         status = request.data.get("status")  # 'success' or 'failure'
#         user_id = request.data.get("user_id")
#         amount = request.data.get("amount", 100.00)
#         reference = request.data.get("reference", f"SIM-TEST-{user_id}")

#         if status == "success":
#             try:
#                 user = User.objects.get(id=user_id)
#                 wallet = confirm_premium_purchase(
#                     user=user, payment_reference=reference, purchase_amount=amount
#                 )

#                 if wallet is None:
#                     return Response({"message": "User is already premium"}, status=200)

#                 return Response(
#                     {
#                         "message": "Premium purchase confirmed",
#                         "wallet_id": wallet.id,
#                         "user_role": user.role,
#                     },
#                     status=200,
#                 )

#             except User.DoesNotExist:
#                 return Response({"message": "User not found"}, status=404)

#             except Exception as e:
#                 return Response({"message": f"Purchase failed: {str(e)}"}, status=500)

#         elif status == "failure":
#             # payment failed — do nothing
#             # user stays as normal student
#             return Response({"message": "Payment failed — no changes made"}, status=200)

#         return Response(
#             {"message": "Invalid status. Use 'success' or 'failure'"}, status=400
#         )
