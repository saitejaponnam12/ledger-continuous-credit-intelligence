/**
 * LEDGER — Auth Store (Zustand)
 * JWT token management, user state persistence.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi } from '../lib/api'

interface User {
  user_id: string
  email: string
  display_name: string
  role: string
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.login(email, password)
          const { access_token, user_id, display_name, role } = response.data
          localStorage.setItem('ledger_token', access_token)
          set({
            token: access_token,
            user: { user_id, email, display_name, role },
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (err: any) {
          set({
            error: err.response?.data?.detail || 'Login failed',
            isLoading: false,
          })
          throw err
        }
      },

      logout: () => {
        localStorage.removeItem('ledger_token')
        set({ token: null, user: null, isAuthenticated: false })
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'ledger-auth',
      partialize: (state) => ({ token: state.token, user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
)
