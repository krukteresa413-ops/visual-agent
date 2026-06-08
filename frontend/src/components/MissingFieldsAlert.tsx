interface MissingField { field: string; level: 'required' | 'recommended'; hint: string; }

interface Props { fields: MissingField[]; onDismiss: () => void; }

const LABELS: Record<string, string> = {
  product_name: '产品名称', category: '品类', specifications: '规格参数',
  selling_points: '主要卖点', target_market: '目标市场', usage_scenarios: '使用场景',
  target_customer: '目标客户', materials: '材质', brand_style: '品牌风格',
  compliance_notes: '合规说明',
};

export default function MissingFieldsAlert({ fields, onDismiss }: Props) {
  if (!fields.length) return null;
  const required = fields.filter(f => f.level === 'required');
  const recommended = fields.filter(f => f.level === 'recommended');

  return (
    <div className="border border-yellow-800 bg-yellow-950/30 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-yellow-300">待补全信息</h4>
        <button onClick={onDismiss} className="text-xs text-gray-500 hover:text-gray-300">忽略</button>
      </div>
      {required.length > 0 && (
        <div>
          <p className="text-xs text-red-400 font-medium mb-1">必填项</p>
          {required.map(f => (
            <div key={f.field} className="text-xs text-gray-300 py-1 flex items-start gap-2">
              <span className="text-red-400 mt-0.5">•</span>
              <div><span className="font-medium">{LABELS[f.field] || f.field}</span><span className="text-gray-500 ml-2">{f.hint}</span></div>
            </div>
          ))}
        </div>
      )}
      {recommended.length > 0 && (
        <div>
          <p className="text-xs text-yellow-400 font-medium mb-1">推荐填写</p>
          {recommended.map(f => (
            <div key={f.field} className="text-xs text-gray-300 py-1 flex items-start gap-2">
              <span className="text-yellow-400 mt-0.5">•</span>
              <div><span className="font-medium">{LABELS[f.field] || f.field}</span><span className="text-gray-500 ml-2">{f.hint}</span></div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
