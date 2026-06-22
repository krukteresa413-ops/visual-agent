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
import Layout from './components/Layout';
import { RequireAuth } from './components/RequireAuth';
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
    <Route path='/brand/:projectId' element={<RequireAuth><BrandPage /></RequireAuth>} />
    <Route path='*' element={<Navigate to='/' replace />} />
    <Route path='/campaign/:projectId' element={<RequireAuth><CampaignPage /></RequireAuth>} />
  </Routes></Layout></BrowserRouter></QueryClientProvider></ErrorBoundary></>;
}
