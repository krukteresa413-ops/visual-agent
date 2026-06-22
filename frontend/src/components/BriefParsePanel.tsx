// @ts-nocheck
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { parseBrief } from '../api/client';
import type { ProductBrief } from '../types';

interface Props { onParsed: (brief: ProductBrief, missing: any[]) => void; }

export default function BriefParsePanel({ onParsed }: Props) {
  const [rawText, setRawText] = useState('');
  const parseMutation = useMutation({
    mutationFn: () => parseBrief(rawText),
    onSuccess: (data) => {
      const { missing_fields, ...brief } = data;
      onParsed(brief as ProductBrief, missing_fields || []);
    },
  });
  const canSubmit = rawText.trim() && !parseMutation.isPending;
  return (
    <div className="border border-gray-700 rounded-xl p-4 bg-gray-900/50">
      <h3 className="text-sm font-medium text-gray-300 mb-2">智能解析</h3>
      <p className="text-xs text-gray-500 mb-3">粘贴产品描述文本，Agent 自动提取结构化产品资料</p>
      <textarea className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-600 resize-none" rows={6}
        placeholder={"Commercial Chest Freezer, capacity 300L, stainless steel body..."}
        value={rawText} onChange={(e) => setRawText(e.target.value)} />
      <button onClick={() => parseMutation.mutate()} disabled={!canSubmit}
        className={canSubmit ? "mt-3 w-full py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white" : "mt-3 w-full py-2 rounded-lg text-sm font-medium bg-gray-800 text-gray-500 cursor-not-allowed"}>
        {parseMutation.isPending ? '解析中...' : 'AI 智能解析'}
      </button>
      {parseMutation.isError && <p className="mt-2 text-red-400 text-xs bg-red-950 p-2 rounded-lg">{(parseMutation.error as any)?.message}</p>}
    </div>
  );
}
