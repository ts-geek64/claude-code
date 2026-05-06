export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupCredentials {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface AuthResponse {
  token: string;
  user: AuthUser;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
}
