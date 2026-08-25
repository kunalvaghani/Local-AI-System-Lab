import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { STORAGE_KEY } from "./hooks/useDensity";
import { routes } from "./navigation/routes";
import { queryClient } from "./query/QueryProvider";
import { EventSourceFixture, runtimeFetch, taskFixture } from "./test/runtimeFixtures";

beforeEach(() => {
  window.history.replaceState(null, "", "/runtime");
  window.localStorage.clear();
  queryClient.clear();
  EventSourceFixture.instances = [];
  vi.stubGlobal("fetch", vi.fn(runtimeFetch));
  vi.stubGlobal("EventSource", EventSourceFixture);
});

afterEach(() => {
  cleanup();
  delete document.documentElement.dataset.density;
  queryClient.clear();
  vi.unstubAllGlobals();
});

describe("Stage 19 runtime command center", () => {
  it("renders real API evidence and keeps unavailable fields honest", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: "Runtime" })).toBeInTheDocument();
    expect(await screen.findByText("API live")).toBeInTheDocument();
    expect(screen.getByText("Qwen 2.5 1.5B")).toBeInTheDocument();
    expect(screen.getByText("12 GiB")).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
    expect(within(screen.getByRole("navigation", { name: "Application areas" })).getAllByRole("link")).toHaveLength(routes.length);
  });

  it("launches a real API task contract and makes its ID URL-addressable", async () => {
    const user = userEvent.setup();
    render(<App />);

    await screen.findByRole("option", { name: "Technical Explainer" });
    const objective = screen.getByRole("textbox", { name: /Objective/ });
    await waitFor(() => expect(objective).toBeEnabled());
    fireEvent.change(objective, { target: { value: "Explain the bounded local runtime." } });
    expect(objective).toHaveValue("Explain the bounded local runtime.");
    expect(screen.getByRole("combobox", { name: "Agent" })).toHaveValue("technical-explainer");
    const launchButton = screen.getByRole("button", { name: "Launch task" });
    await waitFor(() => expect(launchButton).toBeEnabled());
    await user.click(launchButton);

    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/v1/tasks", expect.objectContaining({ method: "POST" })));
    await waitFor(() => expect(window.location.search).toBe(`?task=${taskFixture.task_id}`));
    expect(await screen.findByText(taskFixture.task_id)).toBeInTheDocument();
    expect(screen.getByText("executing")).toBeInTheDocument();
  });

  it("follows ordered lifecycle evidence and sends cancellation to the API", async () => {
    window.history.replaceState(null, "", `/runtime?task=${taskFixture.task_id}`);
    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByText(taskFixture.task_id)).toBeInTheDocument();
    await waitFor(() => expect(EventSourceFixture.instances).toHaveLength(1));
    act(() => {
      EventSourceFixture.instances[0].open();
      EventSourceFixture.instances[0].emit("lifecycle", "7", {
        name: "task.executing",
        recorded_at_utc: "2026-08-25T12:00:00.020000+00:00",
        agent_id: "technical-explainer",
        task_id: taskFixture.task_id,
        state: "executing",
        data: {},
      });
    });
    expect(await screen.findByText("task.executing")).toBeInTheDocument();
    expect(screen.getByText("live")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cancel task" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      `/v1/tasks/${taskFixture.task_id}`,
      expect.objectContaining({ method: "DELETE" }),
    ));
    expect(await screen.findByRole("button", { name: "Cancellation requested" })).toBeDisabled();
  });

  it("keeps application areas URL-addressable", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("link", { name: /Security/ }));

    expect(window.location.pathname).toBe("/security");
    expect(screen.getByRole("heading", { level: 1, name: "Security" })).toBeInTheDocument();
    expect(screen.getAllByText("/v1/security/results").length).toBeGreaterThan(0);
  });

  it("exposes the reusable status and visualization contracts", async () => {
    window.history.replaceState(null, "", "/design-system");
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByRole("heading", { name: "Systems Cartography language" })).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "States" }));
    expect(screen.getByText("Healthy")).toBeInTheDocument();
    expect(screen.getByText("Partial")).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Visualization" }));
    expect(screen.getByRole("heading", { name: "Truth before spectacle" })).toBeInTheDocument();
  });

  it("persists only the versioned device-local density preference", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("radio", { name: "Compact" }));

    expect(document.documentElement).toHaveAttribute("data-density", "compact");
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("compact");
  });

  it("has no automated accessibility violations in the primary shell", async () => {
    const { container } = render(<App />);
    let results: axe.AxeResults | undefined;

    await act(async () => {
      results = await axe.run(container, {
        rules: {
          "color-contrast": { enabled: false },
        },
      });
    });

    expect(results?.violations ?? []).toEqual([]);
  });
});
