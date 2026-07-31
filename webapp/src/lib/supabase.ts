/**
 * The only Supabase client in this app, and the only credentials it can hold.
 *
 * URL + publishable key, both safe to ship in a static bundle. The service key
 * bypasses RLS and therefore has no business in anything a browser downloads;
 * scripts/check-build-secrets.mjs greps the built output to keep it that way.
 * Every query below runs as `authenticated`, filtered by the policies.
 */

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL ?? "";
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? "";

export const isConfigured = Boolean(url && publishableKey);

export const supabase: SupabaseClient = createClient(
  url || "https://unconfigured.invalid",
  publishableKey || "unconfigured",
  { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } },
);
