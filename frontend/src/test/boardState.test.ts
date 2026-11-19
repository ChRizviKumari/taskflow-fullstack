import { describe, expect, it } from "vitest";
import type { Task } from "../api/types";
import { moveTaskLocal, tasksInColumn } from "../lib/boardState";

function t(id: number, column_id: number, position: number): Task {
  return {
    id, column_id, position, board_id: 1, title: `t${id}`, description: "", priority: "medium",
    version: 1, created_at: "", updated_at: "",
  };
}

const base = [t(1, 10, 0), t(2, 10, 1), t(3, 10, 2), t(4, 20, 0)];

describe("moveTaskLocal", () => {
  it("moves across columns and renumbers both", () => {
    const out = moveTaskLocal(base, 2, 20, 0);
    expect(tasksInColumn(out, 10).map((x) => [x.id, x.position])).toEqual([[1, 0], [3, 1]]);
    expect(tasksInColumn(out, 20).map((x) => [x.id, x.position])).toEqual([[2, 0], [4, 1]]);
  });

  it("reorders within a column", () => {
    const out = moveTaskLocal(base, 3, 10, 0);
    expect(tasksInColumn(out, 10).map((x) => x.id)).toEqual([3, 1, 2]);
  });

  it("clamps an out-of-range index", () => {
    const out = moveTaskLocal(base, 1, 20, 99);
    expect(tasksInColumn(out, 20).map((x) => x.id)).toEqual([4, 1]);
  });

  it("does not mutate its input and keeps versions", () => {
    const frozen = Object.freeze(base.map((x) => Object.freeze({ ...x })));
    const out = moveTaskLocal(frozen, 1, 20, 0);
    expect(frozen[0].column_id).toBe(10);
    expect(out.every((x) => x.version === 1)).toBe(true);
  });

  it("ignores unknown ids", () => {
    expect(moveTaskLocal(base, 999, 20, 0)).toEqual(base);
  });
});
