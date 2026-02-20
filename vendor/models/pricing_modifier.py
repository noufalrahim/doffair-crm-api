from odmantic import Model

class PricingModifier(Model):
    pricing_id: str          # FK to VendorService
    modifier_type: str       # BREED_SIZE
    modifier_key: str        # SMALL | MEDIUM | LARGE
    modifier_value: float    # +10, +20
