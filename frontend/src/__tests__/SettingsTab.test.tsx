import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import SettingsTab from "@/components/SettingsTab";
import { mockSettings } from "./fixtures";

vi.mock("@/lib/api", () => ({
  saveSettings: vi.fn(),
  listBackups: vi.fn(),
  restoreBackup: vi.fn(),
  createBackup: vi.fn(),
}));

import { saveSettings, listBackups, createBackup } from "@/lib/api";

describe("SettingsTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listBackups).mockResolvedValue([]);
  });

  it("renders title and description", () => {
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    expect(screen.getByText(/Application Settings/)).toBeInTheDocument();
  });

  it("shows 4 sub-tab buttons", () => {
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    // Sub-tab nav is within the border-b container
    expect(screen.getByRole("button", { name: /🔍 Keywords/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /📰 Journals/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /📊 Scoring/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /💾 Backup/ })).toBeInTheDocument();
  });

  it("shows Keywords sub-tab by default", () => {
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    expect(screen.getByText("Research Keywords")).toBeInTheDocument();
    expect(screen.getByText(/Keyword Priority Scoring/)).toBeInTheDocument();
  });

  it("switches to Journals sub-tab", async () => {
    const user = userEvent.setup();
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /📰 Journals/ }));
    expect(screen.getByText("Target Journals")).toBeInTheDocument();
    expect(screen.getByText(/Exact Matches/)).toBeInTheDocument();
  });

  it("switches to Scoring sub-tab", async () => {
    const user = userEvent.setup();
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /📊 Scoring/ }));
    expect(screen.getByText("Journal Impact Scoring")).toBeInTheDocument();
    expect(screen.getByText("Search Configuration")).toBeInTheDocument();
  });

  it("switches to Backup sub-tab", async () => {
    const user = userEvent.setup();
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /💾 Backup/ }));
    expect(screen.getByText("Available Backups")).toBeInTheDocument();
  });
});

describe("Keywords sub-tab", () => {
  it("shows keywords textarea with current keywords", () => {
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveValue(mockSettings.keywords.join("\n"));
  });

  it("shows high/medium priority multiselects", () => {
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    expect(screen.getByText(/High Priority/)).toBeInTheDocument();
    expect(screen.getByText(/Medium Priority/)).toBeInTheDocument();
  });

  it("shows must-have keywords section", () => {
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    expect(screen.getByText(/Must Have Keywords/)).toBeInTheDocument();
  });

  it("calls saveSettings on save", async () => {
    const user = userEvent.setup();
    vi.mocked(saveSettings).mockResolvedValue({ status: "ok" });
    const onSettingsChange = vi.fn().mockResolvedValue(undefined);

    render(<SettingsTab settings={mockSettings} onSettingsChange={onSettingsChange} />);
    await user.click(screen.getByRole("button", { name: /Save Keywords/ }));

    await waitFor(() => {
      expect(saveSettings).toHaveBeenCalled();
    });
  });
});

describe("Scoring sub-tab", () => {
  it("shows journal impact scoring checkbox enabled", async () => {
    const user = userEvent.setup();
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /📊 Scoring/ }));

    const checkbox = screen.getByRole("checkbox", { name: /Enable Journal Impact Scoring/ });
    expect(checkbox).toBeChecked();
  });

  it("shows search configuration fields", async () => {
    const user = userEvent.setup();
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /📊 Scoring/ }));

    expect(screen.getByText("Days Back")).toBeInTheDocument();
    expect(screen.getByText("Min Keyword Matches")).toBeInTheDocument();
    expect(screen.getByText("Default Search Mode")).toBeInTheDocument();
  });

  it("shows default data sources", async () => {
    const user = userEvent.setup();
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /📊 Scoring/ }));

    expect(screen.getByRole("checkbox", { name: "PubMed" })).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "arXiv" })).toBeInTheDocument();
  });
});

describe("Backup sub-tab", () => {
  it("shows empty backups message", async () => {
    const user = userEvent.setup();
    vi.mocked(listBackups).mockResolvedValue([]);
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /💾 Backup/ }));

    expect(screen.getByText(/No backups found/)).toBeInTheDocument();
  });

  it("shows create backup button", async () => {
    const user = userEvent.setup();
    render(<SettingsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /💾 Backup/ }));

    expect(screen.getByRole("button", { name: /Create Backup Now/ })).toBeInTheDocument();
  });
});
