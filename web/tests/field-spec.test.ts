import { describe, expect, it } from "vitest";
import {
  ALL_FIELDS,
  draftToRequest,
  validateDraft,
  validateField,
  type Draft,
  type NumberField,
} from "@/lib/field-spec";
import { PRESETS } from "@/lib/presets";

const field = (name: string) => ALL_FIELDS.find((f) => f.name === name)!;

describe("field spec — constraints mirror the service", () => {
  it("accepts values at the inclusive boundaries", () => {
    expect(validateField(field("age"), "18")).toBeNull();
    expect(validateField(field("age"), "120")).toBeNull();
    expect(validateField(field("debt_to_income"), "0")).toBeNull();
    expect(validateField(field("debt_to_income"), "2")).toBeNull();
  });

  it("rejects values past the boundaries", () => {
    expect(validateField(field("age"), "17")).toMatch(/18/);
    expect(validateField(field("debt_to_income"), "2.5")).toMatch(/2/);
    expect(validateField(field("credit_utilization"), "3.1")).toMatch(/3/);
  });

  it("enforces the exclusive minimum on loan amount", () => {
    expect(validateField(field("loan_amount"), "0")).toMatch(/more than 0/);
    expect(validateField(field("loan_amount"), "1")).toBeNull();
  });

  it("requires a non-empty reference", () => {
    expect(validateField(field("applicant_id"), "  ")).toMatch(/reference/i);
    expect(validateField(field("applicant_id"), "APP-1")).toBeNull();
  });

  it("rejects non-numeric input in number fields", () => {
    expect(validateField(field("annual_income"), "lots")).toMatch(/number/i);
  });

  it("only accepts declared enum values", () => {
    expect(validateField(field("home_ownership"), "CASTLE")).toMatch(/option/i);
    expect(validateField(field("home_ownership"), "OWN")).toBeNull();
  });

  it("mirrors the service's numeric bounds exactly", () => {
    const bounds: Record<string, [number | undefined, number | undefined]> = {
      age: [18, 120],
      employment_length: [0, 60],
      debt_to_income: [0, 2],
      credit_utilization: [0, 3],
      interest_rate: [0, 100],
    };
    for (const [name, [min, max]] of Object.entries(bounds)) {
      const f = field(name) as NumberField;
      expect(f.min).toBe(min);
      expect(f.max).toBe(max);
    }
  });
});

describe("field spec — presets and conversion", () => {
  it("every preset passes validation", () => {
    for (const preset of PRESETS) {
      expect(validateDraft(preset.draft)).toEqual({});
    }
  });

  it("converts a draft into a typed numeric request", () => {
    const request = draftToRequest(PRESETS[0].draft);
    expect(request.age).toBe(48);
    expect(typeof request.annual_income).toBe("number");
    expect(request.home_ownership).toBe("OWN");
  });

  it("flags a blank value in every field", () => {
    const empty = Object.fromEntries(ALL_FIELDS.map((f) => [f.name, ""])) as Draft;
    const errors = validateDraft(empty);
    // A truly-blank draft — enums included — fails on every field.
    expect(Object.keys(errors).length).toBe(ALL_FIELDS.length);
  });
});
