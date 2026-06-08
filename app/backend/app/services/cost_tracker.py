import threading
from dataclasses import dataclass, field

@dataclass
class GenerationCostReport:
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    breakdown: list = field(default_factory=list)

class CostTracker:
    PRICE_PER_INPUT_1K = 0.0001
    PRICE_PER_OUTPUT_1K = 0.0002

    def __init__(self):
        self._lock = threading.Lock()
        self._calls = []

    def record_call(self, task_type: str, input_tokens: int = 0, output_tokens: int = 0, model: str = 'deepseek-chat'):
        with self._lock:
            self._calls.append({'task_type':task_type,'input_tokens':input_tokens,'output_tokens':output_tokens,'model':model})

    def report(self) -> GenerationCostReport:
        with self._lock:
            ti = sum(c['input_tokens'] for c in self._calls)
            to = sum(c['output_tokens'] for c in self._calls)
            cost = ti/1000*self.PRICE_PER_INPUT_1K + to/1000*self.PRICE_PER_OUTPUT_1K
            return GenerationCostReport(total_calls=len(self._calls),total_input_tokens=ti,total_output_tokens=to,estimated_cost_usd=round(cost,6),breakdown=list(self._calls))

    def reset(self):
        with self._lock: self._calls.clear()
