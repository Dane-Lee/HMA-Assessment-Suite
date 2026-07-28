import { type ChangeEvent, type FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { InfoIcon } from "../components/InfoIcon";
import { Modal } from "../components/Modal";
import { ProgressChecklist } from "../components/ProgressChecklist";
import {
  completeAssessment,
  deleteReviewVideo,
  getAssessment,
  issueUploadSession,
  listMovements,
  saveManualScore,
  updateAssessmentOA,
  uploadReviewVideo
} from "../lib/api";
import { prettyFault } from "../lib/formatters";
import { MANUAL_FAULT_PROMPTS } from "../lib/manualScoring";
import type {
  ManualAssessmentDetail,
  ManualReviewVideo,
  ManualScorePayload,
  MovementDefinition,
  Side
} from "../lib/types";

type SideDraft = {
  score: number | null;
  faults: string[];
  pain: boolean;
};

type MovementDraft = Partial<Record<Side, SideDraft>> & {
  providerNote?: string;
  hypermobile?: boolean;
};

type PendingVideo = {
  file: File;
  previewUrl: string;
};

function sideLabel(side: Side) {
  return side === "left" ? "Left Side" : "Right Side";
}

function makeClientVideoId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function slotKey(movementKey: string, side: Side) {
  return `${movementKey}:${side}`;
}

export function AssessmentSessionPage() {
  const { assessmentId = "" } = useParams();
  const navigate = useNavigate();
  const [assessment, setAssessment] = useState<ManualAssessmentDetail | null>(null);
  const [movements, setMovements] = useState<MovementDefinition[]>([]);
  const [selectedMovementKey, setSelectedMovementKey] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, MovementDraft>>({});
  const [pendingVideos, setPendingVideos] = useState<Record<string, PendingVideo>>({});
  const [busySlot, setBusySlot] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [linkForm, setLinkForm] = useState({ name: "", employer: "", email: "" });
  const [issuedLink, setIssuedLink] = useState<string | null>(null);
  const [linkModalOpen, setLinkModalOpen] = useState(false);
  const [expandedFaults, setExpandedFaults] = useState<Record<string, boolean>>({});

  async function refresh() {
    const [nextAssessment, nextMovements] = await Promise.all([getAssessment(assessmentId), listMovements()]);
    setAssessment(nextAssessment);
    setMovements(nextMovements);
    setDrafts((current) => seedDrafts(current, nextAssessment));
  }

  useEffect(() => {
    refresh().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Unable to load assessment.");
    });
  }, [assessmentId]);

  const completedKeys = useMemo(
    () => new Set(assessment?.movement_results.map((result) => result.movement_key) ?? []),
    [assessment]
  );
  const firstIncomplete = movements.find((movement) => !completedKeys.has(movement.key));
  const selectedMovement =
    movements.find((movement) => movement.key === selectedMovementKey) ?? firstIncomplete ?? movements[0];

  useEffect(() => {
    if (!selectedMovementKey && selectedMovement) {
      setSelectedMovementKey(selectedMovement.key);
    }
  }, [selectedMovement, selectedMovementKey]);

  const videosBySlot = useMemo(() => {
    const next: Record<string, ManualReviewVideo> = {};
    assessment?.review_videos.forEach((video) => {
      next[slotKey(video.movement_key, video.side)] = video;
    });
    return next;
  }, [assessment]);

  function setSideDraft(movementKey: string, side: Side, patch: Partial<SideDraft>) {
    setDrafts((current) => {
      const movementDraft = current[movementKey] ?? {};
      const sideDraft = movementDraft[side] ?? { score: null, faults: [], pain: false };
      return {
        ...current,
        [movementKey]: {
          ...movementDraft,
          [side]: {
            ...sideDraft,
            ...patch
          }
        }
      };
    });
  }

  function toggleFault(movementKey: string, side: Side, fault: string) {
    const currentFaults = drafts[movementKey]?.[side]?.faults ?? [];
    setSideDraft(movementKey, side, {
      faults: currentFaults.includes(fault)
        ? currentFaults.filter((item) => item !== fault)
        : [...currentFaults, fault]
    });
  }

  function setProviderNote(movementKey: string, providerNote: string) {
    setDrafts((current) => ({
      ...current,
      [movementKey]: {
        ...(current[movementKey] ?? {}),
        providerNote
      }
    }));
  }

  function setHypermobile(movementKey: string, hypermobile: boolean) {
    setDrafts((current) => ({
      ...current,
      [movementKey]: {
        ...(current[movementKey] ?? {}),
        hypermobile
      }
    }));
  }

  async function handleToggleOA(hasOA: boolean) {
    if (!assessment) return;
    setError(null);
    try {
      setAssessment(await updateAssessmentOA(assessment.id, hasOA));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to update OA flag.");
    }
  }

  async function handleVideoFile(movementKey: string, side: Side, event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const key = slotKey(movementKey, side);
    const previous = pendingVideos[key];
    if (previous) URL.revokeObjectURL(previous.previewUrl);
    setPendingVideos((current) => ({
      ...current,
      [key]: {
        file,
        previewUrl: URL.createObjectURL(file)
      }
    }));
  }

  async function uploadPendingVideo(movementKey: string, side: Side) {
    if (!assessment) return;
    const key = slotKey(movementKey, side);
    const pending = pendingVideos[key];
    if (!pending) return;
    setBusySlot(key);
    setError(null);
    try {
      await uploadReviewVideo(assessment.id, movementKey, side, pending.file, makeClientVideoId());
      URL.revokeObjectURL(pending.previewUrl);
      setPendingVideos((current) => {
        const next = { ...current };
        delete next[key];
        return next;
      });
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to upload review video.");
    } finally {
      setBusySlot(null);
    }
  }

  async function handleDeleteVideo(video: ManualReviewVideo) {
    await deleteReviewVideo(video.assessment_id, video.id);
    await refresh();
  }

  async function handleSaveMovement() {
    if (!assessment || !selectedMovement) return;
    const draft = drafts[selectedMovement.key] ?? {};
    const payload: ManualScorePayload = {
      provider_note: draft.providerNote?.trim() || undefined,
      hypermobile: draft.hypermobile ?? false
    };
    for (const side of selectedMovement.sides) {
      const sideDraft = draft[side];
      if (sideDraft?.score === null || sideDraft?.score === undefined) {
        setError(`Enter a score for ${sideLabel(side)} before saving.`);
        return;
      }
      payload[side] = {
        score: sideDraft.score,
        faults: sideDraft.faults,
        pain: sideDraft.pain ?? false
      };
    }
    setSaving(true);
    setError(null);
    try {
      const updated = await saveManualScore(assessment.id, selectedMovement.key, payload);
      setAssessment(updated);
      const nextIncomplete = movements.find(
        (movement) =>
          movement.key !== selectedMovement.key &&
          !updated.movement_results.some((result) => result.movement_key === movement.key)
      );
      if (nextIncomplete) {
        setSelectedMovementKey(nextIncomplete.key);
      } else {
        navigate(`/assessments/${assessment.id}/results`);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save score.");
    } finally {
      setSaving(false);
    }
  }

  async function handleIssueLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!assessment) return;
    setError(null);
    setIssuedLink(null);
    try {
      const issued = await issueUploadSession(assessment.id, {
        name: linkForm.name.trim(),
        employer: linkForm.employer.trim(),
        email: linkForm.email.trim() || undefined
      });
      setIssuedLink(issued.url);
      setLinkForm({ name: "", employer: "", email: "" });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to issue upload link.");
    }
  }

  async function handleComplete() {
    if (!assessment) return;
    const confirmDeleteVideos = assessment.remaining_video_count > 0;
    if (confirmDeleteVideos) {
      const confirmed = window.confirm(
        `This assessment has ${assessment.remaining_video_count} temporary review video${assessment.remaining_video_count === 1 ? "" : "s"}. Delete them and mark scoring complete?`
      );
      if (!confirmed) return;
    }
    const updated = await completeAssessment(assessment.id, confirmDeleteVideos);
    setAssessment(updated);
    navigate(`/assessments/${assessment.id}/results`);
  }

  function toggleFaultsExpanded(key: string) {
    setExpandedFaults((current) => ({ ...current, [key]: !current[key] }));
  }

  if (!assessment || !selectedMovement) {
    return (
      <section className="card">
        <p className="text-sm text-ink/60">Loading manual session...</p>
        {error ? <p className="mt-3 text-sm text-rose-600">{error}</p> : null}
      </section>
    );
  }

  const movementDraft = drafts[selectedMovement.key] ?? {};
  const faultPrompts = MANUAL_FAULT_PROMPTS[selectedMovement.key] ?? [];

  return (
    <div className="grid gap-4">
      <section className="card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-ink/45">Manual session</p>
            <h2 className="mt-1 text-2xl font-semibold">{assessment.participant_name}</h2>
            <label className="mt-3 inline-flex items-center gap-2 rounded-xl bg-panel px-3 py-2 text-sm">
              <input
                checked={assessment.has_oa}
                className="h-4 w-4 rounded border-slate-300 text-accent"
                onChange={(event) => void handleToggleOA(event.target.checked)}
                type="checkbox"
              />
              <span>Known Osteoarthritis (OA)</span>
            </label>
          </div>
          <div className="text-right">
            <div className="text-2xl font-semibold">{assessment.total_score}/15</div>
            <p className="text-xs text-ink/50">Review videos remaining: {assessment.remaining_video_count}</p>
          </div>
        </div>
      </section>

      <ProgressChecklist
        completedKeys={completedKeys}
        movements={movements}
        onSelect={setSelectedMovementKey}
        selectedKey={selectedMovement.key}
      />

      <section className="card grid gap-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-ink/45">Current movement</p>
            <h2 className="mt-1 inline-flex items-center gap-2 text-2xl font-semibold">
              {selectedMovement.label}
              <InfoIcon label="Movement instructions">{selectedMovement.instructions}</InfoIcon>
            </h2>
          </div>
          <button className="button-secondary" onClick={() => void refresh()} type="button">
            Refresh Videos
          </button>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {selectedMovement.sides.map((side) => {
            const sideDraft = movementDraft[side] ?? { score: null, faults: [], pain: false };
            const video = videosBySlot[slotKey(selectedMovement.key, side)];
            const pending = pendingVideos[slotKey(selectedMovement.key, side)];
            const isBusy = busySlot === slotKey(selectedMovement.key, side);
            const faultSlotKey = slotKey(selectedMovement.key, side);
            const faultsOpen = expandedFaults[faultSlotKey] ?? false;
            return (
              <section className="rounded-2xl border border-rim bg-panel p-4" key={side}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-ink/40">{side}</p>
                    <h3 className="font-semibold">{sideLabel(side)} Score</h3>
                  </div>
                  <span className="rounded-full bg-panel-mid px-3 py-1 text-xs font-semibold text-ink/70">
                    {sideDraft.score === null ? "Not Set" : `${sideDraft.score}/3`}
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-4 gap-2">
                  {[0, 1, 2, 3].map((score) => (
                    <button
                      className={`rounded-full border py-2 text-sm font-semibold transition ${
                        sideDraft.score === score
                          ? "border-ink bg-ink text-white"
                          : "border-rim bg-panel text-ink hover:border-accent hover:text-accent"
                      }`}
                      key={score}
                      onClick={() => setSideDraft(selectedMovement.key, side, { score })}
                      type="button"
                    >
                      {score}
                    </button>
                  ))}
                </div>

                <label className="mt-3 flex items-center gap-2 rounded-xl border border-rose-300/60 bg-rose-500/10 px-3 py-2 text-sm font-medium text-rose-700">
                  <input
                    checked={sideDraft.pain}
                    className="h-4 w-4 rounded border-rose-300 text-rose-600"
                    onChange={(event) => setSideDraft(selectedMovement.key, side, { pain: event.target.checked })}
                    type="checkbox"
                  />
                  <span>Pain or Discomfort on This Side</span>
                </label>

                <div className="mt-4">
                  <button
                    aria-expanded={faultsOpen}
                    className="flex w-full items-center justify-between rounded-xl bg-panel-mid px-3 py-2 text-sm font-semibold text-ink/80 transition hover:text-ink"
                    onClick={() => toggleFaultsExpanded(faultSlotKey)}
                    type="button"
                  >
                    <span>Fault Qualifiers{sideDraft.faults.length > 0 ? ` (${sideDraft.faults.length})` : ""}</span>
                    <span aria-hidden className="text-xs text-ink/50">{faultsOpen ? "▲" : "▼"}</span>
                  </button>
                  {faultsOpen ? (
                    <div className="mt-2 grid gap-2">
                      {faultPrompts.map((fault) => (
                        <label className="flex items-center gap-2 rounded-xl bg-panel-mid px-3 py-2 text-sm" key={fault.key}>
                          <input
                            checked={sideDraft.faults.includes(fault.key)}
                            className="h-4 w-4 rounded border-slate-300 text-accent"
                            onChange={() => toggleFault(selectedMovement.key, side, fault.key)}
                            type="checkbox"
                          />
                          <span>{fault.label}</span>
                        </label>
                      ))}
                    </div>
                  ) : null}
                </div>

                <div className="mt-4 rounded-2xl border border-rim bg-panel p-3">
                  <p className="text-sm font-semibold">Optional Review Video</p>
                  {pending ? (
                    <video className="mt-3 aspect-video w-full rounded-2xl bg-slate-900 object-cover" controls playsInline src={pending.previewUrl} />
                  ) : video?.video_url ? (
                    <video className="mt-3 aspect-video w-full rounded-2xl bg-slate-900 object-cover" controls playsInline src={video.video_url} />
                  ) : video?.deleted_at ? (
                    <p className="mt-3 rounded-2xl bg-panel-mid px-3 py-3 text-sm text-ink/60">Video deleted or expired.</p>
                  ) : (
                    <div className="mt-3 flex aspect-video items-center justify-center rounded-2xl border border-dashed border-rim bg-panel-mid px-4 text-center text-sm text-ink/60">
                      No review video saved for this side.
                    </div>
                  )}
                  <div className="mt-3 flex flex-wrap gap-2">
                    <label className="button-secondary py-2">
                      {video?.video_url || pending ? "Replace Video" : "Add Video"}
                      <input
                        accept="video/*"
                        className="sr-only"
                        onChange={(event) => void handleVideoFile(selectedMovement.key, side, event)}
                        type="file"
                      />
                    </label>
                    {pending ? (
                      <button className="button-primary py-2" disabled={isBusy} onClick={() => void uploadPendingVideo(selectedMovement.key, side)} type="button">
                        {isBusy ? "Uploading..." : "Save Video"}
                      </button>
                    ) : null}
                    {video?.video_url ? (
                      <button className="button-secondary py-2" onClick={() => void handleDeleteVideo(video)} type="button">
                        Delete Video
                      </button>
                    ) : null}
                  </div>
                </div>
              </section>
            );
          })}
        </div>

        <label className="flex items-center gap-2 rounded-xl border border-rim bg-panel-mid px-3 py-2 text-sm">
          <input
            checked={movementDraft.hypermobile ?? false}
            className="h-4 w-4 rounded border-slate-300 text-accent"
            onChange={(event) => setHypermobile(selectedMovement.key, event.target.checked)}
            type="checkbox"
          />
          <span className="inline-flex items-center gap-1">
            Hypermobility in This Movement
            <InfoIcon label="Hypermobility">Steers the corrective plan toward stability work instead of mobility work.</InfoIcon>
          </span>
        </label>

        <textarea
          className="w-full resize-none rounded-2xl border border-rim bg-panel px-3 py-2 text-sm text-ink placeholder:text-ink/40 focus:border-accent focus:outline-none"
          maxLength={2000}
          onChange={(event) => setProviderNote(selectedMovement.key, event.target.value)}
          placeholder="Optional provider note"
          rows={2}
          value={movementDraft.providerNote ?? ""}
        />

        {error ? <p className="text-sm text-rose-600">{error}</p> : null}

        <div className="flex flex-wrap items-center gap-3">
          <button className="button-primary" disabled={saving} onClick={() => void handleSaveMovement()} type="button">
            {saving ? "Saving..." : "Save Movement Score"}
          </button>
          <Link className="button-secondary" to={`/assessments/${assessment.id}/results`}>
            Review Results
          </Link>
          <button className="button-secondary ml-auto" onClick={() => setLinkModalOpen(true)} type="button">
            Issue Mobile Video Request
          </button>
        </div>
      </section>

      <section className="card">
        <button
          className="button-primary w-full py-3 text-base font-semibold"
          onClick={() => void handleComplete()}
          type="button"
        >
          Complete Assessment
        </button>
      </section>

      <Modal onClose={() => setLinkModalOpen(false)} open={linkModalOpen} title="Issue Mobile Video Request">
        <p className="text-sm text-ink/70">
          Generate a secure link the employee opens on their phone to record and upload the movement videos.
        </p>
        <form className="mt-4 grid gap-3" onSubmit={handleIssueLink}>
          <input
            className="rounded-2xl border border-rim bg-panel px-4 py-3 text-ink outline-none focus:border-accent"
            onChange={(event) => setLinkForm((current) => ({ ...current, name: event.target.value }))}
            placeholder="Employee Name"
            required
            value={linkForm.name}
          />
          <input
            className="rounded-2xl border border-rim bg-panel px-4 py-3 text-ink outline-none focus:border-accent"
            onChange={(event) => setLinkForm((current) => ({ ...current, employer: event.target.value }))}
            placeholder="Employer"
            required
            value={linkForm.employer}
          />
          <input
            className="rounded-2xl border border-rim bg-panel px-4 py-3 text-ink outline-none focus:border-accent"
            onChange={(event) => setLinkForm((current) => ({ ...current, email: event.target.value }))}
            placeholder="Email (Optional)"
            type="email"
            value={linkForm.email}
          />
          <button className="button-primary" type="submit">
            Issue Upload Link
          </button>
        </form>
        {issuedLink ? (
          <div className="mt-4 rounded-2xl border border-accent/30 bg-accent/10 px-4 py-4">
            <p className="text-xs uppercase tracking-[0.25em] text-ink/45">Secure Link</p>
            <code className="mt-2 block break-all rounded-xl bg-panel px-3 py-2 text-xs">{issuedLink}</code>
            <button
              className="button-secondary mt-3 py-2"
              onClick={() => navigator.clipboard.writeText(issuedLink)}
              type="button"
            >
              Copy Link
            </button>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}

function seedDrafts(current: Record<string, MovementDraft>, assessment: ManualAssessmentDetail) {
  const next = { ...current };
  for (const result of assessment.movement_results) {
    next[result.movement_key] = {
      ...(next[result.movement_key] ?? {}),
      right: {
        score: result.right_score,
        faults: result.faults.right ?? [],
        pain: result.right_pain
      },
      left: {
        score: result.left_score,
        faults: result.faults.left ?? [],
        pain: result.left_pain
      },
      providerNote: result.provider_note ?? "",
      hypermobile: result.hypermobile
    };
  }
  return next;
}
