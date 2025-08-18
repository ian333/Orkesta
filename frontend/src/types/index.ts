// API Response Types
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

// User & Auth Types
export interface User {
  id: string;
  email: string;
  tenantId: string;
  role: 'admin' | 'agent' | 'manager';
  name: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Orkesta Business Types
export interface Product {
  product_id: string;
  sku: string;
  name: string;
  aliases: string[];
  brand: string;
  unit: string;
  pricing: {
    lists: Record<string, Record<string, number>>;
    overrides: any[];
  };
  description?: string;
  category?: string;
}

export interface Client {
  client_id: string;
  name: string;
  email?: string;
  phone?: string;
  company?: string;
  pricing_list: string;
  payment_terms: number;
  credit_limit: number;
  active: boolean;
}

export interface Order {
  order_id: string;
  client_id: string;
  status: 'draft' | 'quoted' | 'confirmed' | 'processing' | 'completed' | 'cancelled';
  items: OrderItem[];
  total_amount: number;
  currency: string;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  product_id: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  sku: string;
  name: string;
}

// Conversation Types
export interface Conversation {
  conversation_id: string;
  client_phone: string;
  stage: 'greeting' | 'discovery' | 'quote' | 'closing' | 'completed';
  intent: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  health_score: number;
  messages: ConversationMessage[];
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: string;
  sender: 'user' | 'agent';
  message: string;
  timestamp: string;
  metadata?: any;
}

// Dashboard Metrics Types
export interface DashboardMetrics {
  overview: {
    total_revenue: number;
    total_orders: number;
    active_conversations: number;
    conversion_rate: number;
  };
  agents: {
    total_suggestions: number;
    approved_suggestions: number;
    confidence_avg: number;
    response_time_avg: number;
  };
  stripe: {
    total_processed: number;
    fees_collected: number;
    active_accounts: number;
    payout_pending: number;
  };
}

// Navigation Types
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  Login: undefined;
  Dashboard: undefined;
  Catalog: undefined;
  ProductDetail: { productId: string };
  Orders: undefined;
  OrderDetail: { orderId: string };
  Conversations: undefined;
  ConversationDetail: { conversationId: string };
  Settings: undefined;
  Profile: undefined;
};