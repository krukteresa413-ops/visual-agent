import { useState, useRef } from 'react';
import api from '../api/client';

interface Props { 
  onParsed: (brief: any, missing: any[], preview: string) => void;
  onUploadStart?: () => void;
  onUploadEnd?: () => void;
}

const ALLOWED = '.pdf,.doc,.docx,.xlsx,.xls,.pptx,.ppt,.txt,.csv';

export default function DocumentUploader({ onParsed, onUploadStart, onUploadEnd }: Props) {
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState('');
  const [error, setError] = useState('');
  const ref = useRef<HTMLInputElement>(null);

  const handle = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return;
    setFileName(file.name); setUploading(true); setError('');
    if (onUploadStart) onUploadStart();
    try {
      const form = new FormData(); form.append('file', file);
      const { data } = await api.post('/api/v1/upload/document/parse', form, {
        headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60000,
      });
      const { parsed_brief, extracted_text_preview } = data;
      const { missing_fields, ...brief } = parsed_brief;
      onParsed(brief, missing_fields || [], extracted_text_preview || '');
    } catch (err: any) { 
      setError(err?.response?.data?.detail || '解析失败');
      if (onUploadEnd) onUploadEnd();
    }
    finally { setUploading(false); if (ref.current) ref.current.value = ''; }
  };

  return (
    <div className="border border-gray-700 rounded-xl p-4 bg-gray-900/50">
      <h3 className="text-sm font-medium text-gray-300 mb-2">上传文档解析</h3>
      <p className="text-xs text-gray-500 mb-3">上传 PDF/Word/Excel/PPT，Agent 自动提取产品资料</p>
      <input ref={ref} type="file" accept={ALLOWED} className="hidden" onChange={handle} />
      <button onClick={() => ref.current?.click()} disabled={uploading}
        className={`w-full py-3 border border-dashed rounded-lg text-sm transition-all ${uploading ? 'border-orange-500 bg-orange-950/20 text-orange-300' : 'border-gray-600 text-gray-400 hover:border-gray-400 hover:text-gray-200'}`}>
        {uploading ? (<span className="flex items-center justify-center gap-2">⏳ 解析 {fileName}...</span>) : '上传 PDF/Word/Excel/PPT'}
      </button>
      {error && <p className="mt-2 text-red-400 text-xs bg-red-950 p-2 rounded-lg">{error}</p>}
    </div>
  );
}
