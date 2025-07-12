from enum import Enum


# Constants
class Currencies(Enum):
    USD = "USD"


class SubscriptionRenewalPeriod(Enum):
    MONTH = "month"


class SubscriptionStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELED = "canceled"


class StripePIStatus(Enum):
    REQUIRES_ACTION = "requires_action"
    SUCCEEDED = "succeeded"


class ResponseMessage:
    STRIPE_PAYMENT_ACTION_REQUIRED = "Stripe payment action required"
    STRIPE_PAYMENT_SUCCESS = "Stripe payment successful"
    STRIPE_PAYMENT_FAILED = "Stripe payment failed"
    STRIPE_CUSTOMER_NOT_FOUND = "Stripe customer not found"
    FREE_PLAN_ALREADY_PURCHASED = "Free plan already purchased"
    PAYMENT_METHOD_ATTACHED = "Payment method attached successfully"
    COUPON_CREATED = "Coupon created successfully"


class Duration(Enum):
    FOREVER = "forever"
    ONCE = "once"
    REPEATING = "repeating"
