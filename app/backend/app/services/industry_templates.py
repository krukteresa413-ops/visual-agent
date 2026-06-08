INDUSTRY_TEMPLATES = {
    'machinery': {'name':'机械/工业设备','name_en':'Machinery','visual_style':'硬朗、金属质感','color_palette':['#1a1a2e','#16213e','#0f3460','#e94560'],'scene_suggestions':['工厂车间','实验室','仓库'],'photo_style':'45度角、专业打光','copywriting_tone':'专业可靠','forbidden':['弱','软','可爱'],'prompt_modifiers':'industrial photography, metallic texture, professional lighting'},
    'home_living': {'name':'家居/生活','name_en':'Home & Living','visual_style':'温暖、自然','color_palette':['#f5f0e8','#d4c5a9','#8d7b68','#3c2a21'],'scene_suggestions':['客厅','卧室','厨房'],'photo_style':'自然光线、生活方式','copywriting_tone':'温馨亲切','forbidden':['冰冷','工业感','粗糙'],'prompt_modifiers':'cozy home interior, natural lighting, lifestyle photography'},
    'fashion': {'name':'时尚/配饰','name_en':'Fashion','visual_style':'高级、简约','color_palette':['#000000','#ffffff','#c9b99a','#8b7355'],'scene_suggestions':['模特展示','街拍','白底'],'photo_style':'时尚摄影、编辑风格','copywriting_tone':'时尚感','forbidden':['俗气','低端','粗糙'],'prompt_modifiers':'fashion photography, editorial style, minimalist background'},
    'beauty': {'name':'美妆/个护','name_en':'Beauty','visual_style':'清新、柔和','color_palette':['#fce4ec','#f8bbd0','#e1bee7','#ce93d8'],'scene_suggestions':['化妆台','浴室','自然光'],'photo_style':'柔焦、高光','copywriting_tone':'温柔精致','forbidden':['暗沉','粗糙','工业'],'prompt_modifiers':'beauty product photography, soft focus, pastel background'},
    'pet': {'name':'宠物用品','name_en':'Pet Supplies','visual_style':'活泼、温暖','color_palette':['#fff3e0','#ffe0b2','#ffcc02','#4caf50'],'scene_suggestions':['公园','家中','宠物店'],'photo_style':'自然光、动态捕捉','copywriting_tone':'活泼可爱','forbidden':['冷漠','危险','伤害'],'prompt_modifiers':'pet photography, happy animals, warm lighting, lifestyle'},
    'food': {'name':'食品/餐饮设备','name_en':'Food & Beverage','visual_style':'干净、专业','color_palette':['#ffffff','#f44336','#ff9800','#4caf50'],'scene_suggestions':['商用厨房','餐厅','食品工厂'],'photo_style':'专业灯光+微距','copywriting_tone':'专业卫生','forbidden':['脏乱','拥挤'],'prompt_modifiers':'commercial kitchen photography, stainless steel, food-safe, clean'},
    'outdoor': {'name':'户外/运动','name_en':'Outdoor','visual_style':'动感、自然','color_palette':['#1b5e20','#ff6f00','#0d47a1','#212121'],'scene_suggestions':['山地','海滩','城市'],'photo_style':'动作摄影、自然光','copywriting_tone':'活力运动','forbidden':['室内','静态','脆弱'],'prompt_modifiers':'outdoor adventure photography, natural landscape, action shot'},
    'electronics': {'name':'电子/3C','name_en':'Electronics','visual_style':'科技感、未来感','color_palette':['#0a0a0a','#1a237e','#00bcd4','#ffffff'],'scene_suggestions':['展示台','办公室','家庭'],'photo_style':'暗色背景+霓虹光','copywriting_tone':'科技专业','forbidden':['老式','模糊','杂光'],'prompt_modifiers':'tech product photography, dark background, neon glow, cinematic'},
}

def get_template(industry: str) -> dict:
    return INDUSTRY_TEMPLATES.get(industry, {})

def list_templates() -> list:
    return [{'key': k, 'name': v['name'], 'name_en': v['name_en']} for k, v in INDUSTRY_TEMPLATES.items()]

def template_to_prompt_context(industry: str) -> str:
    t = INDUSTRY_TEMPLATES.get(industry)
    if not t: return ''
    return f"""行业风格: {t['name']}
视觉风格: {t['visual_style']}
配色: {', '.join(t['color_palette'])}
场景建议: {', '.join(t['scene_suggestions'])}
摄影风格: {t['photo_style']}
文案语调: {t['copywriting_tone']}
禁止元素: {', '.join(t['forbidden'])}
Prompt修饰: {t['prompt_modifiers']}"""
