import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { ApiService } from '../../core/services/api.service';
import { BusinessProfile, PlatformService } from '../../core/services/platform.service';

@Component({ selector: 'app-dashboard', standalone: true, imports: [CommonModule, FormsModule, RouterLink], templateUrl: './dashboard.component.html', styleUrl: './dashboard.component.css' })
export class DashboardComponent implements OnInit {
  showBusinesses = false;
  analytics: Record<string, any> | null = null;
  analyticsLoading = false;
  analyticsError = '';
  question = '';
  answer = '';
  assistantError = '';
  assistantLoading = false;

  constructor(public platform: PlatformService, private router: Router, private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    if (this.platform.isLoggedIn) {
      this.platform.refreshBusinesses().subscribe({
        next: businesses => { if (!businesses.length) void this.router.navigateByUrl('/business-setup'); else this.loadAnalytics(); },
        error: () => this.loadAnalytics()
      });
    }
  }
  selectBusiness(id: number): void {
    this.platform.selectBusiness(id);
    this.showBusinesses = false;
    this.analytics = null;
    this.answer = '';
    this.loadAnalytics();
  }
  addBusiness(): void { void this.router.navigateByUrl('/business-setup'); }
  loadAnalytics(): void {
    const business = this.platform.activeBusiness;
    if (!business) return;
    this.analyticsLoading = true;
    this.analyticsError = '';
    this.api.getBusinessAnalytics(business.id).subscribe({
      next: result => { this.analytics = this.asObject(result); this.analyticsLoading = false; this.cdr.detectChanges(); },
      error: (err: HttpErrorResponse) => { this.analyticsLoading = false; this.analyticsError = this.errorText(err, 'Could not load analytics.'); this.cdr.detectChanges(); }
    });
  }
  askBusiness(): void {
    const business = this.platform.activeBusiness;
    const query = this.question.trim();
    if (!business || !query || this.assistantLoading) return;
    this.assistantLoading = true;
    this.assistantError = '';
    this.answer = '';
    this.api.askBusinessAgent(business.id, query).subscribe({
      next: result => { this.answer = this.answerText(result); this.assistantLoading = false; this.cdr.detectChanges(); },
      error: (err: HttpErrorResponse) => { this.assistantError = this.errorText(err, 'The AI assistant could not answer right now.'); this.assistantLoading = false; this.cdr.detectChanges(); }
    });
  }
  get revenueLabel(): string { const n = this.findNumber(['overall.recent_revenue', 'recent_revenue', 'revenue', 'summary.recent_revenue', 'total_revenue']); return n === null ? '—' : new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n); }
  get unitsLabel(): string { const n = this.findNumber(['overall.recent_quantity', 'recent_quantity', 'units_sold', 'total_quantity', 'summary.recent_quantity']); return n === null ? '—' : new Intl.NumberFormat('en-IN').format(n); }
  get growthLabel(): string { const n = this.findNumber(['overall.revenue_growth_percent', 'revenue_growth_percent', 'growth_percent', 'summary.revenue_growth_percent']); return n === null ? 'See analytics' : `${n > 0 ? '+' : ''}${n.toFixed(1)}%`; }
  get productsLabel(): string { const p = this.findArray(['products', 'product_analytics', 'summary.products']); return p ? String(p.length) : 'See analytics'; }
  get rawAnalytics(): string { return this.analytics ? JSON.stringify(this.analytics, null, 2) : ''; }
  private findNumber(paths: string[]): number | null {
    if (!this.analytics) return null;
    for (const path of paths) {
      let value: any = this.analytics;
      for (const part of path.split('.')) value = value?.[part];
      if (value !== undefined && value !== null && value !== '' && Number.isFinite(Number(value))) return Number(value);
    }
    return null;
  }
  private findArray(paths: string[]): unknown[] | null {
    if (!this.analytics) return null;
    for (const path of paths) { let value: any = this.analytics; for (const part of path.split('.')) value = value?.[part]; if (Array.isArray(value)) return value; }
    return null;
  }
  private asObject(value: unknown): Record<string, any> {
    if (typeof value === 'object' && value !== null) return value as Record<string, any>;
    return { result: value };
  }
  private answerText(value: unknown): string {
    if (typeof value === 'string') return value;
    if (typeof value === 'object' && value !== null) {
      const obj = value as Record<string, unknown>;
      for (const key of ['answer', 'response', 'message', 'result', 'ai_response']) if (typeof obj[key] === 'string') return obj[key] as string;
    }
    return JSON.stringify(value, null, 2);
  }
  private errorText(err: HttpErrorResponse, fallback: string): string {
    const detail = err.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((item: { msg?: string }) => item.msg ?? '').filter(Boolean).join(' ');
    if (err.status === 0) return 'Cannot reach the backend. Confirm FastAPI is running at http://127.0.0.1:8000 and check CORS.';
    return fallback;
  }
}
