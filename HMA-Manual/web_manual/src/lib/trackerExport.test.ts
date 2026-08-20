import { describe, expect, it } from "vitest";

import { buildTrackerExport, buildTrackerRecord } from "./trackerExport";
import type { ManualAssessmentDetail, ManualMovementResult } from "./types";

function movement(partial: Partial<ManualMovementResult> & { movement_key: string }): ManualMovementResult {
  return {
    id: `res-${partial.movement_key}`,
    assessment_id: "a1",
    right_score: null,
    left_score: null,
    final_score: 0,
    hypermobile: false,
    right_pain: false,
    left_pain: false,
    faults: {},
    provider_note: null,
    reviewed_at: "2026-07-23T12:00:00+00:00",
    ...partial
  };
}

function assessment(partial: Partial<ManualAssessmentDetail> = {}): ManualAssessmentDetail {
  return {
    id: "assessment-123",
    participant_name: "Casey Jones",
    employee_id: null,
    employee_employer: "Hendrickson",
    status: "completed",
    total_score: 5,
    score_band: "High opportunity for improvement",
    has_oa: true,
    consent_notice_version: "v1",
    consent_scope: null,
    created_at: "2026-07-23T14:30:00+00:00",
    retention_expires_at: null,
    completed_at: null,
    videos_deleted_at: null,
    remaining_video_count: 0,
    movement_results: [],
    review_videos: [],
    upload_sessions: [],
    ...partial
  };
}

describe("buildTrackerRecord", () => {
  it("remaps movement keys and preserves Right/Left order, pain, and hypermobility", () => {
    const record = buildTrackerRecord(
      assessment({
        movement_results: [
          movement({
            movement_key: "forward_lunge",
            right_score: 2,
            left_score: 3,
            final_score: 2,
            right_pain: true,
            hypermobile: true
          })
        ]
      })
    );

    // key remap forward_lunge -> lunge; side order [Right, Left]
    expect(record.scores.lunge).toEqual([
      { val: 2, pain: true },
      { val: 3, pain: false }
    ]);
    expect(record.hypermobile.lunge).toBe(true);
  });

  it("fills unscored movements with null values and false flags", () => {
    const record = buildTrackerRecord(assessment());
    for (const key of ["lunge", "sld", "shoulder", "trunk", "cervical"] as const) {
      expect(record.scores[key]).toEqual([
        { val: null, pain: false },
        { val: null, pain: false }
      ]);
      expect(record.hypermobile[key]).toBe(false);
    }
  });

  it("carries OA, total, name split, company, and date-only", () => {
    const record = buildTrackerRecord(assessment());
    expect(record.hasOA).toBe(true);
    expect(record.total).toBe(5);
    expect(record.fname).toBe("Casey");
    expect(record.lname).toBe("Jones");
    expect(record.name).toBe("Casey Jones");
    expect(record.company).toBe("Hendrickson");
    expect(record.date).toBe("2026-07-23");
    expect(record.id).toBe("assessment-123");
  });

  it("prefers the provider's explicit employee details over anything derived", () => {
    const record = buildTrackerRecord(
      assessment({
        participant_name: "EMP-4471",
        first_name: "Casey",
        last_name: "Jones",
        company: "Navarre",
        department: "Weld",
        shift: "2nd",
        work_location: "Line 3"
      })
    );
    expect(record.fname).toBe("Casey");
    expect(record.lname).toBe("Jones");
    expect(record.name).toBe("Casey Jones");
    // explicit company wins over the linked employee's employer
    expect(record.company).toBe("Navarre");
    expect(record.dept).toBe("Weld");
    expect(record.shift).toBe("2nd");
    expect(record.location).toBe("Line 3");
  });

  it("splits a fallback name on the LAST space so multi-word first names survive", () => {
    expect(buildTrackerRecord(assessment({ participant_name: "Mary Jo Smith" }))).toMatchObject({
      fname: "Mary Jo",
      lname: "Smith"
    });
  });

  it("reads a fallback name written as 'Last, First'", () => {
    expect(buildTrackerRecord(assessment({ participant_name: "Smith, John" }))).toMatchObject({
      fname: "John",
      lname: "Smith",
      name: "John Smith"
    });
  });

  it("keeps a bare ID as the name when there is nothing to split", () => {
    const record = buildTrackerRecord(assessment({ participant_name: "EMP-4471", employee_employer: null }));
    expect(record.fname).toBe("EMP-4471");
    expect(record.lname).toBe("");
    expect(record.name).toBe("EMP-4471");
    expect(record.company).toBe("");
  });

  it("exports an array (the Tracker import shape) with all five movement keys", () => {
    const out = buildTrackerExport(assessment());
    expect(Array.isArray(out)).toBe(true);
    expect(out).toHaveLength(1);
    expect(Object.keys(out[0].scores).sort()).toEqual(["cervical", "lunge", "shoulder", "sld", "trunk"]);
  });
});
