import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ApiClient } from "../api/client";
import { ApiError } from "../api/client";
import { AuthProvider } from "../context/AuthContext";
import { LoginForm } from "../components/LoginForm";

function fakeApi(login: ApiClient["login"]): ApiClient {
  return { login } as unknown as ApiClient;
}

describe("LoginForm", () => {
  it("shows the server error message on failed login", async () => {
    const login = vi.fn().mockRejectedValue(new ApiError(401, "invalid_credentials", "Invalid email or password"));
    render(<AuthProvider apiOverride={fakeApi(login)}><LoginForm /></AuthProvider>);
    await userEvent.type(screen.getByLabelText("Email"), "a@b.co");
    await userEvent.type(screen.getByLabelText("Password"), "password123");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password");
  });

  it("submits credentials", async () => {
    const login = vi.fn().mockResolvedValue({ token: "t", user: { id: 1, email: "a@b.co", name: "A", created_at: "" } });
    render(<AuthProvider apiOverride={fakeApi(login)}><LoginForm /></AuthProvider>);
    await userEvent.type(screen.getByLabelText("Email"), "a@b.co");
    await userEvent.type(screen.getByLabelText("Password"), "password123");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(login).toHaveBeenCalledWith("a@b.co", "password123"));
  });
});
