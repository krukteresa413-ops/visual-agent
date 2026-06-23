import { useState, useEffect, useCallback } from 'react';

interface ToastItem {
  id: number;
  message: string;
  type: 'success' | 'error';
}

let toastId = 0;
let addToastFn: ((msg: string, type?: 'success' | 'error') => void) | null = null;

export function toast(message: string, type: 'success' | 'error' = 'success') {
  addToastFn?.(message, type);
}

export default function Toast() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const addToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    const id = ++toastId;
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000);
  }, []);

  useEffect(() => {
    addToastFn = addToast;
    return () => { addToastFn = null; };
  }, [addToast]);

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map(t => (
        <div
          key={t.id}
          className={`px-4 py-2.5 rounded-xl text-sm font-medium shadow-lg animate-fadeIn ${
            t.type === 'error'
              ? 'bg-red-500 text-white'
              : 'bg-[#333] text-white'
          }`}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}
