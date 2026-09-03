import unittest

from workbook_generator import _generation_blocked


class WorkbookAccessTest(unittest.TestCase):
    def test_free_users_are_blocked(self):
        self.assertTrue(_generation_blocked("assessor", "free", 5, False, {"platform_quota": 5}))

    def test_platform_pass_requires_byok(self):
        policy = {"platform_quota": 0}
        self.assertTrue(_generation_blocked("assessor", "platform_pass", 0, False, policy))
        self.assertFalse(_generation_blocked("assessor", "platform_pass", 0, True, policy))

    def test_lifetime_and_enterprise_allow_platform_fallback(self):
        policy = {"platform_quota": None}
        self.assertFalse(_generation_blocked("assessor", "lifetime", 0, False, policy))
        self.assertFalse(_generation_blocked("assessor", "enterprise", 0, False, policy))


if __name__ == "__main__":
    unittest.main()