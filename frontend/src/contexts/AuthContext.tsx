import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { AuthState, User } from '../types';
import apiService from '../services/api';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth Reducer
type AuthAction = 
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User }
  | { type: 'CLEAR_USER' }
  | { type: 'SET_TOKEN'; payload: string };

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
      };
    
    case 'SET_TOKEN':
      return { ...state, token: action.payload };
    
    case 'CLEAR_USER':
      return {
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      };
    
    default:
      return state;
  }
};

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      // Check if user is already authenticated
      if (apiService.isAuthenticated()) {
        // Try to get user profile
        await refreshUser();
      } else {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      dispatch({ type: 'CLEAR_USER' });
    }
  };

  const login = async (email: string, password: string): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      // Mock login for now - replace with actual API call
      const mockResponse = {
        user: {
          id: 'user_123',
          email,
          tenantId: 'test-tenant',
          role: 'agent' as const,
          name: 'Usuario Demo',
        },
        token: 'mock_jwt_token_' + Date.now(),
      };

      // Set auth in API service
      await apiService.setAuth(mockResponse.token, mockResponse.user.tenantId);

      // Update state
      dispatch({ type: 'SET_TOKEN', payload: mockResponse.token });
      dispatch({ type: 'SET_USER', payload: mockResponse.user });

    } catch (error) {
      console.error('Login error:', error);
      dispatch({ type: 'CLEAR_USER' });
      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await apiService.clearAuth();
      dispatch({ type: 'CLEAR_USER' });
    } catch (error) {
      console.error('Logout error:', error);
      // Clear state anyway
      dispatch({ type: 'CLEAR_USER' });
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      // Mock user refresh - replace with actual API call
      const mockUser: User = {
        id: 'user_123',
        email: 'demo@orkesta.com',
        tenantId: 'test-tenant',
        role: 'agent',
        name: 'Usuario Demo',
      };

      dispatch({ type: 'SET_USER', payload: mockUser });
    } catch (error) {
      console.error('Refresh user error:', error);
      dispatch({ type: 'CLEAR_USER' });
    }
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};