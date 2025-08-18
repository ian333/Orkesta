// API Base Configuration
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000',
  CONTROL_TOWER_URL: 'http://localhost:8003',
  CONTROL_TOWER_V2_URL: 'http://localhost:8004',
  TIMEOUT: 10000,
};

// API Endpoints
export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/auth/login',
  LOGOUT: '/auth/logout',
  PROFILE: '/auth/profile',
  
  // Context (Shared Brain)
  PRODUCTS: (tenantId: string) => `/api/context/${tenantId}/products`,
  PRODUCT_SEARCH: (tenantId: string) => `/api/context/${tenantId}/products/search`,
  CLIENTS: (tenantId: string) => `/api/context/${tenantId}/clients`,
  ORDERS: (tenantId: string) => `/api/context/${tenantId}/orders`,
  
  // Smart Agents
  CATALOG_MAP: (tenantId: string) => `/api/agents/${tenantId}/catalog/map`,
  PRICE_RESOLVE: (tenantId: string) => `/api/agents/${tenantId}/pricing/resolve`,
  QUOTE_BUILD: (tenantId: string) => `/api/agents/${tenantId}/quote/build`,
  SUGGESTIONS: (tenantId: string) => `/api/agents/${tenantId}/suggestions`,
  
  // Conversations
  CONVERSATIONS: (tenantId: string) => `/api/conversations/${tenantId}`,
  CONVERSATION_START: (tenantId: string) => `/api/conversations/${tenantId}/start`,
  CONVERSATION_CONTINUE: (tenantId: string, convId: string) => 
    `/api/conversations/${tenantId}/${convId}/continue`,
  
  // Dashboard
  DASHBOARD_OVERVIEW: '/api/dashboard/overview',
  DASHBOARD_AGENTS: '/api/dashboard/agents',
  DASHBOARD_STRIPE: '/api/dashboard/stripe',
  DASHBOARD_CONVERSATIONS: '/api/dashboard/conversations',
  DASHBOARD_SYSTEM: '/api/dashboard/system',
  
  // Stripe Connect
  STRIPE_ACCOUNTS: '/api/connect/accounts',
  STRIPE_CHECKOUT_DIRECT: '/api/connect/checkout/direct',
  STRIPE_FEES_CALCULATE: '/api/connect/fees/calculate',
};

// Request Headers
export const API_HEADERS = {
  CONTENT_TYPE: 'application/json',
  ORG_ID: 'X-Org-Id',
  AUTHORIZATION: 'Authorization',
};

// Error Messages
export const API_ERRORS = {
  NETWORK_ERROR: 'Error de conexión. Verifica tu internet.',
  UNAUTHORIZED: 'No autorizado. Inicia sesión nuevamente.',
  FORBIDDEN: 'No tienes permisos para esta acción.',
  NOT_FOUND: 'Recurso no encontrado.',
  SERVER_ERROR: 'Error del servidor. Intenta más tarde.',
  TIMEOUT: 'Tiempo de espera agotado.',
  UNKNOWN: 'Error desconocido.',
};