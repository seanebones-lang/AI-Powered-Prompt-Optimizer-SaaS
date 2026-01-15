"""
Stripe payment integration for premium subscription tiers.

Handles checkout sessions, webhooks, and subscription management.
Pricing tiers: Free ($0), Pro ($19.99/mo), Enterprise ($99.99/mo)
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import os

logger = logging.getLogger(__name__)

# Check if Stripe is available
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe not installed. Payment features disabled.")


class PricingTier(Enum):
    """Subscription pricing tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class TierConfig:
    """Configuration for a pricing tier."""
    name: str
    price_id: Optional[str]
    monthly_price: int  # in cents
    daily_limit: int
    features: list


# Pricing configuration
PRICING_TIERS: Dict[PricingTier, TierConfig] = {
    PricingTier.FREE: TierConfig(
        name="Free",
        price_id=None,
        monthly_price=0,
        daily_limit=5,
        features=[
            "5 optimizations per day",
            "Basic 4-D analysis",
            "Community support"
        ]
    ),
    PricingTier.PRO: TierConfig(
        name="Pro",
        price_id=os.getenv("STRIPE_PRICE_ID_PRO"),
        monthly_price=1999,  # $19.99
        daily_limit=100,
        features=[
            "100 optimizations per day",
            "RAG enhancement",
            "Priority processing",
            "Export to JSON/Markdown/PDF",
            "Email support",
            "API access"
        ]
    ),
    PricingTier.ENTERPRISE: TierConfig(
        name="Enterprise",
        price_id=os.getenv("STRIPE_PRICE_ID_ENTERPRISE"),
        monthly_price=9999,  # $99.99
        daily_limit=1000,
        features=[
            "1000 optimizations per day",
            "Full RAG with custom collections",
            "Batch processing",
            "Custom agent configurations",
            "A/B testing",
            "SLA guarantee",
            "Dedicated support",
            "Webhook notifications"
        ]
    )
}


class PaymentService:
    """Handles Stripe payment operations."""

    def __init__(self):
        """Initialize the payment service."""
        if not STRIPE_AVAILABLE:
            logger.warning("Stripe SDK not available")
            return

        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        if self.api_key:
            stripe.api_key = self.api_key
            logger.info("Stripe payment service initialized")
        else:
            logger.warning("STRIPE_SECRET_KEY not set. Payment features disabled.")

    def is_available(self) -> bool:
        """Check if Stripe is properly configured."""
        return STRIPE_AVAILABLE and bool(self.api_key)

    def create_checkout_session(
        self,
        user_id: int,
        user_email: str,
        tier: PricingTier,
        success_url: str,
        cancel_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Stripe Checkout session for subscription.

        Args:
            user_id: Database user ID
            user_email: User's email address
            tier: Pricing tier to subscribe to
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel

        Returns:
            Dict with session_id and checkout_url, or None on error
        """
        if not self.is_available():
            logger.error("Payment service not available")
            return None

        tier_config = PRICING_TIERS.get(tier)
        if not tier_config or not tier_config.price_id:
            logger.error(f"Invalid tier or missing price_id: {tier}")
            return None

        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                payment_method_types=["card"],
                line_items=[{
                    "price": tier_config.price_id,
                    "quantity": 1
                }],
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                customer_email=user_email,
                client_reference_id=str(user_id),
                metadata={
                    "user_id": str(user_id),
                    "tier": tier.value
                },
                automatic_tax={"enabled": True},
                subscription_data={
                    "metadata": {
                        "user_id": str(user_id),
                        "tier": tier.value
                    }
                },
                # Idempotency key to prevent duplicate charges
                idempotency_key=f"checkout_{user_id}_{tier.value}_{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            )

            logger.info(f"Created checkout session for user {user_id}, tier {tier.value}")
            return {
                "session_id": session.id,
                "checkout_url": session.url
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {str(e)}")
            return None

    def create_customer_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> Optional[str]:
        """
        Create a Stripe Customer Portal session for self-service management.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal

        Returns:
            Portal URL or None on error
        """
        if not self.is_available():
            return None

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session.url

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {str(e)}")
            return None

    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.

        Args:
            payload: Raw webhook payload
            signature: Stripe signature header

        Returns:
            Dict with event type and relevant data
        """
        if not self.is_available() or not self.webhook_secret:
            return {"error": "Webhook handling not configured"}

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
        except ValueError:
            return {"error": "Invalid payload"}
        except stripe.error.SignatureVerificationError:
            return {"error": "Invalid signature"}

        event_type = event["type"]
        data = event["data"]["object"]

        result = {"event_type": event_type, "handled": True}

        # Handle specific events
        if event_type == "checkout.session.completed":
            result["action"] = "activate_subscription"
            result["user_id"] = data.get("client_reference_id")
            result["subscription_id"] = data.get("subscription")
            result["customer_id"] = data.get("customer")

        elif event_type == "invoice.payment_succeeded":
            result["action"] = "record_payment"
            result["invoice_id"] = data.get("id")
            result["amount_paid"] = data.get("amount_paid")
            result["customer_id"] = data.get("customer")

        elif event_type == "customer.subscription.updated":
            result["action"] = "update_subscription"
            result["subscription_id"] = data.get("id")
            result["status"] = data.get("status")
            result["current_period_end"] = data.get("current_period_end")

        elif event_type == "customer.subscription.deleted":
            result["action"] = "cancel_subscription"
            result["subscription_id"] = data.get("id")

        else:
            result["handled"] = False

        logger.info(f"Handled webhook event: {event_type}")
        return result

    def get_subscription_status(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription status from Stripe.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Subscription details or None
        """
        if not self.is_available():
            return None

        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription: {str(e)}")
            return None

    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> bool:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of billing period

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            if at_period_end:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                stripe.Subscription.delete(subscription_id)

            logger.info(f"Cancelled subscription: {subscription_id}")
            return True

        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return False


def get_tier_for_user(user) -> PricingTier:
    """
    Determine the pricing tier for a user based on their subscription status.

    Args:
        user: User database object

    Returns:
        PricingTier enum value
    """
    # For personal use, always return ENTERPRISE tier to access all features
    return PricingTier.ENTERPRISE


def get_daily_limit_for_tier(tier: PricingTier) -> int:
    """Get daily optimization limit for a tier."""
    return PRICING_TIERS[tier].daily_limit


# Global payment service instance
payment_service = PaymentService()
