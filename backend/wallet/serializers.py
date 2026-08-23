# wallets/serializers.py
from rest_framework import serializers
# from django.contrib.auth import get_user_model
from .models import Wallet, Transaction, Withdrawal

# User = get_user_model()

class WalletSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance', 'total_earned', 'currency', 'status', 'created_at']
        read_only_fields = fields  # Fully readonly

class TransactionSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'wallet', 'type', 'direction', 'amount', 'status', 
                 'reference', 'description', 'created_at']
        read_only_fields = fields  # Fully readonly

class PayoutInfoSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['Mobile Money', 'Bank'])
    detail = serializers.CharField(max_length=50)

class WithdrawalSerializer(serializers.ModelSerializer):
    wallet = serializers.StringRelatedField()
    payout_info = PayoutInfoSerializer()
    
    class Meta:
        model = Withdrawal
        fields = ['id', 'wallet', 'amount', 'payout_info', 'status', 
                 'processor', 'created_at', 'updated_at']
        read_only_fields = ['id', 'wallet', 'status', 'processor', 
                           'created_at', 'updated_at']
    
    def validate_amount(self, value):
        """Min withdrawal GH₵10, not more than balance"""
        if value < 10:
            raise serializers.ValidationError("Minimum withdrawal is GH₵10")
        wallet = self.context['request'].user.wallet
        if value > wallet.balance:
            raise serializers.ValidationError("Insufficient balance")
        return value
    
    def validate_payout_info(self, value):
        """Validate payout method + detail"""
        method = value.get('method')
        detail = value.get('detail')
        if not method or not detail:
            raise serializers.ValidationError("Both method and detail required")
        return value
    
    def create(self, validated_data):
        payout_info = validated_data.pop('payout_info')
        withdrawal = Withdrawal.objects.create(
            wallet=self.context['request'].user.wallet,
            amount=validated_data['amount'],
            payout_info=payout_info
        )
        return withdrawal

class WithdrawalListSerializer(serializers.ModelSerializer):
    """List view - less detail"""
    wallet = serializers.StringRelatedField()
    
    class Meta:
        model = Withdrawal
        fields = ['id', 'wallet', 'amount', 'status', 'created_at']

# Service purchase serializer