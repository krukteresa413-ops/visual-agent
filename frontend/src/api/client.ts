/**
 * Typed API client — encapsulates all ~50 MOYAG endpoints (Phase 0.1).
 * Replace src/api/client.ts with this file.
 */
import axios from 'axios';
import type { AxiosInstance } from 'axios';

// ── Types ────────────────────────────────────────────────────────


export interface AuthUser {
  id: number;
  tenant_id: number;
  email: string | null;
  phone?: string | null;
  name: string;
  role: 'platform_admin' | 'tenant_admin' | 'member';
}

export interface AuthLoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  generation_count: number;
}

export interface DashboardData {
  total_projects: number;
  total_generations: number;
  projects_with_activity: number;
  recent_activity: Array<{
    id: number;
    project_name: string;
    model_used: string;
    created_at: string | null;
  }>;
  active_agents: string[];
}

export interface HistoryItem {
  id: number;
  project_name: string;
  model_used: string;
  generation_seconds: number | null;
  created_at: string | null;
  main_image_url: string | null;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface CampaignData {
  project_id: number;
  project_name: string;
  status: string;
  steps: Array<{
    step: string;
    label: string;
    status: string;
    progress: number;
    output?: Record<string, unknown> | null;
  }>;
  assets: Array<{
    type: string;
    label: string;
    url?: string;
    preview?: string;
    text?: string;
  }>;
}

export interface AssetLibrary {
  project_id: number;
  project_name: string;
  categories: Record<string, Array<{
    id: number;
    type: string;
    label: string;
    url?: string | null;
    preview?: string | null;
    text?: string | null;
    created_at?: string | null;
  }>>;
  total: number;
}

export interface GenerationProvider {
  name: string;
  display_name: string;
  description: string;
}

export interface GenerationRecord {
  id: number;
  model_used: string;
  generation_seconds: number;
  created_at: string;
}

export interface AsyncTask {
  task_id: string;
  status: 'processing' | 'complete' | 'error';
  parsed_brief?: Record<string, unknown>;
  generation?: Record<string, unknown>;
  error?: string;
}

// ── Client ────────────────────────────────────────────────────────

const client: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 600000, // 5 min for generation
});

// ── Auth interceptor (0.2 will enhance this) ──────────────────────

const TOKEN_KEY = 'moyag_token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

client.interceptors.request.use((cfg) => {
  const token = getToken();
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

client.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      clearToken();
      window.location.assign('/auth');
    }
    return Promise.reject(err);
  }
);

// ── API methods (grouped by domain) ───────────────────────────────

