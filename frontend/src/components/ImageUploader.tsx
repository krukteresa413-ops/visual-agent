// ImageUploader component
import { useState, useRef } from 'react';
import api from '../api/client';

interface Img { filename: string; url: string; }
interface Props { images: Img[]; onChange: (i: Img[]) => void; max?: number; }

export default function ImageUploader({ images, onChange, max = 5 }: Props) {
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return;
    setUploading(true);
    try {
      const form = new FormData(); form.append('file', file);
      const { data } = await api.post('/api/v1/upload/image', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      onChange([...images, { filename: data.filename, url: data.url }]);
    } catch (err: any) { alert(err?.response?.data?.detail || '上传失败'); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ''; }
  };

  const remove = async (idx: number) => {
    const img = images[idx];
    try { await api.delete('/api/v1/upload/image/' + img.filename); } catch {}
    onChange(images.filter((_, i) => i !== idx));
  };

  return (
    <div>
      <label className="block text-xs font-medium text-gray-400 mb-1">产品图片 <span className="text-gray-600">（{images.length}/{max}）</span></label>
      {images.length > 0 && (
        <div className="flex gap-2 mb-2 flex-wrap">
          {images.map((img, i) => (
            <div key={i} className="relative w-16 h-16 rounded-lg overflow-hidden border border-gray-700">
              <img src={img.url} alt={img.filename} className="w-full h-full object-cover" />
              <button onClick={() => remove(i)} className="absolute inset-0 bg-black/60 text-white text-xs flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">删除</button>
            </div>
          ))}
        </div>
      )}
      {images.length < max && (
        <>
          <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={handleUpload} />
          <button onClick={() => fileRef.current?.click()} disabled={uploading} className="w-full py-2 border border-dashed border-gray-700 rounded-lg text-xs text-gray-400 hover:border-gray-400 hover:text-gray-200 transition-colors">
            {uploading ? '上传中...' : `点击上传 (${images.length}/${max})`}
          </button>
        </>
      )}
    </div>
  );
}
