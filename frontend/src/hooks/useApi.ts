import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import orkestaApi from '../services/orkestaApi';
import { Product, Client, Order, Conversation } from '../types';

// Query Keys
export const QUERY_KEYS = {
  PRODUCTS: 'products',
  CLIENTS: 'clients',
  ORDERS: 'orders',
  CONVERSATIONS: 'conversations',
  SUGGESTIONS: 'suggestions',
  DASHBOARD_OVERVIEW: 'dashboard-overview',
  DASHBOARD_AGENTS: 'dashboard-agents',
  DASHBOARD_STRIPE: 'dashboard-stripe',
  STRIPE_ACCOUNTS: 'stripe-accounts',
};

// Products hooks
export const useProducts = (searchQuery?: string) => {
  return useQuery({
    queryKey: [QUERY_KEYS.PRODUCTS, searchQuery],
    queryFn: () => orkestaApi.getProducts(searchQuery),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useAddProduct = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (product: Omit<Product, 'product_id'>) => 
      orkestaApi.addProduct(product),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.PRODUCTS] });
    },
  });
};

// Clients hooks
export const useClients = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.CLIENTS],
    queryFn: orkestaApi.getClients,
    staleTime: 5 * 60 * 1000,
  });
};

export const useAddClient = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (client: Omit<Client, 'client_id'>) => 
      orkestaApi.addClient(client),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.CLIENTS] });
    },
  });
};

// Orders hooks
export const useOrders = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.ORDERS],
    queryFn: orkestaApi.getOrders,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// Smart Agents hooks
export const useCatalogMap = () => {
  return useMutation({
    mutationFn: ({ query, context }: { query: string; context?: any }) =>
      orkestaApi.mapCatalog(query, context),
  });
};

export const useResolvePrice = () => {
  return useMutation({
    mutationFn: ({ productId, quantity, clientId }: { 
      productId: string; 
      quantity: number; 
      clientId?: string; 
    }) => orkestaApi.resolvePrice(productId, quantity, clientId),
  });
};

export const useBuildQuote = () => {
  return useMutation({
    mutationFn: ({ items, clientId }: { items: any[]; clientId?: string }) =>
      orkestaApi.buildQuote(items, clientId),
  });
};

export const useSuggestions = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.SUGGESTIONS],
    queryFn: orkestaApi.getSuggestions,
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  });
};

export const useApproveSuggestion = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (suggestionId: string) => 
      orkestaApi.approveSuggestion(suggestionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.SUGGESTIONS] });
    },
  });
};

// Conversations hooks
export const useConversations = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.CONVERSATIONS],
    queryFn: orkestaApi.getConversations,
    refetchInterval: 15 * 1000, // Refetch every 15 seconds
  });
};

export const useStartConversation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ intent, clientPhone, message }: {
      intent: string;
      clientPhone: string;
      message: string;
    }) => orkestaApi.startConversation(intent, clientPhone, message),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.CONVERSATIONS] });
    },
  });
};

export const useContinueConversation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ conversationId, message }: {
      conversationId: string;
      message: string;
    }) => orkestaApi.continueConversation(conversationId, message),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.CONVERSATIONS] });
    },
  });
};

// Dashboard hooks
export const useDashboardOverview = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.DASHBOARD_OVERVIEW],
    queryFn: orkestaApi.getDashboardOverview,
    refetchInterval: 60 * 1000, // Refetch every minute
  });
};

export const useDashboardAgents = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.DASHBOARD_AGENTS],
    queryFn: orkestaApi.getDashboardAgents,
    refetchInterval: 60 * 1000,
  });
};

export const useDashboardStripe = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.DASHBOARD_STRIPE],
    queryFn: orkestaApi.getDashboardStripe,
    refetchInterval: 60 * 1000,
  });
};

// Stripe hooks
export const useStripeAccounts = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.STRIPE_ACCOUNTS],
    queryFn: orkestaApi.getStripeAccounts,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useCreateStripeAccount = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: {
      email: string;
      charges_mode: string;
      pricing_mode: string;
    }) => orkestaApi.createStripeAccount(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.STRIPE_ACCOUNTS] });
    },
  });
};

export const useCreateCheckoutSession = () => {
  return useMutation({
    mutationFn: (data: {
      amount: number;
      order_id: string;
      success_url: string;
      cancel_url: string;
    }) => orkestaApi.createCheckoutSession(data),
  });
};

export const useCalculateFees = () => {
  return useMutation({
    mutationFn: (data: {
      amount: number;
      charges_mode: string;
    }) => orkestaApi.calculateFees(data),
  });
};