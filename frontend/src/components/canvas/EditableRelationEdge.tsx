import { useState } from 'react';
import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from '@xyflow/react';

type EditableRelationData = {
  label?: string;
  relation_type?: string;
  instruction?: string;
  onLabelCommit?: (edgeId: string, label: string) => void;
};

export default function EditableRelationEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  label,
  data,
}: EdgeProps) {
  const relationData = (data || {}) as EditableRelationData;
  const initialLabel = String(relationData.label || label || relationData.instruction || relationData.relation_type || 'variant_of');
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(initialLabel);
  const [edgePath, labelX, labelY] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });

  const commit = () => {
    const nextLabel = draft.trim() || initialLabel;
    setDraft(nextLabel);
    setEditing(false);
    relationData.onLabelCommit?.(id, nextLabel);
  };

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} className="stroke-orange-300" />
      <EdgeLabelRenderer>
        <div
          data-editable-relation-edge
          className="nodrag nopan pointer-events-auto absolute max-w-[260px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-orange-200 bg-white/95 px-2 py-1 text-[10px] text-orange-700 shadow-sm backdrop-blur"
          style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)` }}
          title={draft}
          onDoubleClick={() => setEditing(true)}
        >
          {editing ? (
            <input
              data-relation-label-input
              value={draft}
              autoFocus
              onChange={(event) => setDraft(event.target.value)}
              onBlur={commit}
              onKeyDown={(event) => {
                if (event.key === 'Enter') commit();
                if (event.key === 'Escape') setEditing(false);
              }}
              className="w-56 rounded border border-orange-200 px-1 py-0.5 text-[10px] outline-none"
            />
          ) : (
            <button type="button" onClick={() => setEditing(true)} className="block max-w-[240px] truncate">
              {draft}
            </button>
          )}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
