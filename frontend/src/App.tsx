import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ProjectsPage from './pages/ProjectsPage';
import GeneratePage from './pages/GeneratePage';
const queryClient = new QueryClient();
export default function App() {
  return <QueryClientProvider client={queryClient}><BrowserRouter><Routes>
    <Route path='/' element={<ProjectsPage />} />
    <Route path='/generate/:projectId' element={<GeneratePage />} />
    <Route path='*' element={<Navigate to='/' replace />} />
  </Routes></BrowserRouter></QueryClientProvider>;
}
