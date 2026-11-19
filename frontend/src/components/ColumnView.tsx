import { useState, type DragEvent, type FormEvent } from "react";
import type { Column, Task } from "../api/types";
import { TaskCard } from "./TaskCard";

interface Props {
  column: Column;
  tasks: Task[];
  dndEnabled: boolean;
  onMove: (taskId: number, columnId: number, beforeTaskId: number | null) => void;
  onAdd: (columnId: number, title: string) => void;
  onDelete: (taskId: number) => void;
}

export function ColumnView({ column, tasks, dndEnabled, onMove, onAdd, onDelete }: Props) {
  const [over, setOver] = useState(false);
  const [title, setTitle] = useState("");

  function drop(e: DragEvent<HTMLElement>) {
    e.preventDefault();
    setOver(false);
    const id = Number(e.dataTransfer.getData("text/plain"));
    if (Number.isInteger(id)) onMove(id, column.id, null);
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    const t = title.trim();
    if (!t) return;
    onAdd(column.id, t);
    setTitle("");
  }

  return (
    <section
      className={`column${over ? " over" : ""}`}
      aria-label={column.name}
      onDragOver={dndEnabled ? (e) => { e.preventDefault(); setOver(true); } : undefined}
      onDragLeave={() => setOver(false)}
      onDrop={dndEnabled ? drop : undefined}
    >
      <h2>{column.name} <span className="count">{tasks.length}</span></h2>
      <div className="tasks">
        {tasks.map((t) => (
          <TaskCard
            key={t.id}
            task={t}
            draggable={dndEnabled}
            onDelete={onDelete}
            onDropBefore={(dragged, before) => { setOver(false); onMove(dragged, column.id, before); }}
          />
        ))}
        {tasks.length === 0 && <p className="empty">No tasks</p>}
      </div>
      <form onSubmit={submit} className="add">
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Add a task" aria-label={`Add task to ${column.name}`} maxLength={200} />
      </form>
    </section>
  );
}
