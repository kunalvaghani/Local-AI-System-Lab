import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { runtimeApi } from "../api/client";

const queryKeys = {
  health: ["runtime", "health"] as const,
  agents: ["runtime", "agents"] as const,
  scheduler: ["runtime", "scheduler"] as const,
  hardware: ["runtime", "hardware"] as const,
  models: ["runtime", "models"] as const,
  metrics: ["runtime", "metrics"] as const,
  task: (taskId: string) => ["runtime", "task", taskId] as const,
};

function useHealthQuery() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: ({ signal }) => runtimeApi.health(signal),
    refetchInterval: 3_000,
  });
}

function useAgentsQuery() {
  return useQuery({
    queryKey: queryKeys.agents,
    queryFn: ({ signal }) => runtimeApi.agents(signal),
    refetchInterval: 60_000,
  });
}

function useSchedulerQuery() {
  return useQuery({
    queryKey: queryKeys.scheduler,
    queryFn: ({ signal }) => runtimeApi.scheduler(signal),
    refetchInterval: 1_000,
  });
}

function useHardwareQuery() {
  return useQuery({
    queryKey: queryKeys.hardware,
    queryFn: ({ signal }) => runtimeApi.hardware(signal),
    refetchInterval: 5_000,
  });
}

function useModelsQuery() {
  return useQuery({
    queryKey: queryKeys.models,
    queryFn: ({ signal }) => runtimeApi.models(signal),
    refetchInterval: 60_000,
  });
}

function useMetricsQuery() {
  return useQuery({
    queryKey: queryKeys.metrics,
    queryFn: ({ signal }) => runtimeApi.metrics(signal),
    refetchInterval: 5_000,
  });
}

const terminalStatuses = new Set(["completed", "failed", "cancelled", "timed_out"]);

function useTaskQuery(taskId: string | null) {
  return useQuery({
    queryKey: queryKeys.task(taskId ?? "none"),
    queryFn: ({ signal }) => runtimeApi.task(taskId!, signal),
    enabled: taskId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && terminalStatuses.has(status) ? false : 1_000;
    },
  });
}

function useCreateTaskMutation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: runtimeApi.createTask,
    onSuccess: (task) => {
      client.setQueryData(queryKeys.task(task.task_id), task);
      void client.invalidateQueries({ queryKey: queryKeys.scheduler });
      void client.invalidateQueries({ queryKey: queryKeys.metrics });
    },
  });
}

function useCancelTaskMutation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: runtimeApi.cancelTask,
    onSuccess: (task) => {
      client.setQueryData(queryKeys.task(task.task_id), task);
      void client.invalidateQueries({ queryKey: queryKeys.scheduler });
      void client.invalidateQueries({ queryKey: queryKeys.metrics });
    },
  });
}

export {
  queryKeys,
  useAgentsQuery,
  useCancelTaskMutation,
  useCreateTaskMutation,
  useHardwareQuery,
  useHealthQuery,
  useMetricsQuery,
  useModelsQuery,
  useSchedulerQuery,
  useTaskQuery,
};
