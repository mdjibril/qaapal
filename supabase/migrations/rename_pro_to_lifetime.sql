-- ============================================================
-- Migration: Rename 'pro' subscription tier to 'lifetime'
-- Run this in the Supabase SQL Editor (Dashboard > SQL Editor)
-- ============================================================

-- Step 1: Update any existing organizations that are on the 'pro' tier
UPDATE public.organizations
SET subscription_tier = 'lifetime'
WHERE subscription_tier = 'pro';

-- Step 2: (Optional) If you added a CHECK constraint on subscription_tier, update it.
-- NOTE: The default setup_full_db.sql does NOT have a CHECK constraint on
-- organizations.subscription_tier, so this step may be a no-op.
-- Only run the lines below if you manually added such a constraint.

-- ALTER TABLE public.organizations
--   DROP CONSTRAINT IF EXISTS organizations_subscription_tier_check;

-- ALTER TABLE public.organizations
--   ADD CONSTRAINT organizations_subscription_tier_check
--   CHECK (subscription_tier IN ('free', 'platform_pass', 'lifetime', 'enterprise'));

-- Step 3: Verify the change
SELECT id, name, subscription_tier FROM public.organizations ORDER BY subscription_tier;
