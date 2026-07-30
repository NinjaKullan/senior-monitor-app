-- 0003 — take EXECUTE on the family-lookup helper away from `anon`.
--
-- Supabase configures default privileges that grant EXECUTE on new public-schema
-- functions to anon, authenticated and service_role at creation time. That is a
-- *direct* grant on the role, so 0002's `revoke all ... from public` does not
-- remove it: revoking from PUBLIC only drops the implicit world grant.
--
-- The result is that `app_current_family_ids()` — a SECURITY DEFINER function
-- that reads `members` with RLS bypassed — was callable by the pre-login anon
-- role. It returns nothing without a JWT (auth.uid() is null, so the lookup
-- matches no rows), but an unauthenticated caller has no business invoking a
-- definer-rights function over the tenancy table at all. Least privilege, and
-- one less thing for a future change to that function to get wrong.
--
-- Already applied to production; this file is the repo catching up.

revoke execute on function public.app_current_family_ids() from anon;
