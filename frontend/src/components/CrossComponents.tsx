// @ts-nocheck
/**
 * Cross-cutting UI components — Loading / Error / Empty states (Phase 0.6).
 */
import React from 'react';

export function LoadingSpinner({ text = '加载中...' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="w-6 h-6 border-2 border-gray-700 border-t-gray-300 rounded-full animate-spin mb-2" />
      <p className="text-xs text-gray-500">{text}</p>
    </div>
  );
}

export function ErrorMessage({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="w-10 h-10 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mb-3">
        <span className="text-red-400 text-sm">!</span>
      </div>
      <p className="text-xs text-gray-400 text-center max-w-xs">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 px-3 py-1 text-xs text-gray-400 border border-gray-800 rounded hover:border-gray-600 transition-colors"
        >
          重试
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, description, action }: {
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="w-10 h-10 rounded-full bg-gray-900 border border-gray-800 flex items-center justify-center mb-3">
        <span className="text-gray-600 text-sm">—</span>
      </div>
      <p className="text-xs text-gray-400">{title}</p>
      {description && <p className="text-xs text-gray-600 mt-1">{description}</p>}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-3 px-3 py-1 text-xs text-gray-400 border border-gray-800 rounded hover:border-gray-600 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
