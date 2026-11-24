import unittest
from types import SimpleNamespace
from unittest.mock import patch

import database as db


class FakeRpcClient:
    def __init__(self, response_data):
        self.response_data = response_data
        self.calls = []

    def rpc(self, function_name, params):
        self.calls.append((function_name, params))
        return self

    def execute(self):
        return SimpleNamespace(data=self.response_data)


class AiCreditApiTest(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            "free_credits_remaining": 3,
            "purchased_credits_remaining": 20,
            "credits_balance": 23,
            "free_credits_reset_at": "2026-12-01T00:00:00+00:00",
        }

    def test_refresh_uses_database_snapshot(self):
        client = FakeRpcClient(self.snapshot)
        with patch.object(db, "get_admin_supabase", return_value=client):
            success, result = db.refresh_ai_credit_balance("org-1")

        self.assertTrue(success)
        self.assertEqual(result, self.snapshot)
        self.assertEqual(
            client.calls,
            [("refresh_ai_credit_balance", {"p_org_id": "org-1"})],
        )

    def test_free_consumption_syncs_authoritative_balances(self):
        response = dict(self.snapshot, allowed=True, reason="free_credit")
        client = FakeRpcClient(response)
        with (
            patch.object(db, "get_admin_supabase", return_value=client),
            patch.object(db, "_sync_credit_session") as sync_session,
        ):
            allowed, reason = db.consume_ai_credit("org-1", "free", False)

        self.assertTrue(allowed)
        self.assertEqual(reason, "free_credit")
        sync_session.assert_called_once_with(self.snapshot)
        self.assertEqual(
            client.calls,
            [("consume_ai_credit", {"p_org_id": "org-1"})],
        )

    def test_purchased_consumption_is_reported_separately(self):
        response = dict(self.snapshot, allowed=True, reason="purchased_credit")
        client = FakeRpcClient(response)
        with (
            patch.object(db, "get_admin_supabase", return_value=client),
            patch.object(db, "_sync_credit_session") as sync_session,
        ):
            allowed, reason = db.consume_ai_credit("org-1", "free", False)

        self.assertTrue(allowed)
        self.assertEqual(reason, "purchased_credit")
        sync_session.assert_called_once_with(self.snapshot)

    def test_empty_balance_blocks_generation(self):
        empty_snapshot = {
            "free_credits_remaining": 0,
            "purchased_credits_remaining": 0,
            "credits_balance": 0,
            "free_credits_reset_at": "2026-12-01T00:00:00+00:00",
        }
        client = FakeRpcClient(dict(empty_snapshot, allowed=False, reason="no_free_credits"))
        with (
            patch.object(db, "get_admin_supabase", return_value=client),
            patch.object(db, "_sync_credit_session") as sync_session,
        ):
            allowed, reason = db.consume_ai_credit("org-1", "free", False)

        self.assertFalse(allowed)
        self.assertEqual(reason, "no_free_credits")
        sync_session.assert_called_once_with(empty_snapshot)

    def test_admin_top_up_grants_a_purchased_pack(self):
        client = FakeRpcClient({"status": "applied"})
        with patch.object(db, "get_admin_supabase", return_value=client):
            success, error = db.top_up_org_credits("org-1", 20)

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(
            client.calls,
            [
                (
                    "grant_purchased_ai_credits",
                    {
                        "p_org_id": "org-1",
                        "p_amount": 20,
                        "p_provider": "admin",
                        "p_product_name": "Admin credit top-up",
                    },
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
