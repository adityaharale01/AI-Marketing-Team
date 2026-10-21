import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, switchMap, tap, map, catchError, throwError } from 'rxjs';
import { ApiService, ApiUser, ApiBusiness, BusinessCreateRequest } from './api.service';

export interface PlatformUser { id: number; name: string; email: string; role?: string; }
export interface BusinessProfile {
  id: number; name: string; category: string; city: string; createdAt: string;
  email?: string; phone?: string; address?: string; state?: string; country?: string; pincode?: string;
}

@Injectable({ providedIn: 'root' })
export class PlatformService {
  private readonly userKey = 'aimarketing_user';
  private readonly businessesKey = 'aimarketing_businesses';
  private readonly activeKey = 'aimarketing_active_business';
  private readonly tokenKey = 'aimarketing_access_token';

  constructor(private router: Router, private api: ApiService) {}

  get user(): PlatformUser | null {
    const raw = localStorage.getItem(this.userKey);
    if (!raw) return null;
    try { return JSON.parse(raw) as PlatformUser; } catch { return null; }
  }
  get businesses(): BusinessProfile[] {
    const raw = localStorage.getItem(this.businessesKey);
    if (!raw) return [];
    try { return JSON.parse(raw) as BusinessProfile[]; } catch { return []; }
  }
  get activeBusiness(): BusinessProfile | null {
    const id = Number(localStorage.getItem(this.activeKey));
    return this.businesses.find(b => b.id === id) ?? this.businesses[0] ?? null;
  }
  get isLoggedIn(): boolean { return !!localStorage.getItem(this.tokenKey); }

  register(name: string, email: string, password: string): Observable<ApiUser> {
    return this.api.register({ full_name: name.trim(), email: email.trim().toLowerCase(), password });
  }

  login(email: string, password: string): Observable<void> {
    return this.api.login({ email: email.trim().toLowerCase(), password }).pipe(
      tap(token => localStorage.setItem(this.tokenKey, token.access_token)),
      switchMap(() => this.api.currentUser()),
      tap(user => this.storeUser(user)),
      switchMap(() => this.api.getBusinesses()),
      tap(businesses => this.storeBusinesses(businesses)),
      map(() => undefined),
      catchError(error => { localStorage.removeItem(this.tokenKey); localStorage.removeItem(this.userKey); return throwError(() => error); })
    );
  }

  refreshBusinesses(): Observable<BusinessProfile[]> {
    return this.api.getBusinesses().pipe(map(items => items.map(b => this.toBusiness(b))), tap(items => {
      localStorage.setItem(this.businessesKey, JSON.stringify(items));
      const active = localStorage.getItem(this.activeKey);
      if (!active || !items.some(b => String(b.id) === active)) {
        if (items.length) localStorage.setItem(this.activeKey, String(items[0].id));
        else localStorage.removeItem(this.activeKey);
      }
    }));
  }

  addBusiness(input: BusinessCreateRequest): Observable<BusinessProfile> {
    return this.api.createBusiness(input).pipe(
      map(business => this.toBusiness(business)),
      tap(business => {
        const existing = this.businesses.filter(item => item.id !== business.id);
        localStorage.setItem(this.businessesKey, JSON.stringify([...existing, business]));
        localStorage.setItem(this.activeKey, String(business.id));
      })
    );
  }

  selectBusiness(id: number | string): void {
    if (this.businesses.some(b => String(b.id) === String(id))) localStorage.setItem(this.activeKey, String(id));
  }
  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
    localStorage.removeItem(this.businessesKey);
    localStorage.removeItem(this.activeKey);
    void this.router.navigateByUrl('/login');
  }
  continueAfterLogin(): void {
    void this.router.navigateByUrl(this.businesses.length ? '/dashboard' : '/business-setup');
  }

  private storeUser(user: ApiUser): void {
    localStorage.setItem(this.userKey, JSON.stringify({ id: user.id, name: user.full_name, email: user.email, role: user.role }));
  }
  private storeBusinesses(items: ApiBusiness[]): void {
    const mapped = items.map(item => this.toBusiness(item));
    localStorage.setItem(this.businessesKey, JSON.stringify(mapped));
    const active = localStorage.getItem(this.activeKey);
    if (!active || !mapped.some(b => String(b.id) === active)) {
      if (mapped.length) localStorage.setItem(this.activeKey, String(mapped[0].id));
      else localStorage.removeItem(this.activeKey);
    }
  }
  private toBusiness(b: ApiBusiness): BusinessProfile {
    return { id: b.id, name: b.business_name, category: b.business_type, city: b.city, createdAt: b.created_at,
      email: b.email, phone: b.phone, address: b.address, state: b.state, country: b.country, pincode: b.pincode };
  }
}
