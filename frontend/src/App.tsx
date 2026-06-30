import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ProjectsPage from './pages/ProjectsPage';
import GeneratePage from './pages/GeneratePage';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import ErrorBoundary from './components/ErrorBoundary';
import { ToastContainer } from "./components/Toast";
import CampaignPage from './pages/CampaignPage';
import PromptLibrary from './pages/PromptLibrary';
import VideoEditPage from './pages/VideoEditPage';
import InspirationPage from './pages/InspirationPage';
import BrandPage from './pages/BrandPage';
import ProjectsLibraryPage from './pages/ProjectsLibraryPage';
import BrandLibraryPage from './pages/BrandLibraryPage';
import ProfilePage from './pages/ProfilePage';
import CopywritingPage from './pages/CopywritingPage';
import NewProjectPage from './pages/NewProjectPage';
import Layout from './components/Layout';
import { RequireAuth } from './components/RequireAuth';
import { lazy, Suspense } from 'react';
// Excalidraw 小样(spike):独立懒加载路由,不影响主包体积/现有画布
const ExcaliCanvas = lazy(() => import('./components/canvas/ExcaliCanvas'));
const queryClient = new QueryClient();
export default function App() {
  return <><ToastContainer /><ErrorBoundary><QueryClientProvider client={queryClient}><BrowserRouter><Layout><Routes>
    <Route path='/' element={<RequireAuth><ProjectsPage /></RequireAuth>} />
    <Route path='/generate/:projectId' element={<RequireAuth><GeneratePage /></RequireAuth>} />
    <Route path='/auth' element={<AuthPage />} />
    <Route path='/dashboard' element={<RequireAuth><DashboardPage /></RequireAuth>} />
    <Route path='/history' element={<RequireAuth><HistoryPage /></RequireAuth>} />
    <Route path='/video-edit' element={<RequireAuth><VideoEditPage /></RequireAuth>} />
    <Route path='/prompts' element={<RequireAuth><PromptLibrary /></RequireAuth>} />
    <Route path='/inspiration' element={<RequireAuth><InspirationPage /></RequireAuth>} />
    <Route path='/projects' element={<RequireAuth><ProjectsLibraryPage /></RequireAuth>} />
    <Route path='/brands' element={<RequireAuth><BrandLibraryPage /></RequireAuth>} />
    <Route path='/profile' element={<RequireAuth><ProfilePage /></RequireAuth>} />
    <Route path='/copywriting' element={<RequireAuth><CopywritingPage /></RequireAuth>} />
    <Route path='/new' element={<RequireAuth><NewProjectPage /></RequireAuth>} />
    <Route path='/brand/:projectId' element={<RequireAuth><BrandPage /></RequireAuth>} />
    <Route path='/excali/:projectId' element={<RequireAuth><Suspense fallback={<div className='grid h-screen place-items-center text-gray-400'>加载 Excalidraw 画布…</div>}><ExcaliCanvas /></Suspense></RequireAuth>} />
    <Route path='*' element={<Navigate to='/' replace />} />
    <Route path='/campaign/:projectId' element={<RequireAuth><CampaignPage /></RequireAuth>} />
  </Routes></Layout></BrowserRouter></QueryClientProvider></ErrorBoundary></>;
}
