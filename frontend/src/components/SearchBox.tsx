import { useEffect, useState } from "react";
import { useDebounced } from "../hooks/useDebounced";

interface Props {
  onQuery: (q: string) => void;
  delayMs?: number;
}

/** Type-ahead: emits the trimmed query after the user pauses typing. */
export function SearchBox({ onQuery, delayMs = 250 }: Props) {
  const [text, setText] = useState("");
  const debounced = useDebounced(text.trim(), delayMs);
  useEffect(() => onQuery(debounced), [debounced, onQuery]);
  return (
    <input
      type="search"
      className="search"
      placeholder="Search tasks..."
      aria-label="Search tasks"
      value={text}
      onChange={(e) => setText(e.target.value)}
    />
  );
}
