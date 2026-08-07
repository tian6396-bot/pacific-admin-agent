export type UserRole = 'employee' | 'agent' | 'admin'

export interface UserInfo {
  id: string
  name: string
  username: string
  role: UserRole
  department?: string
}

export interface LoginPayload {
  username: string
  password: string
}
