// @ts-nocheck
import { useParams } from 'react-router-dom';
import BrandKitPanel from '../components/BrandKitPanel';
import Layout from '../components/Layout';

export default function BrandPage() {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <div className="liquid-page min-h-screen p-8">
      <a href="/" className="text-gray-400 hover:text-gray-200 text-sm mb-4 inline-block transition-colors">← 返回首页</a>
      <BrandKitPanel
        projectId={Number(projectId) || 0}
        hasUploadedPdf={false}
        onClose={() => window.history.back()}
      />
    </div>
  );
}
