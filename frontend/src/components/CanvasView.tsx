import CanvasFlow from './CanvasFlow';
import CanvasViewLegacy from './CanvasViewLegacy';

const useFlowCanvas = import.meta.env.VITE_ENABLE_FLOW_CANVAS === 'true';

export default function CanvasView(props: React.ComponentProps<typeof CanvasViewLegacy>) {
  return useFlowCanvas ? <CanvasFlow {...props} /> : <CanvasViewLegacy {...props} />;
}
