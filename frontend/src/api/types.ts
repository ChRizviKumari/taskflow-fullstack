export type Priority = "low" | "medium" | "high";

export interface User {
  id: number;
  email: string;
  name: string;
  created_at: string;
}

export interface Column {
  id: number;
  board_id: number;
  name: string;
  position: number;
  task_count?: number;
}

export interface Board {
  id: number;
  owner_id: number;
  name: string;
  created_at: string;
  task_count?: number;
  columns?: Column[];
}

export interface Task {
  id: number;
  board_id: number;
  column_id: number;
  title: string;
  description: string;
  priority: Priority;
  position: number;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface TaskPatch {
  version: number;
  title?: string;
  description?: string;
  priority?: Priority;
  column_id?: number;
  position?: number;
}

export interface TaskQuery {
  q?: string;
  priority?: Priority;
  column_id?: number;
  page?: number;
  page_size?: number;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: unknown;
}
