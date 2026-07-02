/**
 * Supabase server-side client (service role).
 *
 * Uses SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY so that writes are never
 * blocked by Row-Level Security.  Never expose this client to the browser.
 */
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.SUPABASE_URL ?? "";
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";

/**
 * Returns null (instead of throwing) when env vars are absent so the API
 * route can gracefully fall back to the local-file strategy.
 */
export function getSupabaseAdmin() {
  if (!supabaseUrl || !supabaseKey) return null;
  return createClient(supabaseUrl, supabaseKey, {
    auth: { persistSession: false },
  });
}
