/**
 * SpaceAI FC — Supabase Client
 * ==============================
 * Auth + CRUD for saved analyses.
 *
 * Required env vars:
 *   VITE_SUPABASE_URL
 *   VITE_SUPABASE_ANON_KEY
 *
 * Table schema (run in Supabase SQL editor):
 * -------------------------------------------
 * create table public.analyses (
 *   id          uuid primary key default gen_random_uuid(),
 *   user_id     uuid references auth.users(id) on delete cascade,
 *   match_name  text not null,
 *   feature     text not null,
 *   input_data  jsonb default '{}',
 *   results     jsonb default '{}',
 *   created_at  timestamptz default now()
 * );
 * alter table public.analyses enable row level security;
 * create policy "Users manage own analyses"
 *   on public.analyses for all
 *   using (auth.uid() = user_id)
 *   with check (auth.uid() = user_id);
 */

import { createClient, type AuthError, type User } from "@supabase/supabase-js";
import type { SavedAnalysis, UserProfile } from "./types";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

// Gracefully handle missing env vars (app still runs, auth is disabled)
export const supabase =
  supabaseUrl && supabaseKey
    ? createClient(supabaseUrl, supabaseKey)
    : null;

const isConfigured = Boolean(supabase);

/** Returns true if Supabase is configured */
export function isSupabaseConfigured(): boolean {
  return isConfigured;
}

// ── Auth helpers ─────────────────────────────────────────────────

export interface AuthResult {
  user: UserProfile | null;
  error: string | null;
}

export async function signUp(
  email: string,
  password: string,
  fullName: string
): Promise<AuthResult> {
  if (!supabase) return { user: null, error: "Supabase is not configured." };

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: { data: { full_name: fullName } },
  });

  if (error) return { user: null, error: formatAuthError(error) };
  if (!data.user) return { user: null, error: "Sign-up failed — no user returned." };

  return {
    user: {
      id: data.user.id,
      email: data.user.email ?? email,
      full_name: fullName,
    },
    error: null,
  };
}

export async function signIn(
  email: string,
  password: string
): Promise<AuthResult> {
  if (!supabase) return { user: null, error: "Supabase is not configured." };

  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) return { user: null, error: formatAuthError(error) };
  if (!data.user) return { user: null, error: "Sign-in failed." };

  return { user: userFromSupabase(data.user), error: null };
}

export async function signOut(): Promise<void> {
  if (!supabase) return;
  await supabase.auth.signOut();
}

export async function getCurrentUser(): Promise<UserProfile | null> {
  if (!supabase) return null;
  const { data } = await supabase.auth.getUser();
  if (!data.user) return null;
  return userFromSupabase(data.user);
}

/** Subscribe to auth state changes. Returns unsubscribe function. */
export function onAuthStateChange(
  callback: (user: UserProfile | null) => void
): () => void {
  if (!supabase) return () => {};

  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange((_event, session) => {
    callback(session?.user ? userFromSupabase(session.user) : null);
  });

  return () => subscription.unsubscribe();
}

// ── Analyses CRUD ────────────────────────────────────────────────

export async function saveAnalysis(
  userId: string,
  matchName: string,
  feature: string,
  inputData: Record<string, unknown>,
  results: Record<string, unknown>
): Promise<{ id: string | null; error: string | null }> {
  if (!supabase) return { id: null, error: "Supabase is not configured." };

  const { data, error } = await supabase
    .from("analyses")
    .insert({
      user_id: userId,
      match_name: matchName,
      feature,
      input_data: inputData,
      results,
    })
    .select("id")
    .single();

  if (error) return { id: null, error: error.message };
  return { id: data?.id ?? null, error: null };
}

export async function getAnalyses(
  userId: string
): Promise<{ data: SavedAnalysis[]; error: string | null }> {
  if (!supabase) return { data: [], error: "Supabase is not configured." };

  const { data, error } = await supabase
    .from("analyses")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false });

  if (error) return { data: [], error: error.message };
  return { data: (data as SavedAnalysis[]) ?? [], error: null };
}

export async function getAnalysisById(
  id: string
): Promise<{ data: SavedAnalysis | null; error: string | null }> {
  if (!supabase) return { data: null, error: "Supabase is not configured." };

  const { data, error } = await supabase
    .from("analyses")
    .select("*")
    .eq("id", id)
    .single();

  if (error) return { data: null, error: error.message };
  return { data: data as SavedAnalysis, error: null };
}

export async function deleteAnalysis(
  id: string
): Promise<{ error: string | null }> {
  if (!supabase) return { error: "Supabase is not configured." };

  const { error } = await supabase.from("analyses").delete().eq("id", id);
  return { error: error?.message ?? null };
}

// ── Internal helpers ─────────────────────────────────────────────

function userFromSupabase(user: User): UserProfile {
  return {
    id: user.id,
    email: user.email ?? "",
    full_name:
      (user.user_metadata?.full_name as string | undefined) ??
      user.email?.split("@")[0] ??
      "Manager",
  };
}

function formatAuthError(error: AuthError): string {
  // Map common Supabase error codes to user-friendly messages
  switch (error.message) {
    case "Invalid login credentials":
      return "Wrong email or password.";
    case "User already registered":
      return "An account with this email already exists.";
    case "Email not confirmed":
      return "Please check your email and confirm your account first.";
    default:
      return error.message;
  }
}
