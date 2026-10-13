"""No API calls: test deterministic business validation."""
import unittest
from order_extractor import OrderInfo, validate_order

class ValidationTests(unittest.TestCase):
    def test_valid(self):
        draft = validate_order(OrderInfo(product="女装", quantity=20, unit_price=1500, currency="PHP", delivery_date=None))
        self.assertEqual(draft.total_amount, 30000)
        self.assertEqual(draft.status, "pending_confirmation")
    def test_missing_price(self):
        with self.assertRaises(ValueError):
            validate_order(OrderInfo(product="女装", quantity=20, unit_price=None, currency="PHP", delivery_date=None))
    def test_zero_quantity(self):
        with self.assertRaises(ValueError):
            validate_order(OrderInfo(product="女装", quantity=0, unit_price=1500, currency="PHP", delivery_date=None))
    def test_bad_date(self):
        with self.assertRaises(ValueError):
            validate_order(OrderInfo(product="女装", quantity=20, unit_price=1500, currency="PHP", delivery_date="2026-02-30"))

if __name__ == "__main__":
    unittest.main()