export const api = {
  auth: {
    login: (payload: { identifier?: string; email?: string; phone?: string; password: string }) =>
      client.post<AuthLoginResponse>('/auth/login', payload).then(r => r.data),
    register: (payload: { email?: string; phone?: string; password: string; name: string; tenant_name: string; role?: string }) =>
      client.post<AuthUser>('/auth/register', payload).then(r => r.data),
    me: () => client.get<AuthUser>('/auth/me').then(r => r.data),
  },

  // Library
  library: {
    brand: (tenantId?: number) =>
      client.get("/library/brand", { params: tenantId != null ? { tenant_id: tenantId } : {} }).then(r => r.data),
    products: (tenantId?: number) =>
      client.get("/library/products", { params: tenantId != null ? { tenant_id: tenantId } : {} }).then(r => r.data),
    product: (id: number) =>
      client.get(`/library/product/${id}`).then(r => r.data),
  },

  // Projects
  projects: {
    list: () => client.get<Project[]>('/projects/').then(r => r.data),
    create: (name: string, desc?: string) =>
      client.post<Project>('/projects/', { name, description: desc }).then(r => r.data),
    get: (id: number) => client.get<Project>(`/projects/${id}`).then(r => r.data),
    delete: (id: number) => client.delete(`/projects/${id}`).then(r => r.data),
    history: (id: number, limit = 20) =>
      client.get<GenerationRecord[]>(`/projects/${id}/history?limit=${limit}`).then(r => r.data),
  },

  // Dashboard
  dashboard: {
    get: () => client.get<DashboardData>('/dashboard/').then(r => r.data),
  },

  // History
  history: {
    list: (params: { page?: number; page_size?: number; project_id?: number } = {}) =>
      client.get<HistoryResponse>('/history/', { params }).then(r => r.data),
  },

  // Campaign
  campaign: {
    get: (projectId: number) =>
      client.get<CampaignData>(`/campaign/${projectId}`).then(r => r.data),
  },

  // Assets
  assets: {
    library: (projectId: number) =>
      client.get<AssetLibrary>('/assets/', { params: { project_id: projectId } }).then(r => r.data),
  },

  // Generation
  generation: {
    providers: () =>
      client.get<GenerationProvider[]>('/generation/providers').then(r => r.data),
    models: () =>
      client.get('/generation/models').then(r => r.data),
    catalog: () =>
      client.get('/models/catalog').then(r => r.data),
    skills: (category?: string) =>
      client.get('/skills' + (category ? '?category=' + encodeURIComponent(category) : '')).then(r => r.data),
    skillCategories: () =>
      client.get('/skills/categories').then(r => r.data),
    image: (params: { provider: string; prompt: string; width: number; height: number; model?: string; reference_image_url?: string }) =>
      client.post('/generation/image', params).then(r => r.data),
    generateAsync: (formData: FormData) =>
      client.post<AsyncTask>('/generate-async', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(r => r.data),
    quickGenerate: (params: { prompt: string; project_id?: number; prompt_template?: string; reference_image_url?: string; image_provider?: string; image_model?: string; auto_model?: boolean; agent_mode?: string; brief?: Record<string, unknown> }) =>
      client.post<AsyncTask>('/quick-generate', params).then(r => r.data),
    pollTask: (taskId: string) =>
      client.get<AsyncTask>(`/generation/task/${taskId}`).then(r => r.data),
    getDetail: (id: number) =>
      client.get(`/visual-tasks/generations/${id}`).then(r => r.data),
    generateVariants: (params: Record<string, unknown>) =>
      client.post('/visual-tasks/generate-variants', params).then(r => r.data),
    strategyPreview: (params: { brief: Record<string, unknown>; platform_id?: string }) =>
      client.post('/unified/strategy/preview', params).then(r => r.data),
  },

  // Video
  video: {
    providers: () =>
      client.get<GenerationProvider[]>('/video-providers').then(r => r.data),
    generate: (params: { provider: string; prompt: string; duration: number; width: number; height: number }) =>
      client.post('/video', params).then(r => r.data),
  },

  // Progress (SSE endpoint — consumed by useGenerationTask)
  progress: {
    streamUrl: (taskId: string) => `/api/v1/progress/${taskId}/stream`,
  },

  // Brief
  brief: {
    parse: (text: string) =>
      client.post<Record<string, unknown>>('/brief/parse', { text }).then(r => r.data),
    review: (brief: Record<string, unknown>) =>
      client.post('/brief/review', brief).then(r => r.data),
    save: (projectId: number, brief: Record<string, unknown>) =>
      client.post('/brief/save', { project_id: projectId, brief }).then(r => r.data),
    get: (projectId: number) =>
      client.get<{ brief: Record<string, unknown> | null }>(`/brief/project/${projectId}`).then(r => r.data),
  },

  // Brand
  brand: {
    extract: (params: Record<string, unknown>) =>
      client.post('/brand/extract', params).then(r => r.data),
    get: (projectId: number) =>
      client.get(`/brand/${projectId}`).then(r => r.data),
    create: (params: Record<string, unknown>) =>
      client.post('/brand/', params).then(r => r.data),
    // 多品牌库管理(/brand/manage/*)
    list: () =>
      client.get('/brand/manage/list').then(r => r.data),
    createManual: (params: Record<string, unknown>) =>
      client.post('/brand/manage/create', params).then(r => r.data),
    update: (id: number, params: Record<string, unknown>) =>
      client.patch(`/brand/manage/${id}`, params).then(r => r.data),
    remove: (id: number) =>
      client.delete(`/brand/manage/${id}`).then(r => r.data),
  },

  // Export
  export: {
    markdown: (projectId: number) =>
      client.get(`/visual-tasks/projects/${projectId}/export/markdown`, { responseType: 'blob' }),
    docx: (projectId: number) =>
      client.get(`/visual-tasks/projects/${projectId}/export/docx`, { responseType: 'blob' }),
  },

  // Upload
  upload: {
    image: (formData: FormData) =>
      client.post('/upload/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(r => r.data),
    documentParse: (formData: FormData) =>
      client.post('/upload/document/parse', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(r => r.data),
  },

  // Platform & Templates
  platform: {
    list: () => client.get('/platforms').then(r => r.data),
    get: (id: string) => client.get(`/platforms/${id}`).then(r => r.data),
    scenes: () => client.get('/scenes').then(r => r.data),
    scene: (id: string) => client.get(`/scenes/${id}`).then(r => r.data),
  },

  templates: {
    list: () => client.get('/visual-tasks/templates').then(r => r.data),
    byIndustry: (industry: string) =>
      client.get(`/visual-tasks/templates/${industry}`).then(r => r.data),
  },

  // Copywriting
  copywriting: {
    generate: (params: Record<string, unknown>) =>
      client.post('/copywriting/generate', params).then(r => r.data),
  },

  // Layout
  layout: {
    generate: (params: Record<string, unknown>) =>
      client.post('/layout/generate', params).then(r => r.data),
  },

  // Canvas (legacy)
  canvas: {
    get: (projectId: number) =>
      client.get(`/canvas/projects/${projectId}/canvas`).then(r => r.data),
  },

  // Canvas AI Actions
  canvasActions: {
    start: (payload: Record<string, unknown>) =>
      client.post('/canvas-actions', payload).then(r => r.data),
    poll: (taskId: string) =>
      client.get(`/canvas-actions/${taskId}`).then(r => r.data),
  },

  // Canvas right-click image actions
  canvasImageActions: {
    run: (payload: { project_id: number; asset_id: string; action: string; image_url: string; instruction?: string; provider?: string; model?: string }) =>
      client.post('/canvas/image-action', payload).then(r => r.data),
  },

  // Atelier Flow Infinite Canvas APIs
  atelierCanvas: {
    getState: (projectId: number) =>
      client.get(`/projects/${projectId}/canvas-state`).then(r => r.data),
    saveState: (projectId: number, payload: Record<string, unknown>) =>
      client.put(`/projects/${projectId}/canvas-state`, payload).then(r => r.data),
    getTimeline: (projectId: number) =>
      client.get(`/projects/${projectId}/timeline`).then(r => r.data),
    getAssets: (projectId: number, params?: Record<string, unknown>) =>
      client.get(`/projects/${projectId}/canvas-assets`, { params }).then(r => r.data),
  },

  // Font Generation APIs
  font: {
    generate: (formData: FormData) =>
      client.post('/font/generate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(r => r.data),
    list: (projectId: number) =>
      client.get(`/font/list/${projectId}`).then(r => r.data),
  },
};

// ── Download helper (blob → trigger download) ─────────────────────

export async function downloadFile(
  projectId: number,
  format: 'markdown' | 'docx'
): Promise<void> {
  const res = format === 'docx'
    ? await api.export.docx(projectId)
    : await api.export.markdown(projectId);
  const url = URL.createObjectURL(res.data);
  const a = document.createElement('a');
  a.href = url;
  a.download = `moyag_${projectId}.${format === 'docx' ? 'docx' : 'md'}`;
  a.click();
  URL.revokeObjectURL(url);
}

export default client;
// Backward compat: pages can still do `import api from '../api/client'`

// ── Backward compat shims (old named exports) ─────────────────────
// Remove these after all pages are migrated to api.xxx() syntax.
export const listProjects = api.projects.list;
export const createProject = api.projects.create;
export const deleteProject = api.projects.delete;
export const listGenerations = (pid: number) => api.projects.history(pid);
export const generateAll = (req: Record<string, unknown>) =>
  client.post('/visual-tasks/generate-all-fast', req).then(r => r.data);
export const exportMarkdown = (id: number) =>
  api.export.markdown(id).then(r => r.data);
export const saveBrief = api.brief.save;
export const getProjectBrief = api.brief.get;
export const parseBrief = api.brief.parse;
export const getGenerationDetail = api.generation.getDetail;

// Types — keep existing exports

// ── Video Edit Pipeline ──
export const videoEdit = {
  createProject: (name: string, description = '') => {
    const form = new URLSearchParams();
    form.append('name', name);
    form.append('description', description);
    return axios.post('/api/v1/video-edit/projects', form.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  createDemo: () => axios.post('/api/v1/video-edit/demo').then(r => r.data),
  uploadFiles: (projectId: string, files: File[]) => {
    const form = new FormData();
    files.forEach(f => form.append('files', f));
    return axios.post('/api/v1/video-edit/projects/' + projectId + '/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000,
    });
  },
  scanMedia: (projectId: string) =>
    axios.post('/api/v1/video-edit/projects/' + projectId + '/scan'),
  analyzeMedia: (projectId: string) =>
    axios.post('/api/v1/video-edit/projects/' + projectId + '/analyze', {}, { timeout: 120000 }),
  generateScript: (projectId: string, topic = '') => {
    const form = new URLSearchParams();
    if (topic) form.append('topic', topic);
    return axios.post('/api/v1/video-edit/projects/' + projectId + '/script', form.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      timeout: 180000,
    });
  },
  generateBlueprint: (projectId: string, structureIndex = 0) =>
    axios.post('/api/v1/video-edit/projects/' + projectId + '/blueprint?structure_index=' + structureIndex, {}, { timeout: 180000 }),
  getStatus: (projectId: string) =>
    axios.get('/api/v1/video-edit/projects/' + projectId + '/status'),
  getProject: (projectId: string) =>
    axios.get('/api/v1/video-edit/projects/' + projectId),
  getTimeline: (projectId: string) =>
    axios.get('/api/v1/video-edit/projects/' + projectId + '/timeline'),
  renderVideo: (projectId: string) =>
    axios.post('/api/v1/video-edit/projects/' + projectId + '/render', {}, { timeout: 300000 }),
};
