import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProfileSelectorUI } from "./ProfileSelectorUI";
import type { ProfileDTO } from "../types/dto";

function profile(profileId: string, profileName: string): ProfileDTO {
  return {
    profileId,
    profileName,
    budgetMin: 0,
    budgetMax: 800000,
    selectedFlatTypes: ["4 ROOM"],
    workplaceAddress: null,
    anchorCoordinates: null,
    criteriaWeights: [],
    preferredCommuteMode: "PUBLIC_TRANSIT",
    departureTime: null,
    isActive: true,
    creationTime: null,
    lastUpdatedTime: null,
    minimumPrimarySchools: 0,
    minimumSecondarySchools: 0,
    minimumTertiarySchools: 0,
    minimumMalls: 0,
    minimumHospitals: 0,
  };
}

const profiles = [profile("profile-1", "Plan One"), profile("profile-2", "Plan Two")];

describe("ProfileSelectorUI", () => {
  it("shows the active plan and per-row Edit/Delete actions", () => {
    const onEdit = vi.fn();
    render(
      <ProfileSelectorUI
        profiles={profiles}
        activeProfileId="profile-1"
        onSelect={vi.fn()}
        onEdit={onEdit}
        onDelete={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Plan One" }));

    expect(screen.getAllByRole("menuitemradio")).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: "Edit" })).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: "Delete" })).toHaveLength(2);

    fireEvent.click(screen.getAllByRole("button", { name: "Edit" })[1]);
    expect(onEdit).toHaveBeenCalledWith("profile-2");
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });

  it("selects a plan from its row", () => {
    const onSelect = vi.fn();
    render(
      <ProfileSelectorUI
        profiles={profiles}
        activeProfileId="profile-1"
        onSelect={onSelect}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Plan One" }));
    fireEvent.click(screen.getByRole("menuitemradio", { name: /Plan Two/ }));

    expect(onSelect).toHaveBeenCalledWith("profile-2");
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });

  it("asks for confirmation before deleting a plan", async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined);
    render(
      <ProfileSelectorUI
        profiles={profiles}
        activeProfileId="profile-1"
        onSelect={vi.fn()}
        onEdit={vi.fn()}
        onDelete={onDelete}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Plan One" }));
    fireEvent.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    expect(onDelete).not.toHaveBeenCalled();
    expect(screen.getByRole("heading", { name: /Delete.*Plan One/ })).toBeInTheDocument();
    expect(screen.getByRole("dialog").closest(".app-header")).toBeNull();
    expect(document.querySelector(".modal-backdrop")?.parentElement).toBe(document.body);

    fireEvent.click(screen.getByRole("button", { name: "Delete plan" }));

    await waitFor(() => expect(onDelete).toHaveBeenCalledWith("profile-1"));
  });

  it("disables delete when only one plan is saved", () => {
    render(
      <ProfileSelectorUI
        profiles={profiles.slice(0, 1)}
        activeProfileId="profile-1"
        onSelect={vi.fn()}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Plan One" }));

    expect(screen.getByRole("button", { name: "Delete" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Delete" })).toHaveAttribute(
      "title",
      "Keep at least one saved plan before deleting this one.",
    );
  });
});
