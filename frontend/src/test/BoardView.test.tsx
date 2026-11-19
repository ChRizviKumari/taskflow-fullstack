import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ApiClient } from "../api/client";
import { BoardView } from "../components/BoardView";

const board = {
  id: 1, owner_id: 1, name: "Sprint", created_at: "",
  columns: [{ id: 10, board_id: 1, name: "To Do", position: 0 }, { id: 20, board_id: 1, name: "Done", position: 1 }],
};
const task = {
  id: 1, board_id: 1, column_id: 10, title: "Ship it", description: "", priority: "medium" as const,
  position: 0, version: 1, created_at: "", updated_at: "",
};

describe("BoardView", () => {
  it("renders columns and tasks after loading", async () => {
    const api = {
      getBoard: vi.fn().mockResolvedValue({ board }),
      listTasks: vi.fn().mockResolvedValue({ items: [task], page: 1, page_size: 100, total: 1, total_pages: 1 }),
    } as unknown as ApiClient;
    render(<BoardView api={api} boardId={1} onBack={() => {}} />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading");
    expect(await screen.findByText("Ship it")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Done" })).toBeInTheDocument();
  });

  it("shows an error with retry when loading fails", async () => {
    const api = {
      getBoard: vi.fn().mockResolvedValue({ board }),
      listTasks: vi.fn().mockRejectedValue(new Error("Cannot reach the server")),
    } as unknown as ApiClient;
    render(<BoardView api={api} boardId={1} onBack={() => {}} />);
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Cannot reach the server"));
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
