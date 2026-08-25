import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { STORAGE_KEY } from "./hooks/useDensity";
import { routes } from "./navigation/routes";
import { queryClient } from "./query/QueryProvider";
import { EventSourceFixture, replayFixture, runtimeFetch, taskFixture, traceFixture } from "./test/runtimeFixtures";

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

describe("Stage 23 chaos and security lab", () => {
  it("renders real API evidence in the runtime overview", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: "Runtime" })).toBeInTheDocument();
    expect(await screen.findByText("API live")).toBeInTheDocument();
    expect(screen.getByText("Qwen 2.5 1.5B")).toBeInTheDocument();
    expect(screen.getByText("12 GiB")).toBeInTheDocument();
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

  it("loads a real redacted trace and filters model, tool, and state steps", async () => {
    window.history.replaceState(null, "", `/traces?task=${taskFixture.task_id}`);
    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Trace explorer" })).toBeInTheDocument();
    expect(await screen.findByText(traceFixture.run.run_id)).toBeInTheDocument();
    expect(screen.getByText("model.invocation.started")).toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox", { name: "Kind" }), "tool");
    expect(screen.getByText("tool.execution.completed")).toBeInTheDocument();
    expect(screen.queryByText("model.invocation.started")).not.toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox", { name: "Kind" }), "state");
    expect(screen.getByText("task.state.changed")).toBeInTheDocument();
    expect(screen.getByText(/planning → executing/)).toBeInTheDocument();
  });

  it("makes expanded trace-step evidence URL-addressable and keeps payloads redacted", async () => {
    window.history.replaceState(null, "", `/traces?task=${taskFixture.task_id}`);
    const user = userEvent.setup();
    render(<App />);

    const step = await screen.findByRole("button", { name: /model.invocation.started/ });
    await user.click(step);

    expect(window.location.search).toContain(`step=${traceFixture.steps[2].step_id}`);
    expect(screen.getByText(traceFixture.steps[2].semantic_hash)).toBeInTheDocument();
    expect(screen.getByText(/Input and output payloads are not returned/)).toBeInTheDocument();
    expect(screen.getByText("Δ 15 ms")).toBeInTheDocument();
  });

  it("runs deterministic replay explicitly and explains per-step outcomes", async () => {
    window.history.replaceState(null, "", `/traces?task=${taskFixture.task_id}`);
    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Replay deterministic reducers" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(`/v1/traces/${traceFixture.run.run_id}/replay`, expect.objectContaining({ method: "POST", body: "{}" })));
    expect(await screen.findByText(replayFixture.replay_id)).toBeInTheDocument();
    expect(screen.getByText("Valid")).toBeInTheDocument();
    expect(screen.getByText("Side effects skipped")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /tool.execution.completed/ }));
    expect(await screen.findByText("side-effecting operation was not re-executed")).toBeInTheDocument();
  });

  it("reports an honest empty result when trace filters match nothing", async () => {
    window.history.replaceState(null, "", `/traces?task=${taskFixture.task_id}`);
    render(<App />);

    const searchbox = await screen.findByRole("searchbox", { name: "Search trace" });
    fireEvent.change(searchbox, { target: { value: "not-a-real-trace-event" } });
    expect(searchbox).toHaveValue("not-a-real-trace-event");
    expect(await screen.findByText("No trace steps match the current filters.")).toBeInTheDocument();
  });

  it("bounds the rendered timeline to 100 rows for a 10,000-step trace", async () => {
    const originalSteps = traceFixture.steps;
    traceFixture.steps = Array.from({ length: 10_000 }, (_, index) => ({
      ...originalSteps[index % originalSteps.length],
      ordinal: index,
      step_id: `large-fixture-step-${index}`,
      recorded_at_utc: new Date(Date.parse("2026-08-25T12:00:00.000Z") + index).toISOString(),
    }));

    try {
      window.history.replaceState(null, "", `/traces?task=${taskFixture.task_id}`);
      const user = userEvent.setup();
      render(<App />);

      const timelineHeading = await screen.findByRole("heading", { name: "Execution timeline" });
      const timeline = timelineHeading.closest("article")!;
      expect(within(timeline).getAllByRole("listitem")).toHaveLength(100);
      expect(within(timeline).getByText("Page 1 of 100")).toBeInTheDocument();

      await user.click(within(timeline).getByRole("button", { name: "Next" }));
      expect(within(timeline).getByText("Page 2 of 100")).toBeInTheDocument();
      expect(within(timeline).getAllByRole("listitem")).toHaveLength(100);
    } finally {
      traceFixture.steps = originalSteps;
    }
  });

  it("visualizes measured CPU, RAM, GPU, and VRAM with source boundaries", async () => {
    window.history.replaceState(null, "", "/hardware");
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Hardware & performance lab" })).toBeInTheDocument();
    expect(await screen.findByText("Test CPU")).toBeInTheDocument();
    expect(await screen.findByText("Test GPU")).toBeInTheDocument();
    expect(screen.getByLabelText("RAM used")).toHaveValue(37.5);
    expect(screen.getByLabelText("VRAM used")).toHaveValue(25);
    expect(screen.getByLabelText("GPU utilization")).toHaveValue(12);
    expect(screen.getByText(/CPU percentage is not exposed/)).toBeInTheDocument();
    expect(screen.getAllByText("test").length).toBeGreaterThan(0);
  });

  it("investigates TTFT, throughput, queue delay, and bounded distributions", async () => {
    window.history.replaceState(null, "", `/metrics?task=${taskFixture.task_id}`);
    render(<App />);

    const signals = await screen.findByLabelText("Inference and scheduler signals");
    expect(await within(signals).findByText("1,600 ms")).toBeInTheDocument();
    expect(within(signals).getByText("99.8 tokens/s")).toBeInTheDocument();
    expect(within(signals).getByText("0.2 ms")).toBeInTheDocument();
    expect(within(signals).getByText("0 / 3")).toBeInTheDocument();

    const missingVram = screen.getByRole("row", { name: /VRAM delta/ });
    expect(within(missingVram).getByText("0")).toBeInTheDocument();
    expect(within(missingVram).getAllByText("Unavailable")).toHaveLength(3);
  });

  it("shows model availability, selected workload budget, and recent task trends", async () => {
    window.history.replaceState(null, "", `/hardware?task=${taskFixture.task_id}`);
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Recent workload trend" })).toBeInTheDocument();
    expect(await screen.findByText("task-history-new")).toBeInTheDocument();
    expect(await screen.findByText("task-history-old")).toBeInTheDocument();
    expect(screen.getByText("standard budget")).toBeInTheDocument();
    expect(screen.getByText(/64 tokens · 30,000 ms/)).toBeInTheDocument();
    expect(screen.getByText("Qwen 2.5 0.5B")).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
    expect(screen.getByText(/continuous time series is not inferred|not a background hardware sampler/i)).toBeInTheDocument();
  });

  it("selects only the server-bounded chaos scenarios and launches a confirmed isolated run", async () => {
    window.history.replaceState(null, "", "/chaos");
    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Chaos lab" })).toBeInTheDocument();
    const modelTimeout = await screen.findByRole("checkbox", { name: /model-timeout/ });
    const invalidOutput = screen.getByRole("checkbox", { name: /invalid-model-output/ });
    const toolTimeout = screen.getByRole("checkbox", { name: /tool-timeout/ });
    const crashRecovery = screen.getByRole("checkbox", { name: /agent-crash-recovery/ });
    await user.click(modelTimeout);
    await user.click(invalidOutput);
    await user.click(toolTimeout);
    expect(crashRecovery).toBeDisabled();
    await user.click(screen.getByRole("checkbox", { name: /I confirm this run uses/ }));
    await user.click(screen.getByRole("button", { name: "Launch controlled test" }));

    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/v1/chaos", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ confirm: true, scenarios: ["model-timeout", "invalid-model-output", "tool-timeout"] }),
    })));
    expect(await screen.findByRole("heading", { name: "Failure propagation & recovery" })).toBeInTheDocument();
    expect(screen.getByText("chaos-run-stage23-test")).toBeInTheDocument();
    expect(screen.getByText("Recovered")).toBeInTheDocument();
    expect(screen.getAllByText("Contained").length).toBeGreaterThan(0);
  });

  it("shows retained attack results, blocked actions, and the non-certification boundary", async () => {
    window.history.replaceState(null, "", "/security");
    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Security lab" })).toBeInTheDocument();
    expect(await screen.findByText("stage14-security-stage23-test")).toBeInTheDocument();
    expect(screen.getByText(/does not prove the system is secure/)).toBeInTheDocument();
    expect(screen.getAllByText("Defense held")).toHaveLength(4);
    expect(screen.getByText("network destination was denied")).toBeInTheDocument();
    expect(screen.getByText("security_blocked")).toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox", { name: "Category" }), "tool escalation");
    const table = screen.getByRole("table");
    expect(within(table).getByText("tool-escalation")).toBeInTheDocument();
    expect(within(table).queryByText("network-exfiltration")).not.toBeInTheDocument();
  });

  it("executes selected deterministic security cases through the confirmed API boundary", async () => {
    window.history.replaceState(null, "", "/security");
    const user = userEvent.setup();
    render(<App />);

    await screen.findByRole("button", { name: "Select all" });
    await user.click(screen.getByRole("button", { name: "Select all" }));
    await user.click(screen.getByRole("checkbox", { name: /I confirm this suite uses/ }));
    await user.click(screen.getByRole("button", { name: "Execute security suite" }));

    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/v1/security", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ confirm: true, cases: ["prompt-injection", "tool-escalation", "network-exfiltration", "secret-output"] }),
    })));
    expect(await screen.findByText("stage23-security-new-test")).toBeInTheDocument();
    expect(screen.getByText("Newly executed suite")).toBeInTheDocument();
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
    ["Traces", "/traces", "Trace explorer"],
    ["Hardware", "/hardware", "Hardware & performance lab"],
    ["Metrics", "/metrics", "Hardware & performance lab"],
    ["Chaos", "/chaos", "Chaos lab"],
    ["Security", "/security", "Security lab"],
  ])("has no automated accessibility violations in the %s workspace", async (_label, path, heading) => {
    window.history.replaceState(null, "", `${path}?task=${taskFixture.task_id}`);
    const { container } = render(<App />);
    await screen.findByRole("heading", { name: heading });
    if (path === "/chaos") await screen.findByText("model-timeout");
    else if (path === "/security") await screen.findByText("stage14-security-stage23-test");
    else await screen.findAllByText(taskFixture.task_id);
    let results: axe.AxeResults | undefined;

    await act(async () => {
      results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    });

    expect(results?.violations ?? []).toEqual([]);
  });
});
