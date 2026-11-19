import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, type ApiClient } from "../api/client";
import type { Board, Priority, Task } from "../api/types";
import { moveTaskLocal, replaceTask, tasksInColumn } from "../lib/boardState";

export type Status = "loading" | "ready" | "error";

const PAGE_SIZE = 100;

async function fetchAllTasks(api: ApiClient, boardId: number, q: string, signal: AbortSignal): Promise<Task[]> {
  const all: Task[] = [];
  for (let page = 1; ; page++) {
    const res = await api.listTasks(boardId, { q: q || undefined, page, page_size: PAGE_SIZE }, signal);
    all.push(...res.items);
    if (page >= res.total_pages) return all;
  }
}

function isAbort(err: unknown): boolean {
  return err instanceof DOMException && err.name === "AbortError";
}

function messageOf(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong";
}

export function useBoardData(api: ApiClient, boardId: number, query: string) {
  const [board, setBoard] = useState<Board | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [reloadTick, setReloadTick] = useState(0);

  const tasksRef = useRef(tasks);
  tasksRef.current = tasks;

  // Board metadata: once per board.
  useEffect(() => {
    const ctrl = new AbortController();
    setBoard(null);
    api.getBoard(boardId, ctrl.signal)
      .then((r) => setBoard(r.board))
      .catch((e) => { if (!isAbort(e)) { setStatus("error"); setError(messageOf(e)); } });
    return () => ctrl.abort();
  }, [api, boardId]);

  // Tasks: re-fetched when the search query changes; the previous request is aborted.
  useEffect(() => {
    const ctrl = new AbortController();
    setStatus((s) => (s === "ready" ? s : "loading"));
    fetchAllTasks(api, boardId, query, ctrl.signal)
      .then((list) => { setTasks(list); setStatus("ready"); setError(null); })
      .catch((e) => { if (!isAbort(e)) { setStatus("error"); setError(messageOf(e)); } });
    return () => ctrl.abort();
  }, [api, boardId, query, reloadTick]);

  const reload = useCallback(() => setReloadTick((n) => n + 1), []);

  /** Optimistic move: apply locally, call the API, roll back on any failure. */
  const moveTask = useCallback(
    async (taskId: number, toColumnId: number, beforeTaskId: number | null) => {
      const snapshot = tasksRef.current;
      const task = snapshot.find((t) => t.id === taskId);
      if (!task) return;
      const dest = tasksInColumn(snapshot, toColumnId).filter((t) => t.id !== taskId);
      const index = beforeTaskId === null ? dest.length : Math.max(0, dest.findIndex((t) => t.id === beforeTaskId));
      if (task.column_id === toColumnId && task.position === index) return; // no-op drop

      setActionError(null);
      setTasks(moveTaskLocal(snapshot, taskId, toColumnId, index));
      try {
        const { task: saved } = await api.updateTask(taskId, {
          version: task.version, column_id: toColumnId, position: index,
        });
        setTasks((cur) => replaceTask(cur, saved));
      } catch (err) {
        setTasks(snapshot); // rollback
        if (err instanceof ApiError && err.isConflict) {
          setActionError("Someone else changed this task. Your move was undone and the board refreshed.");
          reload();
        } else {
          setActionError(`Move failed and was undone: ${messageOf(err)}`);
        }
      }
    },
    [api, reload],
  );

  const addTask = useCallback(
    async (columnId: number, title: string, priority: Priority = "medium") => {
      setActionError(null);
      try {
        const { task } = await api.createTask(columnId, { title, priority });
        setTasks((cur) => [...cur, task]);
      } catch (err) {
        setActionError(`Could not add task: ${messageOf(err)}`);
      }
    },
    [api],
  );

  const removeTask = useCallback(
    async (taskId: number) => {
      const snapshot = tasksRef.current;
      setTasks(snapshot.filter((t) => t.id !== taskId));
      try {
        await api.deleteTask(taskId);
        reload(); // server closes position gaps; resync
      } catch (err) {
        setTasks(snapshot);
        setActionError(`Could not delete task: ${messageOf(err)}`);
      }
    },
    [api, reload],
  );

  return { board, tasks, status, error, actionError, dismissActionError: () => setActionError(null), reload, moveTask, addTask, removeTask };
}
