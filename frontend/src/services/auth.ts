import api from './api'
import type { LoginRequest, RegisterRequest, AuthResponse } from '@/types/auth'

export const authApi = {
  login: (data: LoginRequest) => 
    api.post<AuthResponse>('/auth/login', data),
  
  register: (data: RegisterRequest) => 
    api.post<AuthResponse>('/auth/register', data),
  
  logout: () => 
    api.post('/auth/logout'),
  
  getCurrentUser: (userId: number) => 
    api.get<AuthResponse>('/auth/me', { params: { userId } }),
}

// 本地存储工具
export const authStorage = {
  setUser: (user: AuthResponse) => {
    localStorage.setItem('userId', user.userId.toString())
    localStorage.setItem('username', user.username)
    localStorage.setItem('userInfo', JSON.stringify(user))
  },
  
  getUser: (): AuthResponse | null => {
    const userInfo = localStorage.getItem('userInfo')
    return userInfo ? JSON.parse(userInfo) : null
  },
  
  getUserId: (): number | null => {
    const userId = localStorage.getItem('userId')
    return userId ? parseInt(userId) : null
  },
  
  clear: () => {
    localStorage.removeItem('userId')
    localStorage.removeItem('username')
    localStorage.removeItem('userInfo')
  },
  
  isLoggedIn: (): boolean => {
    return !!localStorage.getItem('userId')
  },
}
