import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_CONFIG, API_HEADERS, API_ERRORS } from '../constants/api';

class ApiService {
  private instance: AxiosInstance;
  private tenantId: string | null = null;
  private token: string | null = null;

  constructor() {
    this.instance = axios.create({
      baseURL: API_CONFIG.BASE_URL,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': API_HEADERS.CONTENT_TYPE,
      },
    });

    this.setupInterceptors();
    this.loadStoredAuth();
  }

  private setupInterceptors() {
    // Request interceptor
    this.instance.interceptors.request.use(
      async (config) => {
        // Add auth token if available
        if (this.token) {
          config.headers[API_HEADERS.AUTHORIZATION] = `Bearer ${this.token}`;
        }

        // Add tenant ID if available
        if (this.tenantId) {
          config.headers[API_HEADERS.ORG_ID] = this.tenantId;
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 errors
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          await this.clearAuth();
          // Redirect to login would be handled by navigation context
          return Promise.reject(new Error(API_ERRORS.UNAUTHORIZED));
        }

        // Handle other errors
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private async loadStoredAuth() {
    try {
      const [storedToken, storedTenantId] = await Promise.all([
        AsyncStorage.getItem('auth_token'),
        AsyncStorage.getItem('tenant_id'),
      ]);

      if (storedToken && storedTenantId) {
        this.token = storedToken;
        this.tenantId = storedTenantId;
      }
    } catch (error) {
      console.error('Error loading stored auth:', error);
    }
  }

  private handleError(error: any): Error {
    if (error.code === 'ECONNABORTED') {
      return new Error(API_ERRORS.TIMEOUT);
    }

    if (!error.response) {
      return new Error(API_ERRORS.NETWORK_ERROR);
    }

    const { status } = error.response;

    switch (status) {
      case 401:
        return new Error(API_ERRORS.UNAUTHORIZED);
      case 403:
        return new Error(API_ERRORS.FORBIDDEN);
      case 404:
        return new Error(API_ERRORS.NOT_FOUND);
      case 500:
      case 502:
      case 503:
      case 504:
        return new Error(API_ERRORS.SERVER_ERROR);
      default:
        return new Error(API_ERRORS.UNKNOWN);
    }
  }

  // Auth methods
  async setAuth(token: string, tenantId: string) {
    this.token = token;
    this.tenantId = tenantId;

    await Promise.all([
      AsyncStorage.setItem('auth_token', token),
      AsyncStorage.setItem('tenant_id', tenantId),
    ]);
  }

  async clearAuth() {
    this.token = null;
    this.tenantId = null;

    await Promise.all([
      AsyncStorage.removeItem('auth_token'),
      AsyncStorage.removeItem('tenant_id'),
    ]);
  }

  // HTTP methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config);
    return response.data;
  }

  // Utility methods
  setBaseURL(url: string) {
    this.instance.defaults.baseURL = url;
  }

  getTenantId(): string | null {
    return this.tenantId;
  }

  getToken(): string | null {
    return this.token;
  }

  isAuthenticated(): boolean {
    return !!(this.token && this.tenantId);
  }
}

export const apiService = new ApiService();
export default apiService;