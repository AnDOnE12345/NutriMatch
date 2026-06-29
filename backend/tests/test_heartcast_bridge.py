import unittest

from tools.heartcast_bridge import HeartRateParseError, parse_heart_rate_measurement


class HeartCastBridgeParserTests(unittest.TestCase):
    def test_parse_uint8_heart_rate(self):
        self.assertEqual(parse_heart_rate_measurement(bytes([0x00, 75])), 75)

    def test_parse_uint16_heart_rate(self):
        self.assertEqual(parse_heart_rate_measurement(bytes([0x01, 0x2C, 0x01])), 300)

    def test_ignores_optional_trailing_fields(self):
        self.assertEqual(parse_heart_rate_measurement(bytes([0x00, 91, 0x99, 0x88])), 91)

    def test_rejects_short_payload(self):
        with self.assertRaises(HeartRateParseError):
            parse_heart_rate_measurement(bytes([0x00]))


if __name__ == "__main__":
    unittest.main()
