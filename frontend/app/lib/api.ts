import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface QueryRequest {
  text?: string;
  image?: string; // base64 encoded
  top_k?: number;
  image_weight?: number;
  text_weight?: number;
  // Advanced features for occasion/mood-aware and sentiment-based search
  occasion?: string;
  mood?: string;
  season?: string;
  time_of_day?: string;
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
  // Advanced features
  sentiment?: SentimentInfo;
  occasion?: OccasionInfo;
}

export interface QueryResponse {
  results: ProductResult[];
  query_time: number;
  total_products: number;
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async searchProducts(request: QueryRequest): Promise<QueryResponse> {
    try {
      const response = await axios.post(`${this.baseURL}/query`, request);
      return response.data;
    } catch (error) {
      console.error('Error searching products:', error);
      throw new Error('Failed to search products');
    }
  }

  async uploadImage(file: File): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${this.baseURL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data.image_base64;
    } catch (error) {
      console.error('Error uploading image:', error);
      throw new Error('Failed to upload image');
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
}

export const apiClient = new ApiClient();