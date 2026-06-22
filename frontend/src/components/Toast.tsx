import { useState, useEffect } from 'react';

type ToastType = 'error' | 'success' | 'info';

interface ToastState {
  message: string;
  type: ToastType;
  visible: boolean;
}

let toastFn: ((msg: string, type?: ToastType) => void) | null = null;

export function toast(msg: string, type: ToastType = 'error') {
  toastFn?.(msg, type);
}

export function ToastContainer() {
  const [state, setState] = useState<ToastState>({ message: '', type: 'error', visible: false });

  useEffect(() => {
    toastFn = (msg, type = 'error') => {
      setState({ message: msg, type, visible: true });
      setTimeout(() => setState(s => ({ ...s, visible: false })), 3000);
    };
    return () => { toastFn = null; };
  }, []);

  if (!state.visible) return null;

  const colors = {
    error: 'bg-red-500/90',
    success: 'bg-green-500/90',
    info: 'bg-blue-500/90',
  };

  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] animate-in fade-in slide-in-from-top-2">
      <div className={`${colors[state.type]} text-white px-6 py-3 rounded-xl shadow-2xl backdrop-blur-md text-sm font-medium`}>
        {state.message}
      </div>
    </div>
  );
}
