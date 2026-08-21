// Maps a completed manual assessment into the exact record shape the HMA
// Corrective Exercise Tracker imports (its "Import JSON" / "Paste JSON" box takes
// an array of these). Field names and value shapes mirror the Tracker's own
// getFormData()/record model so an exported record drives its exercise builder
// with no re-entry.

import type { ManualAssessmentDetail } from "./types";

// Manual movement keys -> Tracker movement keys.
const MANUAL_TO_TRACKER_KEY: Record<string, TrackerMovementKey> = {
  forward_lunge: "lunge",
  single_leg_dip: "sld",
  shoulder_reach_behind_back: "shoulder",
  trunk_rotation: "trunk",
  cervical_rotation: "cervical"
};

// Tracker key order (matches the Tracker's MOVEMENTS array).
const TRACKER_KEYS = ["lunge", "sld", "shoulder", "trunk", "cervical"] as const;
type TrackerMovementKey = (typeof TRACKER_KEYS)[number];

type TrackerSideScore = { val: number | null; pain: boolean };

export type TrackerRecord = {
  id: string;
  // Badge #. Named `badge` to match the Tracker's own short field names; it maps
  // to `employee.employee_number` when the Tracker builds a Cadence plan payload.
  // Optional here — anonymous scoring stays valid — but Cadence rejects a plan
  // without one, so the Tracker flags a blank badge on import.
  badge: string;
  fname: string;
  lname: string;
  name: string;
  company: string;
  dept: string;
  shift: string;
  date: string;
  location: string;
  type: string;
  scores: Record<TrackerMovementKey, [TrackerSideScore, TrackerSideScore]>;
  total: number;
  hypermobile: Record<TrackerMovementKey, boolean>;
  hasOA: boolean;
  notes: string;
  followup: string;
  retest: string;
  plan: string;
  pa: string;
  observations: Record<TrackerMovementKey, Record<string, never>>;
  qualityFocus: Record<TrackerMovementKey, never[]>;
};

// Fallback only — used when the provider left First/Last Name blank on the New
// Assessment form. "Last, First" is unambiguous; otherwise the last whitespace-
// separated token is the surname, so "Mary Jo Smith" splits Mary Jo / Smith.
function splitName(fullName: string): { fname: string; lname: string } {
  const trimmed = fullName.trim().replace(/\s+/g, " ");
  if (!trimmed) return { fname: "", lname: "" };

  const comma = trimmed.indexOf(",");
  if (comma !== -1) {
    return {
      fname: trimmed.slice(comma + 1).trim(),
      lname: trimmed.slice(0, comma).trim()
    };
  }

  const lastSpace = trimmed.lastIndexOf(" ");
  if (lastSpace === -1) return { fname: trimmed, lname: "" };
  return { fname: trimmed.slice(0, lastSpace), lname: trimmed.slice(lastSpace + 1) };
}

// The provider's explicit entry wins; fall back to whatever the assessment
// already knows so pre-existing assessments export exactly as they did before.
function firstNonEmpty(...values: Array<string | null | undefined>): string {
  for (const value of values) {
    const trimmed = (value ?? "").trim();
    if (trimmed) return trimmed;
  }
  return "";
}

function toDateOnly(iso: string): string {
  // Tracker stores date as a plain YYYY-MM-DD string.
  return (iso || "").split("T")[0] ?? "";
}

export function buildTrackerRecord(assessment: ManualAssessmentDetail): TrackerRecord {
  const byTrackerKey = new Map<TrackerMovementKey, ManualAssessmentDetail["movement_results"][number]>();
  for (const result of assessment.movement_results) {
    const trackerKey = MANUAL_TO_TRACKER_KEY[result.movement_key];
    if (trackerKey) byTrackerKey.set(trackerKey, result);
  }

  const scores = {} as TrackerRecord["scores"];
  const hypermobile = {} as TrackerRecord["hypermobile"];
  const observations = {} as TrackerRecord["observations"];
  const qualityFocus = {} as TrackerRecord["qualityFocus"];
  const noteLines: string[] = [];

  for (const key of TRACKER_KEYS) {
    const result = byTrackerKey.get(key);
    // Tracker side order is [Right, Left].
    scores[key] = [
      { val: result?.right_score ?? null, pain: result?.right_pain ?? false },
      { val: result?.left_score ?? null, pain: result?.left_pain ?? false }
    ];
    hypermobile[key] = result?.hypermobile ?? false;
    observations[key] = {};
    qualityFocus[key] = [];
    if (result?.provider_note) noteLines.push(`${key}: ${result.provider_note}`);
  }

  const derived = splitName(assessment.participant_name);
  const fname = firstNonEmpty(assessment.first_name, derived.fname);
  const lname = firstNonEmpty(assessment.last_name, derived.lname);

  return {
    id: assessment.id,
    badge: firstNonEmpty(assessment.employee_number),
    fname,
    lname,
    name: firstNonEmpty([fname, lname].join(" "), assessment.participant_name),
    company: firstNonEmpty(assessment.company, assessment.employee_employer),
    dept: firstNonEmpty(assessment.department),
    shift: firstNonEmpty(assessment.shift),
    date: toDateOnly(assessment.created_at),
    location: firstNonEmpty(assessment.work_location),
    type: "",
    scores,
    total: assessment.total_score,
    hypermobile,
    hasOA: assessment.has_oa,
    notes: noteLines.join("\n"),
    followup: "",
    retest: "",
    plan: "",
    pa: "",
    observations,
    qualityFocus
  };
}

// The Tracker import expects an array of records.
export function buildTrackerExport(assessment: ManualAssessmentDetail): TrackerRecord[] {
  return [buildTrackerRecord(assessment)];
}

export function trackerExportJson(assessment: ManualAssessmentDetail): string {
  return JSON.stringify(buildTrackerExport(assessment), null, 2);
}

function safeFileName(name: string): string {
  const base = name.trim().replace(/[^a-z0-9]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase();
  return base || "assessment";
}

export function downloadTrackerExport(assessment: ManualAssessmentDetail): void {
  const blob = new Blob([trackerExportJson(assessment)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `hma-tracker-${safeFileName(assessment.participant_name)}-${toDateOnly(assessment.created_at)}.json`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

export async function copyTrackerExport(assessment: ManualAssessmentDetail): Promise<void> {
  const json = trackerExportJson(assessment);
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(json);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = json;
  textarea.style.cssText = "position:fixed;top:0;left:0;opacity:0;";
  document.body.appendChild(textarea);
  textarea.select();
  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(textarea);
  }
}
