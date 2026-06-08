export interface ProductBrief {
  product_name: string;
  category: string;
  specifications: string[];
  materials?: string[];
  selling_points: string[];
  target_market: string[];
  target_customer?: string[];
  usage_scenarios: string[];
  brand_style?: string;
  compliance_notes?: string[];
  audience_type?: string;
}

export interface GenerateRequest {
  project_id: number;
  brief: ProductBrief;
}

export interface VisualAssetPlan {
  project_id: number;
  main_image: Record<string, any>;
  white_bg: Record<string, any>;
  scene_images: Record<string, any>[];
  selling_points: Record<string, any>[];
  video_scripts: Record<string, any>[];
  ad_material: Record<string, any>;
}
