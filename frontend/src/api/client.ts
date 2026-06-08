import axios from 'axios';
import type { ProductBrief, GenerateRequest, VisualAssetPlan } from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  headers: { 'Content-Type': 'application/json' },
  timeout: 300000,
});

export type { ProductBrief, GenerateRequest, VisualAssetPlan };

export const generateAll = (req: GenerateRequest) =>
  api.post<VisualAssetPlan>('/api/v1/visual-tasks/generate-all-fast', req).then(r => r.data);

export const exportMarkdown = (projectId: number) =>
  api.get<{ markdown: string }>('/api/v1/visual-tasks/projects/' + projectId + '/export/markdown').then(r => r.data);

export default api;

export const parseBrief = (rawText: string) =>
  api.post<Record<string,any>>('/api/v1/brief/parse', { text: rawText }).then(r => r.data);

export interface Project { id: number; name: string; description?: string; created_at: string; generation_count: number; }
export interface GenerationRecord { id: number; model_used: string; generation_seconds: number; created_at: string; }
export const listProjects = () => api.get<Project[]>('/api/v1/projects/').then(r => r.data);
export const createProject = (name: string, desc?: string) => api.post<Project>('/api/v1/projects/', { name, description: desc }).then(r => r.data);
export const deleteProject = (id: number) => api.delete('/api/v1/projects/' + id).then(r => r.data);

export const getGenerationDetail = (id: number) =>
  api.get<{id:number;project_id:number;asset_plan:any;model_used:string}>('/api/v1/visual-tasks/generations/'+id).then(r=>r.data);

export const listGenerations = (pid: number) =>
  api.get<{id:number;model_used:string;generation_seconds:number;created_at:string}[]>('/api/v1/projects/'+pid+'/history').then(r=>r.data);

export const saveBrief = (pid: number, brief: any) => api.post('/api/v1/brief/save', { project_id: pid, brief }).then(r => r.data);
export const getProjectBrief = (pid: number) => api.get<{brief:any|null}>('/api/v1/brief/project/' + pid).then(r => r.data);
