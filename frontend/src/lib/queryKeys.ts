/**
 * TanStack Query keys convention — single source of truth for cache keys (Phase 0.3).
 * Import from here everywhere, never hardcode queryKey strings.
 */

export const queryKeys = {
  projects: ['projects'] as const,
  project: (id: number) => ['project', id] as const,
  dashboard: ['dashboard'] as const,
  history: (filter: { page?: number; page_size?: number; project_id?: number }) =>
    ['history', filter] as const,
  campaign: (projectId: number) => ['campaign', projectId] as const,
  assets: (projectId: number) => ['assets', projectId] as const,
  generationProviders: ['generation', 'providers'] as const,
  videoProviders: ['video', 'providers'] as const,
  brief: (projectId: number) => ['brief', projectId] as const,
  brand: (projectId: number) => ['brand', projectId] as const,
  platforms: ['platforms'] as const,
  scenes: ['scenes'] as const,
  templates: ['templates'] as const,
  templatesByIndustry: (industry: string) => ['templates', industry] as const,
  canvas: (projectId: number) => ['canvas', projectId] as const,
  task: (taskId: string) => ['task', taskId] as const,
} as const;

/**
 * Invalidation helper: after a generation completes, flush all affected caches.
 * Call this in onSuccess of any generation mutation.
 */
export function invalidateAfterGeneration(
  qc: { invalidateQueries: (opts: { queryKey: readonly unknown[] }) => void },
  projectId: number
) {
  qc.invalidateQueries({ queryKey: queryKeys.dashboard });
  qc.invalidateQueries({ queryKey: queryKeys.history({}) });
  qc.invalidateQueries({ queryKey: queryKeys.campaign(projectId) });
  qc.invalidateQueries({ queryKey: queryKeys.assets(projectId) });
}
