import { useState } from "react";
import { BoardList } from "./components/BoardList";
import { BoardView } from "./components/BoardView";
import { LoginForm } from "./components/LoginForm";
import { useAuth } from "./context/AuthContext";

export default function App() {
  const { user, api, logout } = useAuth();
  const [boardId, setBoardId] = useState<number | null>(null);

  if (!user) return <main><LoginForm /></main>;

  return (
    <main>
      <nav className="topbar">
        <span>Signed in as {user.name}</span>
        <button className="link" onClick={logout}>Sign out</button>
      </nav>
      {boardId === null
        ? <BoardList api={api} onOpen={setBoardId} />
        : <BoardView api={api} boardId={boardId} onBack={() => setBoardId(null)} />}
    </main>
  );
}
