import { Injectable, signal } from '@angular/core';
import { BehaviorSubject, Observable, of, throwError } from 'rxjs';
import { delay, map, tap } from 'rxjs/operators';

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'Administrator' | 'Marketing Manager' | 'Guest';
  avatar: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly TOKEN_KEY = 'ai_marketing_jwt_token';
  private readonly USER_KEY = 'ai_marketing_user';

  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  // Also expose a signal for modern Angular templating ease
  public currentUser = signal<User | null>(null);

  constructor() {
    this.loadSession();
  }

  private loadSession(): void {
    const token = localStorage.getItem(this.TOKEN_KEY);
    const userJson = localStorage.getItem(this.USER_KEY);
    if (token && userJson) {
      try {
        const user = JSON.parse(userJson);
        this.currentUserSubject.next(user);
        this.currentUser.set(user);
      } catch (e) {
        this.clearSession();
      }
    }
  }

  public isAuthenticated(): boolean {
    return !!localStorage.getItem(this.TOKEN_KEY);
  }

  public getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  public login(email: string, password: string): Observable<User> {
    if (!email || !password || password.length < 6) {
      return throwError(() => new Error('Invalid email or password (min 6 characters)'));
    }

    const name = email.split('@')[0];
    const formattedName = name.charAt(0).toUpperCase() + name.slice(1);
    
    const mockUser: User = {
      id: 'usr_' + Math.random().toString(36).substring(2, 11),
      email: email,
      name: formattedName,
      role: email.includes('admin') ? 'Administrator' : 'Marketing Manager',
      avatar: `https://api.dicebear.com/7.x/bottts/svg?seed=${formattedName}`
    };

    return of(mockUser).pipe(
      delay(800),
      tap((user) => {
        const mockToken = this.generateMockJWT(email);
        localStorage.setItem(this.TOKEN_KEY, mockToken);
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        this.currentUserSubject.next(user);
        this.currentUser.set(user);
      })
    );
  }

  public logout(): void {
    this.clearSession();
  }

  private clearSession(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.currentUserSubject.next(null);
    this.currentUser.set(null);
  }

  private generateMockJWT(email: string): string {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({
      sub: email,
      exp: Math.floor(Date.now() / 1000) + 3600,
      iat: Math.floor(Date.now() / 1000)
    }));
    const signature = 'simulated_signature_hash_xyz';
    return `${header}.${payload}.${signature}`;
  }
}
