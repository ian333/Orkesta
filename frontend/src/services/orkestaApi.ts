import apiService from './api';
import { API_ENDPOINTS } from '../constants/api';
import { 
  Product, 
  Client, 
  Order, 
  Conversation, 
  DashboardMetrics,
  ApiResponse 
} from '../types';

class OrkestaApiService {
  // Context API (Shared Brain)
  async getProducts(searchQuery?: string): Promise<Product[]> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    if (searchQuery) {
      const response = await apiService.get<ApiResponse<Product[]>>(
        API_ENDPOINTS.PRODUCT_SEARCH(tenantId) + `?q=${encodeURIComponent(searchQuery)}`
      );
      return response.data;
    }

    const response = await apiService.get<ApiResponse<Product[]>>(
      API_ENDPOINTS.PRODUCTS(tenantId)
    );
    return response.data;
  }

  async addProduct(product: Omit<Product, 'product_id'>): Promise<Product> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.post<ApiResponse<Product>>(
      API_ENDPOINTS.PRODUCTS(tenantId),
      product
    );
    return response.data;
  }

  async getClients(): Promise<Client[]> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.get<ApiResponse<Client[]>>(
      API_ENDPOINTS.CLIENTS(tenantId)
    );
    return response.data;
  }

  async addClient(client: Omit<Client, 'client_id'>): Promise<Client> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.post<ApiResponse<Client>>(
      API_ENDPOINTS.CLIENTS(tenantId),
      client
    );
    return response.data;
  }

  async getOrders(): Promise<Order[]> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.get<ApiResponse<Order[]>>(
      API_ENDPOINTS.ORDERS(tenantId)
    );
    return response.data;
  }

  // Smart Agents API
  async mapCatalog(query: string, context?: any): Promise<any> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.post<ApiResponse<any>>(
      API_ENDPOINTS.CATALOG_MAP(tenantId),
      { query, context }
    );
    return response.data;
  }

  async resolvePrice(productId: string, quantity: number, clientId?: string): Promise<any> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.post<ApiResponse<any>>(
      API_ENDPOINTS.PRICE_RESOLVE(tenantId),
      { product_id: productId, quantity, client_id: clientId }
    );
    return response.data;
  }

  async buildQuote(items: any[], clientId?: string): Promise<any> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.post<ApiResponse<any>>(
      API_ENDPOINTS.QUOTE_BUILD(tenantId),
      { items, client_id: clientId }
    );
    return response.data;
  }

  async getSuggestions(): Promise<any[]> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.get<ApiResponse<any[]>>(
      API_ENDPOINTS.SUGGESTIONS(tenantId)
    );
    return response.data;
  }

  async approveSuggestion(suggestionId: string): Promise<any> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.post<ApiResponse<any>>(
      `${API_ENDPOINTS.SUGGESTIONS(tenantId)}/${suggestionId}/approve`
    );
    return response.data;
  }

  // Conversations API
  async getConversations(): Promise<Conversation[]> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.get<ApiResponse<Conversation[]>>(
      API_ENDPOINTS.CONVERSATIONS(tenantId)
    );
    return response.data;
  }

  async startConversation(
    intent: string, 
    clientPhone: string, 
    message: string
  ): Promise<Conversation> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.post<ApiResponse<Conversation>>(
      API_ENDPOINTS.CONVERSATION_START(tenantId),
      { intent, client_phone: clientPhone, message }
    );
    return response.data;
  }

  async continueConversation(
    conversationId: string, 
    message: string
  ): Promise<Conversation> {
    const tenantId = apiService.getTenantId();
    if (!tenantId) throw new Error('No tenant ID available');

    const response = await apiService.post<ApiResponse<Conversation>>(
      API_ENDPOINTS.CONVERSATION_CONTINUE(tenantId, conversationId),
      { message }
    );
    return response.data;
  }

  // Dashboard API
  async getDashboardOverview(): Promise<DashboardMetrics['overview']> {
    const response = await apiService.get<ApiResponse<DashboardMetrics['overview']>>(
      API_ENDPOINTS.DASHBOARD_OVERVIEW
    );
    return response.data;
  }

  async getDashboardAgents(): Promise<DashboardMetrics['agents']> {
    const response = await apiService.get<ApiResponse<DashboardMetrics['agents']>>(
      API_ENDPOINTS.DASHBOARD_AGENTS
    );
    return response.data;
  }

  async getDashboardStripe(): Promise<DashboardMetrics['stripe']> {
    const response = await apiService.get<ApiResponse<DashboardMetrics['stripe']>>(
      API_ENDPOINTS.DASHBOARD_STRIPE
    );
    return response.data;
  }

  async getDashboardConversations(): Promise<any> {
    const response = await apiService.get<ApiResponse<any>>(
      API_ENDPOINTS.DASHBOARD_CONVERSATIONS
    );
    return response.data;
  }

  async getDashboardSystem(): Promise<any> {
    const response = await apiService.get<ApiResponse<any>>(
      API_ENDPOINTS.DASHBOARD_SYSTEM
    );
    return response.data;
  }

  // Stripe Connect API
  async getStripeAccounts(): Promise<any[]> {
    const response = await apiService.get<ApiResponse<any[]>>(
      API_ENDPOINTS.STRIPE_ACCOUNTS
    );
    return response.data;
  }

  async createStripeAccount(data: {
    email: string;
    charges_mode: string;
    pricing_mode: string;
  }): Promise<any> {
    const response = await apiService.post<ApiResponse<any>>(
      API_ENDPOINTS.STRIPE_ACCOUNTS,
      data
    );
    return response.data;
  }

  async createCheckoutSession(data: {
    amount: number;
    order_id: string;
    success_url: string;
    cancel_url: string;
  }): Promise<any> {
    const response = await apiService.post<ApiResponse<any>>(
      API_ENDPOINTS.STRIPE_CHECKOUT_DIRECT,
      data
    );
    return response.data;
  }

  async calculateFees(data: {
    amount: number;
    charges_mode: string;
  }): Promise<any> {
    const response = await apiService.post<ApiResponse<any>>(
      API_ENDPOINTS.STRIPE_FEES_CALCULATE,
      data
    );
    return response.data;
  }
}

export const orkestaApi = new OrkestaApiService();
export default orkestaApi;