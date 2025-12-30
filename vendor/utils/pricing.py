from core.enums import DiscountType


def calculate_final_price(
    base_price: float,
    discount_type: DiscountType,
    discount_value: float | None,
) -> float:
    if discount_type == DiscountType.NONE:
        return base_price

    if discount_type == DiscountType.FLAT:
        return max(0, base_price - (discount_value or 0))

    if discount_type == DiscountType.PERCENT:
        return max(0, base_price * (1 - (discount_value or 0) / 100))

    return base_price
