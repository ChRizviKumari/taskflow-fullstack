import { describe, expect, it, vi } from "vitest";
import { ApiError, buildQuery, createApiClient } from "../api/client";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

describe("api client", () => {
  it("builds query strings and skips empty values", () => {
    expect(buildQuery({ q: "a b", page: 2, priority: undefined, x: "" })).toBe("?q=a+b&page=2");
    expect(buildQuery({})).toBe("");
  });

  it("sends the bearer token and JSON body", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(200, { task: { id: 1 } }));
    const api = createApiClient({ getToken: () => "tok", fetchImpl });
    await api.updateTask(1, { version: 3, title: "x" });
    const [url, init] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/tasks/1");
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer tok");
    expect(JSON.parse(init.body as string)).toEqual({ version: 3, title: "x" });
  });

  it("maps the error envelope to ApiError", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse(409, { error: { code: "version_conflict", message: "stale" } }),
    );
    const api = createApiClient({ getToken: () => null, fetchImpl });
    const err = await api.updateTask(1, { version: 1, title: "x" }).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).isConflict).toBe(true);
  });

  it("calls onUnauthorized on 401 when a token was sent", async () => {
    const onUnauthorized = vi.fn();
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(401, { error: { code: "unauthorized", message: "no" } }));
    const api = createApiClient({ getToken: () => "tok", onUnauthorized, fetchImpl });
    await api.me().catch(() => undefined);
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });

  it("wraps network failures", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new TypeError("boom"));
    const api = createApiClient({ getToken: () => null, fetchImpl });
    await expect(api.me()).rejects.toMatchObject({ code: "network_error" });
  });
});
