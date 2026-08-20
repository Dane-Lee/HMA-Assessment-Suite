import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { InfoIcon } from "../components/InfoIcon";
import { createAssessment } from "../lib/api";
import { buildConsentPayload, PRIVACY_POSTURE_STATEMENT } from "../lib/privacy";
import type { AssessmentDetails } from "../lib/types";

const DETAIL_FIELDS: Array<{ key: keyof AssessmentDetails; label: string }> = [
  { key: "first_name", label: "First Name" },
  { key: "last_name", label: "Last Name" },
  { key: "company", label: "Company" },
  { key: "department", label: "Department" },
  { key: "shift", label: "Shift" },
  { key: "work_location", label: "Location" }
];

const EMPTY_DETAILS: AssessmentDetails = {
  first_name: "",
  last_name: "",
  company: "",
  department: "",
  shift: "",
  work_location: ""
};

export function NewAssessmentPage() {
  const navigate = useNavigate();
  const [participantName, setParticipantName] = useState("");
  const [details, setDetails] = useState<AssessmentDetails>(EMPTY_DETAILS);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const filledDetailCount = DETAIL_FIELDS.filter(({ key }) => (details[key] ?? "").trim()).length;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const assessment = await createAssessment(participantName.trim(), buildConsentPayload(), false, details);
      navigate(`/assessments/${assessment.id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create assessment.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-4">
      <section className="card">
        <p className="text-xs uppercase tracking-[0.3em] text-ink/45">Assessment setup</p>
        <h2 className="mt-2 inline-flex items-center gap-2 text-2xl font-semibold">
          Start a New Manual Assessment
          <InfoIcon label="About this assessment">
            <p>Structured manual scores are retained under policy. Review videos are optional and temporary.</p>
            <p className="mt-2">{PRIVACY_POSTURE_STATEMENT}</p>
          </InfoIcon>
        </h2>
      </section>
      <form className="card grid gap-4" onSubmit={handleSubmit}>
        <label className="grid gap-2">
          <span className="text-sm font-semibold">Participant name or ID</span>
          <input
            className="rounded-2xl border border-rim bg-panel px-4 py-3 text-ink outline-none transition focus:border-accent"
            maxLength={120}
            onChange={(event) => setParticipantName(event.target.value)}
            required
            value={participantName}
          />
        </label>

        <div>
          <div className="flex items-center gap-2 rounded-xl bg-panel-mid px-3 py-2">
            <button
              aria-expanded={detailsOpen}
              className="flex flex-1 items-center justify-between text-left text-sm font-semibold text-ink/80 transition hover:text-ink"
              onClick={() => setDetailsOpen((current) => !current)}
              type="button"
            >
              <span>Employee Details (Optional){filledDetailCount > 0 ? ` (${filledDetailCount})` : ""}</span>
              <span aria-hidden className="text-xs text-ink/50">{detailsOpen ? "▲" : "▼"}</span>
            </button>
            <InfoIcon label="About employee details">
              <p>
                Leave these blank to score anonymously. Anything you fill in is carried into the Corrective Exercise
                Tracker export, so you do not have to re-type it there.
              </p>
            </InfoIcon>
          </div>
          {detailsOpen ? (
            <div className="mt-2 grid gap-3 sm:grid-cols-2">
              {DETAIL_FIELDS.map(({ key, label }) => (
                <label className="grid gap-2" key={key}>
                  <span className="text-sm font-semibold">{label}</span>
                  <input
                    className="rounded-2xl border border-rim bg-panel px-4 py-3 text-ink outline-none transition focus:border-accent"
                    maxLength={120}
                    onChange={(event) => setDetails((current) => ({ ...current, [key]: event.target.value }))}
                    value={details[key] ?? ""}
                  />
                </label>
              ))}
            </div>
          ) : null}
        </div>

        <label className="flex items-start gap-3 rounded-2xl bg-panel px-4 py-4 text-sm text-ink/75">
          <input
            checked={accepted}
            className="mt-1 h-4 w-4 rounded border-slate-300 text-accent"
            onChange={(event) => setAccepted(event.target.checked)}
            type="checkbox"
          />
          <span>
            I confirm participation is voluntary, temporary review-video retention has been explained, and results are
            not used as a stand-alone basis for employment decisions.
          </span>
        </label>
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <button className="button-primary" disabled={!accepted || !participantName.trim() || saving} type="submit">
          {saving ? "Creating..." : "Create manual assessment"}
        </button>
      </form>
    </div>
  );
}
