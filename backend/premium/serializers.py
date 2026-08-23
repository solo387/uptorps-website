# premium/serializers.py
from rest_framework import serializers
from .models import PremiumPackage
from wallet.models import Transaction

class PremiumPackageSerializer(serializers.ModelSerializer):
    """Public package listing"""
    class Meta:
        model = PremiumPackage
        fields = ['id', 'name', 'price', 'duration_days', 'max_referrals', 'status']

class PurchaseSerializer(serializers.Serializer):
    """Purchase request validation.

    Buyer identity comes from the authenticated user in the view —
    any email in payout_info is overwritten server-side.
    """
    package_id = serializers.UUIDField()
    reference = serializers.CharField(max_length=50)
    # Payment/contact metadata only, e.g. {"method": "Mobile Money", "detail": "012345"}
    payout_info = serializers.JSONField()

    def validate_package_id(self, value):
        """Package must exist + active"""
        package = PremiumPackage.objects.filter(
            id=value, status=PremiumPackage.Status.ACTIVE
        )
        if not package.exists():
            raise serializers.ValidationError("Invalid or inactive package")
        return package.first()

    def validate_reference(self, value):
        """Reference must be unique"""
        if Transaction.objects.filter(reference=value).exists():
            raise serializers.ValidationError("Reference already used")
        return value

    def validate_payout_info(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("payout_info must be an object")
        return value

    def validate(self, data):
        """All validations passed"""
        data["package"] = data["package_id"]  # Store package object
        return data