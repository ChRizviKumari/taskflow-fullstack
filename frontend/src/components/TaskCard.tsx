import type { DragEvent } from "react";
import type { Task } from "../api/types";

interface Props {
  task: Task;
  draggable: boolean;
  onDelete: (id: number) => void;
  onDragStart?: (id: number) => void;
  onDragEnd?: () => void;
  onDropBefore?: (taskId: number, beforeId: number) => void;
}

export function TaskCard({ task, draggable, onDelete, onDragStart, onDragEnd, onDropBefore }: Props) {
  function handleDragStart(e: DragEvent<HTMLElement>) {
    e.dataTransfer.setData("text/plain", String(task.id));
    e.dataTransfer.effectAllowed = "move";
    onDragStart?.(task.id);
  }

  function handleDrop(e: DragEvent<HTMLElement>) {
    const dragged = Number(e.dataTransfer.getData("text/plain"));
    if (!Number.isInteger(dragged) || dragged === task.id) return;
    e.preventDefault();
    e.stopPropagation(); // do not also trigger the column's "append" drop
    onDropBefore?.(dragged, task.id);
  }

  return (
    <article
      className={`task priority-${task.priority}`}
      draggable={draggable}
      onDragStart={draggable ? handleDragStart : undefined}
      onDragEnd={onDragEnd}
      onDragOver={draggable ? (e) => e.preventDefault() : undefined}
      onDrop={draggable ? handleDrop : undefined}
      data-testid={`task-${task.id}`}
    >
      <header>
        <strong>{task.title}</strong>
        <button className="icon" aria-label={`Delete ${task.title}`} onClick={() => onDelete(task.id)}>
          x
        </button>
      </header>
      {task.description && <p>{task.description}</p>}
      <footer>
        <span className="badge">{task.priority}</span>
      </footer>
    </article>
  );
}
