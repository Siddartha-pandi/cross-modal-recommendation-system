// AI Search Configuration
export const AI_SEARCH_CONFIG = {
  topK: 20,
  imageWeight: 0.5,
  textWeight: 0.5,
  fusionMethod: 'weighted_avg' as const,
  enableReranking: true,
  rerankingMethod: 'cross_attention' as const,
  diversityWeight: 0.1,
};

// Product Categories - Fashion Products Only
export const PRODUCT_CATEGORIES = [
  "Women's Clothing",
  "Men's Clothing",
  "Kids' Clothing",
  'Shoes & Footwear',
  'Bags & Handbags',
  'Jewelry & Watches',
  'Activewear & Sportswear',
  'Outerwear & Jackets',
  'Dresses & Skirts',
  'Tops & T-Shirts',
  'Pants & Jeans',
  'Accessories & Scarves',
];
