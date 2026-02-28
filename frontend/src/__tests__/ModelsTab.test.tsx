import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ModelsTab from "@/components/ModelsTab";
import { mockSettings, mockModels } from "./fixtures";

vi.mock("@/lib/api", () => ({
  listModels: vi.fn(),
  saveModel: vi.fn(),
  loadModel: vi.fn(),
  previewModel: vi.fn(),
  deleteModel: vi.fn(),
  saveSettings: vi.fn(),
}));

import { listModels, saveModel, loadModel, previewModel, deleteModel } from "@/lib/api";

describe("ModelsTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listModels).mockResolvedValue([]);
  });

  it("renders title and description", () => {
    render(<ModelsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    expect(screen.getByText(/Model Management/)).toBeInTheDocument();
  });

  it("shows save input and button", () => {
    render(<ModelsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    expect(screen.getByPlaceholderText(/AD Neuroimaging Focus/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Save/ })).toBeInTheDocument();
  });

  it("shows empty models message when none exist", () => {
    render(<ModelsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    expect(screen.getByText(/No saved models yet/)).toBeInTheDocument();
  });

  it("lists models after loading", async () => {
    vi.mocked(listModels).mockResolvedValue(mockModels);
    render(<ModelsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText("AD Neuroimaging")).toBeInTheDocument();
      expect(screen.getByText("Tau PET Focus")).toBeInTheDocument();
    });
  });

  it("shows flash error when saving with empty name", async () => {
    const user = userEvent.setup();
    render(<ModelsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /Save/ }));
    expect(screen.getByText(/Please enter a model name/)).toBeInTheDocument();
  });

  it("calls saveModel API and refreshes list", async () => {
    const user = userEvent.setup();
    vi.mocked(saveModel).mockResolvedValue({ status: "ok", filename: "Test.json" });
    vi.mocked(listModels).mockResolvedValue(mockModels);

    render(<ModelsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    const input = screen.getByPlaceholderText(/AD Neuroimaging Focus/);
    await user.type(input, "Test Model");
    await user.click(screen.getByRole("button", { name: /Save/ }));

    await waitFor(() => {
      expect(saveModel).toHaveBeenCalledWith("Test Model");
    });
  });

  it("shows Load, Preview, Delete buttons for each model", async () => {
    vi.mocked(listModels).mockResolvedValue([mockModels[0]]);
    render(<ModelsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Load" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Preview" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
    });
  });

  it("calls loadModel and onSettingsChange when Load is clicked", async () => {
    const user = userEvent.setup();
    const onSettingsChange = vi.fn().mockResolvedValue(undefined);
    vi.mocked(listModels).mockResolvedValue([mockModels[0]]);
    vi.mocked(loadModel).mockResolvedValue({ status: "ok" });

    render(<ModelsTab settings={mockSettings} onSettingsChange={onSettingsChange} />);
    await waitFor(() => screen.getByText("AD Neuroimaging"));
    await user.click(screen.getByRole("button", { name: "Load" }));

    await waitFor(() => {
      expect(loadModel).toHaveBeenCalledWith("AD_Neuroimaging.json");
      expect(onSettingsChange).toHaveBeenCalled();
    });
  });

  it("shows preview panel when Preview is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(listModels).mockResolvedValue([mockModels[0]]);
    vi.mocked(previewModel).mockResolvedValue(mockSettings);

    render(<ModelsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    await waitFor(() => screen.getByText("AD Neuroimaging"));
    await user.click(screen.getByRole("button", { name: "Preview" }));

    await waitFor(() => {
      expect(screen.getByText(/Preview: AD Neuroimaging/)).toBeInTheDocument();
    });
  });

  it("shows export and import buttons", () => {
    render(<ModelsTab settings={mockSettings} onSettingsChange={vi.fn()} />);
    expect(screen.getByText(/Export Settings JSON/)).toBeInTheDocument();
    expect(screen.getByText(/Import Settings/)).toBeInTheDocument();
  });
});
