// DreamPark(山东梦源制冷)资料库种子数据 —— 以 2026 产品目录 PDF 为范例整理。
// 图片已落 ECS /uploads/dreampark/，前端按绝对路径引用(静态挂载,无需 /api/v1 前缀)。

export interface DPProduct {
  id: string;
  name_cn: string;
  name_en: string;
  category: string;
  model: string;
  temp: string;       // 温区
  size: string;       // 尺寸(mm)
  image: string;      // /uploads/dreampark/xxx.png
  features: string[]; // 卖点
}

export interface DPDraggable {
  id: string;
  label: string;
  image: string;
}

export const DP_BRAND = {
  name_cn: '梦源制冷',
  name_en: 'DreamPark',
  full_name: '山东梦源制冷有限公司',
  slogan: '专业商用制冷设备 · 研发制造销售一体 · OEM / ODM 定制',
  philosophy: '以质量拓展市场，以创新求发展',
  // 主色取自目录封面与产品主调(深蓝商务 + 制冷青)
  palette: ['#0E2A47', '#1E6FD9', '#00B8D4', '#0F172A', '#F8FAFC'],
  keywords: ['风冷无霜', '品牌压缩机', 'LED 节能', '商超冷链', 'OEM / ODM', '一站式制冷'],
  series: ['冷藏展示柜系列', '风幕柜系列', '商超冷柜系列', '不锈钢冷柜系列', '冷库工程系列'],
  certs: ['CCC', 'ISO9001', 'ISO14001', '2023 山东省高新技术企业'],
  // 用一张代表性产品图作品牌主视觉(无独立 logo 资产时的兜底)
  hero: '/uploads/dreampark/dp13.png',
};

export const DP_COMPANY = {
  name: '山东梦源制冷有限公司',
  name_en: 'Shandong Dreampark Refrigeration Co., Ltd.',
  intro:
    '山东梦源制冷有限公司是一家集制冷设备研发、制造、销售于一体的生产企业，同时是一家 OEM / ODM 企业。' +
    '公司位于滨州市兴福厨具产业园区，工业园总投资 1.3 亿，并与多座知名高校建立长期合作关系。',
  market:
    '产品分为五大系列：冷藏展示柜、风幕柜、商超冷柜、不锈钢冷柜与冷库工程，广泛应用于各大商超、生鲜市场、' +
    '肉菜市场、便利店、餐馆等商业场所；国内已发展 400 多家经销商及大型连锁客户，并远销海外。',
  highlights: [
    { icon: '🏭', title: '研发·制造·销售一体', desc: '工业园总投资 1.3 亿，中高级设计师一对一定制' },
    { icon: '🤝', title: 'OEM / ODM 定制', desc: '深耕超市冷柜结构与性能，按需开模定制' },
    { icon: '🌐', title: '400+ 经销商 · 远销海外', desc: '国内全国连锁客户 + 海外销售网络' },
    { icon: '✅', title: '权威认证', desc: 'CCC / ISO9001 / ISO14001 · 2023 高新技术企业' },
  ],
  gallery: [
    { id: 'co-team', label: 'Excellent Team 专业团队', image: '/uploads/dreampark/dp13.png' },
    { id: 'co-test', label: 'Strict Testing 严格测试', image: '/uploads/dreampark/dp17.png' },
  ] as DPDraggable[],
};

// 通用卖点(目录中各产品共有)
const F = {
  airCool: '风冷无霜，制冷快速均匀',
  comp: '品牌压缩机，低噪音，运行稳定',
  led: 'LED 节能灯管，高亮度，耗电量低',
  frame: '铝合金门框，坚固耐用',
  curtain: '透明夜帘，防尘防虫更节能',
  shelf: '加厚可调节层架',
  freshLed: 'LED 生鲜灯，高亮度，为商品增色',
  micro: '微孔式出风，冷气分布均匀',
  lowe: '高透 Low-E 防雾玻璃，商品高清展示',
  power: '立体循环制冷，冻力强劲',
  steel: '柜内不锈钢材质，耐腐蚀易清洁',
};

