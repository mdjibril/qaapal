WITH sample(tier, balance, purchased, depleted_at) AS (
    VALUES
        ('enterprise'::public.subscription_tier, 999999, 0, NULL::timestamptz),
        ('free'::public.subscription_tier, 0, 0, now() - interval '10 days'),
        ('free'::public.subscription_tier, 20, 20, NULL::timestamptz)
)
SELECT
    tier,
    CASE
        WHEN tier = 'enterprise' AND balance = 999999 AND purchased = 0 THEN 5
        ELSE LEAST(GREATEST(balance, 0), 5)
    END AS free_credits,
    CASE
        WHEN tier = 'enterprise' AND balance = 999999 AND purchased = 0 THEN 0
        ELSE GREATEST(balance - 5, 0)
    END AS purchased_credits,
    CASE
        WHEN tier = 'enterprise' AND balance = 999999 AND purchased = 0 THEN 5
        WHEN balance <= 0 AND depleted_at IS NOT NULL THEN 0
        ELSE NULL
    END AS expected_total_or_due_reset
FROM sample;