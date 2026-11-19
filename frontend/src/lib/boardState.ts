import type { Task } from "../api/types";

/** Tasks of one column, ordered by position. */
export function tasksInColumn(tasks: readonly Task[], columnId: number): Task[] {
  return tasks.filter((t) => t.column_id === columnId).sort((a, b) => a.position - b.position || a.id - b.id);
}

function renumber(list: Task[]): Task[] {
  return list.map((t, i) => (t.position === i ? t : { ...t, position: i }));
}

/**
 * Pure, immutable move used for optimistic updates. Mirrors the server: the target
 * index is clamped and positions in the source and destination columns are made contiguous.
 * `version` is intentionally untouched; the server's response supplies the new one.
 */
export function moveTaskLocal(
  tasks: readonly Task[],
  taskId: number,
  toColumnId: number,
  toIndex: number,
): Task[] {
  const moving = tasks.find((t) => t.id === taskId);
  if (!moving) return [...tasks];
  const fromColumnId = moving.column_id;

  const source = tasksInColumn(tasks, fromColumnId).filter((t) => t.id !== taskId);
  const dest = fromColumnId === toColumnId ? source : tasksInColumn(tasks, toColumnId);
  const idx = Math.max(0, Math.min(toIndex, dest.length));
  const inserted = [...dest.slice(0, idx), { ...moving, column_id: toColumnId }, ...dest.slice(idx)];

  const updated = new Map<number, Task>();
  for (const t of renumber(inserted)) updated.set(t.id, t);
  if (fromColumnId !== toColumnId) for (const t of renumber(source)) updated.set(t.id, t);

  return tasks.map((t) => updated.get(t.id) ?? t);
}

/** Replace one task (e.g. with the server's authoritative copy). */
export function replaceTask(tasks: readonly Task[], next: Task): Task[] {
  return tasks.map((t) => (t.id === next.id ? next : t));
}
