import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface QueryRequest {
  text?: string;
  image?: string; // base64 encoded
  top_k?: number;
  image_weight?: number;
  text_weight?: number;
  fusion_method?: string;
  category_filter?: string;
  price_min?: number;
  price_max?: number;
  enable_reranking?: boolean;
  // Advanced features for occasion/mood-aware and sentiment-based search
  occasion?: string;
  mood?: string;
  enable_sentiment_scoring?: boolean;
  enable_occasion_ranking?: boolean;
}

export interface SentimentInfo {
  aesthetic_score: number;
  emotion_category: string;
  color_harmony: number;
  brightness_score: number;
  warmth_score: number;
}

export interface OccasionInfo {
  occasion_score: number;
  matched_occasion?: string;
  matched_mood?: string;
  boost_applied: number;
}

export interface ProductResult {
  product_id: string;
  title: string;
  image_url: string;
  similarity_score: number;
  price?: number;
  category?: string;
  description?: string;
  // Advanced features
  sentiment?: SentimentInfo;
  occasion?: OccasionInfo;
}

export interface QueryResponse {
  results: ProductResult[];
  query_time: number;
  total_products: number;
  query_info?: {
    has_text: boolean;
    has_image: boolean;
    fusion_method?: string;
  };
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async searchProducts(request: QueryRequest): Promise<QueryResponse> {
    try {
      const response = await axios.post(`${this.baseURL}/search/workflow`, request);
      return response.data;
    } catch (error) {
      console.error('Error searching products:', error);
      throw new Error('Failed to search products');
    }
  }

  async hybridSearch(formData: FormData): Promise<QueryResponse> {
    try {
      const response = await axios.post(`${this.baseURL}/search/workflow-multipart`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error in hybrid search:', error);
      throw new Error('Failed to perform hybrid search');
    }
  }

  async uploadAndSearch(file: File, options?: Partial<QueryRequest>): Promise<QueryResponse> {
    try {
      const formData = new FormData();
      formData.append('image', file);  // Changed from 'image_file' to 'image'
      
      if (options?.top_k) formData.append('top_k', options.top_k.toString());
      if (options?.text) formData.append('text', options.text);
      if (options?.text_weight !== undefined) formData.append('text_weight', options.text_weight.toString());
      if (options?.image_weight !== undefined) formData.append('image_weight', options.image_weight.toString());
      if (options?.fusion_method) formData.append('fusion_method', options.fusion_method);
      if (options?.category_filter) formData.append('category_filter', options.category_filter);
      if (options?.enable_reranking !== undefined) formData.append('enable_reranking', options.enable_reranking.toString());
      
      const response = await axios.post(`${this.baseURL}/search/workflow-multipart`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data;
    } catch (error) {
      console.error('Error uploading and searching:', error);
      throw new Error('Failed to upload and search');
    }
  }

  async getProduct(productId: string): Promise<ProductResult | null> {
    try {
      // Try to fetch from search results - this is a workaround since there's no dedicated product endpoint
      const response = await axios.post(`${this.baseURL}/search/workflow`, {
        text: productId,
        top_k: 1
      });
      
      if (response.data.results && response.data.results.length > 0) {
        return response.data.results[0];
      }
      return null;
    } catch (error) {
      console.error('Error getting product:', error);
      return null;
    }
  }

  async getSimilarProducts(productId: string, top_k: number = 10): Promise<ProductResult[]> {
    try {
      const response = await axios.post(`${this.baseURL}/search/workflow`, {
        text: productId,
        top_k,
        enable_reranking: true
      });
      
      return response.data.results || [];
    } catch (error) {
      console.error('Error getting similar products:', error);
      return [];
    }
  }

  async getIndexStatus() {
    try {
      const response = await axios.get(`${this.baseURL}/index/status`);
      return response.data;
    } catch (error) {
      console.error('Error getting index status:', error);
      return { status: 'error', total_products: 0 };
    }
  }

  // ===== E-COMMERCE API METHODS =====

  async getEcommerceSources() {
    try {
      const response = await axios.get(`${this.baseURL}/ecommerce/sources`);
      return response.data.sources;
    } catch (error) {
      console.error('Error fetching e-commerce sources:', error);
      return [];
    }
  }

  async fetchEcommerceProducts(
    query: string,
    sources?: string[],
    maxResultsPerSource: number = 20
  ): Promise<any> {
    try {
      const params = new URLSearchParams();
      params.append('query', query);
      params.append('max_results_per_source', maxResultsPerSource.toString());
      
      if (sources && sources.length > 0) {
        sources.forEach(source => params.append('sources', source));
      }
      
      const response = await axios.post(
        `${this.baseURL}/ecommerce/fetch?${params.toString()}`,
        {}
      );
      
      return response.data;
    } catch (error) {
      console.error('Error fetching from e-commerce APIs:', error);
      throw new Error('Failed to fetch products from e-commerce APIs');
    }
  }

  async searchAndEmbedProducts(
    query: string,
    sources?: string[],
    maxResults: number = 15
  ): Promise<any> {
    try {
      const params = new URLSearchParams();
      params.append('query', query);
      params.append('max_results', maxResults.toString());
      
      if (sources && sources.length > 0) {
        sources.forEach(source => params.append('sources', source));
      }
      
      const response = await axios.post(
        `${this.baseURL}/ecommerce/search-and-embed?${params.toString()}`,
        {}
      );
      
      return response.data;
    } catch (error) {
      console.error('Error in search and embed:', error);
      throw new Error('Failed to search and embed products');
    }
  }

  async getEcommerceStatus(): Promise<any> {
    try {
      const response = await axios.get(`${this.baseURL}/ecommerce/status`);
      return response.data;
    } catch (error) {
      console.error('Error getting e-commerce status:', error);
      return { ecommerce_integration: 'unknown' };
    }
  }
}

export const apiClient = new ApiClient();