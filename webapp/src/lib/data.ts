/**
 * Every read the app performs, in one file.
 *
 * No query names a family: RLS decides what comes back. The client asking
 * politely for its own rows would only mask a policy bug, and this is the layer
 * a future spec is most likely to extend carelessly.
 */

import { supabase } from "./supabase";
import { READ_SURFACE } from "./queries";
import type { DigestSend, Family, Member, Parent, ParentSignal, Ping } from "./types";

async function readAll<T>(table: keyof typeof READ_SURFACE): Promise<T[]> {
  const { data, error } = await supabase.from(table).select(READ_SURFACE[table]);
  if (error) throw error;
  return (data ?? []) as T[];
}

export interface FamilySnapshot {
  family: Family | null;
  parents: Parent[];
  members: Member[];
  signals: ParentSignal[];
  pings: Ping[];
  digests: DigestSend[];
}

export async function claimMembership(): Promise<void> {
  const { error } = await supabase.rpc("app_claim_membership");
  if (error) throw error;
}

export async function loadSnapshot(): Promise<FamilySnapshot> {
  const [families, parents, members, signals, pings, digests] = await Promise.all([
    readAll<Family>("families"),
    readAll<Parent>("parents"),
    readAll<Member>("members"),
    readAll<ParentSignal>("parent_signals"),
    readAll<Ping>("pings"),
    readAll<DigestSend>("digest_sends"),
  ]);
  return {
    family: families[0] ?? null,
    parents,
    members,
    signals,
    pings,
    digests,
  };
}
