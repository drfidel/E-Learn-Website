from .models import Payment


def verify_payment(payment: Payment) -> bool:
    """Placeholder verification logic for Stripe/Flutterwave webhooks."""
    return bool(payment.external_reference)
