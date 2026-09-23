import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface User {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly TOKEN_KEY = 'md_access_token';
  private readonly USER_KEY = 'md_user';

  private readonly currentUser = signal<User | null>(
    this.readStoredUser()
  );

  readonly user = this.currentUser.asReadonly();

  constructor(private http: HttpClient) {}

  register(
    name: string,
    email: string,
    password: string
  ): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(
        `${environment.apiBaseUrl}/auth/register`,
        {
          name: name.trim(),
          email: email.trim().toLowerCase(),
          password,
        }
      )
      .pipe(
        tap((response) => {
          this.saveAuth(response);
        })
      );
  }

  login(
    email: string,
    password: string
  ): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(
        `${environment.apiBaseUrl}/auth/login`,
        {
          email: email.trim().toLowerCase(),
          password,
        }
      )
      .pipe(
        tap((response) => {
          this.saveAuth(response);
        })
      );
  }

  getMe(): Observable<User> {
    return this.http
      .get<User>(`${environment.apiBaseUrl}/auth/me`)
      .pipe(
        tap((user) => {
          this.currentUser.set(user);
          localStorage.setItem(
            this.USER_KEY,
            JSON.stringify(user)
          );
        })
      );
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem(this.TOKEN_KEY);
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.currentUser.set(null);
  }

  private saveAuth(response: AuthResponse): void {
    localStorage.setItem(
      this.TOKEN_KEY,
      response.access_token
    );

    localStorage.setItem(
      this.USER_KEY,
      JSON.stringify(response.user)
    );

    this.currentUser.set(response.user);
  }

  private readStoredUser(): User | null {
    try {
      const raw = localStorage.getItem(this.USER_KEY);

      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }
}