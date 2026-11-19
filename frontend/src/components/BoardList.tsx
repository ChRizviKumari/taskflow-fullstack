import { useCallback, useEffect, useState, type FormEvent } from "react";
import type { ApiClient } from "../api/client";
import type { Board } from "../api/types";

interface Props {
  api: ApiClient;
  onOpen: (id: number) => void;
}

export function BoardList({ api, onOpen }: Props) {
  const [boards, setBoards] = useState<Board[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");

  const load = useCallback(
    (signal?: AbortSignal) => {
      setLoading(true);
      api.listBoards({ page_size: 100 }, signal)
        .then((r) => { setBoards(r.items); setError(null); })
        .catch((e) => { if (!(e instanceof DOMException)) setError(e.message); })
        .finally(() => setLoading(false));
    },
    [api],
  );

  useEffect(() => {
    const ctrl = new AbortController();
    load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  async function create(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      const { board } = await api.createBoard(name.trim());
      setName("");
      onOpen(board.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create board");
    }
  }

  return (
    <div>
      <h1>Your boards</h1>
      <form onSubmit={create} className="add">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="New board name" aria-label="New board name" maxLength={100} />
        <button type="submit">Create</button>
      </form>
      {loading && <p role="status">Loading boards...</p>}
      {error && <p role="alert" className="error">{error} <button onClick={() => load()}>Retry</button></p>}
      {!loading && !error && boards.length === 0 && <p className="empty">No boards yet. Create your first one above.</p>}
      <ul className="boards">
        {boards.map((b) => (
          <li key={b.id}>
            <button className="card" onClick={() => onOpen(b.id)}>
              <strong>{b.name}</strong>
              <span>{b.task_count ?? 0} tasks</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