export const DP_PRODUCTS: DPProduct[] = [
  { id: 'dp-p07', name_cn: '经济款冷藏展示柜', name_en: 'Economy Supermarket Cooler', category: '冷藏展示柜系列',
    model: 'DP-LF-450', temp: '2~8℃', size: '600×600×1860', image: '/uploads/dreampark/dp07.png',
    features: [F.airCool, F.comp, F.led, F.frame] },
  { id: 'dp-p13', name_cn: '炫黑款立式展示柜', name_en: 'Dazzle Black Chiller', category: '冷藏展示柜系列',
    model: 'DP-DB-600', temp: '2~8℃', size: '1200×730×2000', image: '/uploads/dreampark/dp13.png',
    features: [F.airCool, F.comp, '炫黑灯箱框，更换广告更醒目', F.shelf] },
  { id: 'dp-p17', name_cn: '直角外机风幕柜', name_en: 'Right Angle Multideck Chiller', category: '风幕柜系列',
    model: 'DP-FM-2000', temp: '2~8℃', size: '2000×800×2000', image: '/uploads/dreampark/dp17.png',
    features: [F.airCool, F.comp, F.curtain, F.led] },
  { id: 'dp-p28', name_cn: '鲜肉展示柜', name_en: 'Fresh Meat Showcase', category: '鲜肉柜系列',
    model: 'DP-XR6-18', temp: '-3~3℃', size: '1875×1100×1200', image: '/uploads/dreampark/dp28.png',
    features: [F.airCool, F.freshLed, F.micro, F.steel] },
  { id: 'dp-p31', name_cn: '熟食展示柜', name_en: 'Deli Showcase', category: '熟食柜系列',
    model: 'DP-SS-1500', temp: '2~8℃', size: '1500×900×1250', image: '/uploads/dreampark/dp31.png',
    features: [F.airCool, F.freshLed, F.lowe, F.micro] },
  { id: 'dp-p35', name_cn: '卧式水果柜', name_en: 'Horizontal Fruit Showcase', category: '水果柜系列',
    model: 'DP-SG-1800', temp: '2~8℃', size: '1800×900×1150', image: '/uploads/dreampark/dp35.png',
    features: [F.airCool, F.comp, F.freshLed, F.curtain] },
  { id: 'dp-p36', name_cn: '组合岛柜 KLA', name_en: 'Combination Island Cabinet KLA', category: '岛柜系列',
    model: 'DP-KLA-25', temp: '-18~-22℃', size: '2500×1100×850', image: '/uploads/dreampark/dp36.png',
    features: [F.power, F.comp, F.led, F.lowe] },
  { id: 'dp-p42', name_cn: '卧式冷冻柜', name_en: 'Chest Freezer', category: '冷冻柜系列',
    model: 'DP-BD-508', temp: '-18~-24℃', size: '1880×680×845', image: '/uploads/dreampark/dp42.png',
    features: ['加厚发泡柜体，锁冷隔热', F.comp, '粉末喷涂钢板外壳，耐刮防锈', '微电脑智能控温'] },
  { id: 'dp-p46', name_cn: '厨房不锈钢冷柜', name_en: 'Kitchen Refrigerator / Freezer', category: '不锈钢冷柜系列',
    model: 'DP-70P-dr', temp: '-18~8℃', size: '1220×760×1980', image: '/uploads/dreampark/dp46.png',
    features: ['全不锈钢柜体，食品级易清洁', '双温双控，冷藏冷冻一柜搞定', F.comp, F.shelf] },
  { id: 'dp-p49', name_cn: '冰激凌展示柜', name_en: 'Ice Cream Freezer Showcase', category: '冰激凌柜系列',
    model: 'DP-ic-04-6', temp: '-18~-22℃', size: '1290×740×1264', image: '/uploads/dreampark/dp49.png',
    features: [F.power, F.lowe, F.led, '弧形玻璃，展示面更通透'] },
  { id: 'dp-p50', name_cn: '方形蛋糕柜', name_en: 'Square Cake Showcase', category: '蛋糕柜系列',
    model: 'DP-CK-12', temp: '2~8℃', size: '1200×700×1200', image: '/uploads/dreampark/dp50.png',
    features: [F.airCool, '三层高透展示，蛋糕甜品高清呈现', '内置加湿，保鲜不干裂', F.led] },
];

export const DP_CATEGORIES: string[] = Array.from(new Set(DP_PRODUCTS.map(p => p.category)));

// 销售 SOP —— 由目录卖点提炼的种子内容(可在面板内继续维护)
export const DP_SALES_SOP = {
  process: [
    { step: '1 · 需求确认', desc: '门店类型(商超/生鲜/便利店/餐饮)、陈列品类、温区、尺寸与电压' },
    { step: '2 · 选型推荐', desc: '按品类匹配系列:饮料→立式展示柜;生鲜→鲜肉/风幕柜;冷冻→岛柜/卧式柜' },
    { step: '3 · 报价签约', desc: '确认型号/数量/物流/质保;支持 OEM/ODM 定制开模' },
    { step: '4 · 交付售后', desc: '安装指导 + 压缩机质保 + 备件支持' },
  ],
  scripts: [
    { title: '开场(价值锚点)', text: '梦源制冷是研发制造销售一体的厂家,400+ 经销商、CCC/ISO 认证,商超冷链整店方案都能配。' },
    { title: '节能卖点', text: '全系风冷无霜 + 品牌压缩机 + LED 节能灯,长期电费比杂牌省一截,稳定运行更省心。' },
    { title: '定制卖点', text: '尺寸、温区、门型、灯箱广告都能按门店定制(OEM/ODM),不是只卖标准款。' },
  ],
  objections: [
    { q: '比杂牌贵', a: '算总账:品牌压缩机寿命与能耗优势,2~3 年省下的电费和维修就补回差价,且整店风格统一。' },
    { q: '担心售后', a: '压缩机质保 + 全国备件,经销商本地化响应;认证齐全,出口标准品控。' },
    { q: '怕尺寸不合', a: '提供按门店实测的定制开模,温区/尺寸/门型都可改,避免买回来摆不下。' },
  ],
};
