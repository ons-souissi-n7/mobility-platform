import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AgreementForm } from "@/components/mobility/agreement-form";
import type { Agreement, Department, Level, MobilityCategory, PartnerUniversity } from "@/lib/api/types";

function makeUniversity(overrides: Partial<PartnerUniversity> = {}): PartnerUniversity {
  return {
    id: 1,
    moveon_id: null,
    name: "TU Berlin",
    short_name: "TUB",
    translated_name: "",
    erasmus_code: "",
    city: "Berlin",
    url: "",
    email: "",
    country_id: 1,
    country_iso2: "DE",
    country_name_fr: "Allemagne",
    last_sync_moveon: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeAgreement(overrides: Partial<Agreement> = {}): Agreement {
  return {
    id: 1,
    moveon_id: null,
    reference: "",
    name: "Erasmus TU Berlin",
    partner_university_id: 1,
    category_id: null,
    direction: "outgoing",
    valid_from: null,
    valid_until: null,
    inp_total_places: 5,
    inp_institutions: "N7",
    duration_weeks: 24,
    remarks: "",
    department_ids: [],
    level_ids: [],
    last_sync_moveon: null,
    deleted_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

const defaultProps = {
  departments: [] as Department[],
  frameworks: [] as MobilityCategory[],
  mobilityLevels: [] as Level[],
  onCancel: vi.fn(),
  universities: [makeUniversity()],
};

describe("AgreementForm — Durée du séjour", () => {
  it("submits duration_weeks as a number when filled in", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(<AgreementForm {...defaultProps} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Nom de l'accord"), "Erasmus TU Berlin");
    await user.selectOptions(screen.getByLabelText("Université partenaire"), "1");
    await user.type(screen.getByLabelText(/durée du séjour/i), "24");
    await user.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toMatchObject({ duration_weeks: 24 });
  });

  it("submits null when the duration field is left empty", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(<AgreementForm {...defaultProps} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Nom de l'accord"), "Erasmus TU Berlin");
    await user.selectOptions(screen.getByLabelText("Université partenaire"), "1");
    await user.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toMatchObject({ duration_weeks: null });
  });

  it("pre-fills the duration field from an existing agreement when editing", () => {
    render(
      <AgreementForm {...defaultProps} item={makeAgreement({ duration_weeks: 12 })} onSubmit={vi.fn()} />,
    );

    expect(screen.getByLabelText(/durée du séjour/i)).toHaveValue(12);
  });

  it("leaves the duration field blank when editing an agreement with no duration set", () => {
    render(
      <AgreementForm {...defaultProps} item={makeAgreement({ duration_weeks: null })} onSubmit={vi.fn()} />,
    );

    expect(screen.getByLabelText(/durée du séjour/i)).toHaveValue(null);
  });
});
