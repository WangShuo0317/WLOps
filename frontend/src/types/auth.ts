export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
  realName?: string
}

export interface AuthResponse {
  userId: number
  username: string
  email?: string
  realName?: string
  role: string
  message?: string
}

export interface UserInfo {
  userId: number
  username: string
  email?: string
  realName?: string
  role: string
}
