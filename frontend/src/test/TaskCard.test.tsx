import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Task } from "../api/types";
import { TaskCard } from "../components/TaskCard";

const task: Task = {
  id: 5, board_id: 1, column_id: 1, title: "Write tests", description: "soon", priority: "high",
  position: 0, version: 1, created_at: "", updated_at: "",
};

describe("TaskCard", () => {
  it("renders title, description and priority", () => {
    render(<TaskCard task={task} draggable onDelete={() => {}} />);
    expect(screen.getByText("Write tests")).toBeInTheDocument();
    expect(screen.getByText("soon")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("is draggable only when enabled", () => {
    const { rerender } = render(<TaskCard task={task} draggable onDelete={() => {}} />);
    expect(screen.getByTestId("task-5")).toHaveAttribute("draggable", "true");
    rerender(<TaskCard task={task} draggable={false} onDelete={() => {}} />);
    expect(screen.getByTestId("task-5")).toHaveAttribute("draggable", "false");
  });

  it("calls onDelete", () => {
    const onDelete = vi.fn();
    render(<TaskCard task={task} draggable onDelete={onDelete} />);
    fireEvent.click(screen.getByLabelText("Delete Write tests"));
    expect(onDelete).toHaveBeenCalledWith(5);
  });

  it("reports a drop before this card using dataTransfer", () => {
    const onDropBefore = vi.fn();
    render(<TaskCard task={task} draggable onDelete={() => {}} onDropBefore={onDropBefore} />);
    fireEvent.drop(screen.getByTestId("task-5"), { dataTransfer: { getData: () => "9" } });
    expect(onDropBefore).toHaveBeenCalledWith(9, 5);
  });
});
