import { useState } from "react";
import type { ApiClient } from "../api/client";
import { useBoardData } from "../hooks/useBoardData";
import { tasksInColumn } from "../lib/boardState";
import { ColumnView } from "./ColumnView";
import { SearchBox } from "./SearchBox";

interface Props {
  api: ApiClient;
  boardId: number;
  onBack: () => void;
}

export function BoardView({ api, boardId, onBack }: Props) {
  const [query, setQuery] = useState("");
  const { board, tasks, status, error, actionError, dismissActionError, reload, moveTask, addTask, removeTask } =
    useBoardData(api, boardId, query);

  // Positions are board-wide; reordering inside a filtered subset would be ambiguous.
  const dndEnabled = query === "";

  return (
    <div className="board">
      <div className="toolbar">
        <button className="link" onClick={onBack}>&larr; Boards</button>
        <h1>{board?.name ?? "Loading..."}</h1>
        <SearchBox onQuery={setQuery} />
      </div>

      {!dndEnabled && <p className="hint">Drag and drop is disabled while a search filter is active.</p>}
      {actionError && (
        <div role="alert" className="error banner">
          {actionError} <button className="link" onClick={dismissActionError}>Dismiss</button>
        </div>
      )}

      {status === "loading" && <p role="status">Loading tasks...</p>}
      {status === "error" && (
        <div role="alert" className="error banner">
          {error} <button onClick={reload}>Retry</button>
        </div>
      )}

      {board?.columns && status !== "error" && (
        <div className="columns">
          {board.columns.map((c) => (
            <ColumnView
              key={c.id}
              column={c}
              tasks={tasksInColumn(tasks, c.id)}
              dndEnabled={dndEnabled}
              onMove={moveTask}
              onAdd={(colId, title) => void addTask(colId, title)}
              onDelete={(id) => void removeTask(id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
