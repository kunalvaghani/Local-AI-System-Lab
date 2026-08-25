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

describe("Stage 20 agent and scheduler visualization", () => {
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

  it("preserves selected task context while navigating agent and scheduler views", async () => {
    window.history.replaceState(null, "", `/runtime?task=${taskFixture.task_id}`);
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("link", { name: /Agents/ }));
    expect(window.location.pathname).toBe("/agents");
    expect(window.location.search).toBe(`?task=${taskFixture.task_id}`);
    expect(await screen.findByRole("heading", { name: "Agent state map" })).toBeInTheDocument();
    expect(screen.getAllByText("Technical Explainer").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("link", { name: /Scheduler/ }));
    expect(window.location.pathname).toBe("/scheduler");
    expect(window.location.search).toBe(`?task=${taskFixture.task_id}`);
    expect(await screen.findByRole("heading", { name: "Request placement" })).toBeInTheDocument();
  });

  it("renders the selected agent state path from ordered lifecycle evidence", async () => {
    window.history.replaceState(null, "", `/agents?task=${taskFixture.task_id}`);
    render(<App />);

    await screen.findByRole("heading", { name: "Agent state map" });
    await waitFor(() => expect(EventSourceFixture.instances.length).toBeGreaterThan(0));
    act(() => {
      const source = EventSourceFixture.instances.at(-1)!;
      source.open();
      source.emit("lifecycle", "4", { name: "admission.evaluated", recorded_at_utc: "2026-08-25T12:00:00.015000+00:00", agent_id: "technical-explainer", task_id: taskFixture.task_id, state: "admitted", data: { action: "accept", permitted: true, reason: "Estimated resources fit measured capacity.", confidence: "high", estimate: { model_id: "qwen-test", context_tokens: 2048, gpu_layers: 12, predicted_host_ram_mib: 2200, predicted_vram_mib: 1800 }, constraints: [] } });
      source.emit("lifecycle", "5", { name: "task.executing", recorded_at_utc: "2026-08-25T12:00:00.020000+00:00", agent_id: "technical-explainer", task_id: taskFixture.task_id, state: "executing", data: {} });
    });

    expect(await screen.findByText("admitted")).toBeInTheDocument();
    expect(screen.getAllByText("executing").length).toBeGreaterThan(0);
    expect(screen.getByText("Estimated resources fit measured capacity.")).toBeInTheDocument();
    expect(screen.getByText("local-docs [read]")).toBeInTheDocument();
  });

  it("projects priority dispatch and exposes real scheduler timings and cancellation", async () => {
    window.history.replaceState(null, "", `/scheduler?task=${taskFixture.task_id}`);
    const user = userEvent.setup();
    render(<App />);

    await screen.findAllByText("task-interactive");
    const queue = screen.getByRole("heading", { name: "Projected queue" });
    const list = queue.closest("article")!;
    const items = within(list).getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("task-interactive");
    expect(items[1]).toHaveTextContent("task-background");
    expect(screen.getAllByText("0.2 ms").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "Cancel task" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(`/v1/tasks/${taskFixture.task_id}`, expect.objectContaining({ method: "DELETE" })));
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

  it.each([
    ["Agents", "/agents", "Agent state map"],
    ["Scheduler", "/scheduler", "Scheduler map"],
  ])("has no automated accessibility violations in the %s workspace", async (_label, path, heading) => {
    window.history.replaceState(null, "", `${path}?task=${taskFixture.task_id}`);
    const { container } = render(<App />);
    await screen.findByRole("heading", { name: heading });
    await screen.findAllByText(taskFixture.task_id);
    let results: axe.AxeResults | undefined;

    await act(async () => {
      results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    });

    expect(results?.violations ?? []).toEqual([]);
  });
});
