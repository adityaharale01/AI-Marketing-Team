import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export const API_BASE_URL = environment.apiBaseUrl;

export interface RegisterRequest { full_name: string; email: string; password: string; }
export interface LoginRequest { email: string; password: string; }
export interface AuthToken { access_token: string; token_type: string; }
export interface ApiUser { id: number; full_name: string; email: string; role: string; created_at: string; }
export interface ApiBusiness {
  id: number; business_name: string; business_type: string; description?: string | null;
  email: string; phone: string; website?: string | null; address: string; city: string;
  state: string; country: string; pincode: string; logo?: string | null;
  gst_number?: string | null; business_registration_number?: string | null;
  owner_id: number; is_active: boolean; created_at: string; updated_at: string;
}
export interface MarketingCampaignRequest {
  campaign_name: string;
  goal: string;
  platform: string;
  target_audience?: string;
  offer?: string;
  budget?: number | null;
  business_id?: number;
}

export interface MarketingCampaignResult {
  campaign_id: number;
  business: { id: number; name: string; type: string };
  campaign_name: string;
  objective: string;
  platform: string;
  target_audience: string;
  strategy: string;
  caption: string;
  hashtags: string[];
  poster: {
    headline: string;
    subtitle: string;
    call_to_action: string;
  };
  content_notes: string;
  status: string;
  publish_mode: string;
  message: string;
}

export interface MarketingPublishResult {
  campaign_id: number;
  status: string;
  simulated: boolean;
  platform: string;
  message: string;
}
export interface BusinessCreateRequest {
  business_name: string; business_type: string; description?: string | null;
  email: string; phone: string; website?: string | null; address: string; city: string;
  state: string; country: string; pincode: string; logo?: string | null;
  gst_number?: string | null; business_registration_number?: string | null;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = API_BASE_URL;
  constructor(private http: HttpClient) {}

  /**
   * Every business-scoped request carries business_id so the backend resolves
   * the currently selected business instead of defaulting to the first one.
   */
  private businessParams(businessId?: number | string, extra?: HttpParams): HttpParams {
    let params = extra ?? new HttpParams();
    if (businessId !== undefined && businessId !== null && `${businessId}` !== '') {
      params = params.set('business_id', `${businessId}`);
    }
    return params;
  }

  register(payload: RegisterRequest): Observable<ApiUser> {
    return this.http.post<ApiUser>(`${this.baseUrl}/auth/register`, payload);
  }
  login(payload: LoginRequest): Observable<AuthToken> {
    return this.http.post<AuthToken>(`${this.baseUrl}/auth/login`, payload);
  }
  currentUser(): Observable<ApiUser> {
    return this.http.get<ApiUser>(`${this.baseUrl}/users/me`);
  }
  getBusinesses(): Observable<ApiBusiness[]> {
    return this.http.get<ApiBusiness[]>(`${this.baseUrl}/business/`);
  }
  createBusiness(payload: BusinessCreateRequest): Observable<ApiBusiness> {
    return this.http.post<ApiBusiness>(`${this.baseUrl}/business/`, payload);
  }
  getBusinessAnalytics(businessId: number | string): Observable<unknown> {
    return this.http.get<unknown>(`${this.baseUrl}/ai/business-analytics/${businessId}`);
  }
  askBusinessAgent(businessId: number | string, query: string): Observable<unknown> {
    const params = new HttpParams().set('business_id', businessId).set('query', query);
    return this.http.post<unknown>(`${this.baseUrl}/ai/business-agent`, null, { params });
  }

  // Products
  listProducts(businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/products/`, { params: this.businessParams(businessId) }); }
  createProduct(payload: Record<string, unknown>, businessId?: number | string): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/products/`, payload, { params: this.businessParams(businessId) }); }
  searchProducts(query: string, businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/products/search`, { params: this.businessParams(businessId, new HttpParams().set('name', query)) }); }
  getProduct(id: number | string, businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/products/${id}`, { params: this.businessParams(businessId) }); }
  updateProduct(id: number | string, payload: Record<string, unknown>, businessId?: number | string): Observable<unknown> { return this.http.put<unknown>(`${this.baseUrl}/products/${id}`, payload, { params: this.businessParams(businessId) }); }
  deleteProduct(id: number | string, businessId?: number | string): Observable<unknown> { return this.http.delete<unknown>(`${this.baseUrl}/products/${id}`, { params: this.businessParams(businessId) }); }

  // Sales
  listSales(businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/sales/`, { params: this.businessParams(businessId) }); }
  createSale(payload: Record<string, unknown>, businessId?: number | string): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/sales/`, payload, { params: this.businessParams(businessId) }); }
  getSalesForProduct(productId: number | string, businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/sales/product/${productId}`, { params: this.businessParams(businessId) }); }
  getSale(id: number | string, businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/sales/${id}`, { params: this.businessParams(businessId) }); }
  updateSale(id: number | string, payload: Record<string, unknown>, businessId?: number | string): Observable<unknown> { return this.http.put<unknown>(`${this.baseUrl}/sales/${id}`, payload, { params: this.businessParams(businessId) }); }
  deleteSale(id: number | string, businessId?: number | string): Observable<unknown> { return this.http.delete<unknown>(`${this.baseUrl}/sales/${id}`, { params: this.businessParams(businessId) }); }

  // Campaigns
  listCampaigns(businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/campaigns/`, { params: this.businessParams(businessId) }); }
  createCampaign(payload: Record<string, unknown>, businessId?: number | string): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/campaigns/`, payload, { params: this.businessParams(businessId) }); }
  searchCampaigns(name: string, businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/campaigns/search`, { params: this.businessParams(businessId, new HttpParams().set('name', name)) }); }
  getCampaignsByStatus(status: string, businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/campaigns/status/${encodeURIComponent(status)}`, { params: this.businessParams(businessId) }); }
  getCampaign(id: number | string, businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/campaigns/${id}`, { params: this.businessParams(businessId) }); }
  updateCampaign(id: number | string, payload: Record<string, unknown>, businessId?: number | string): Observable<unknown> { return this.http.put<unknown>(`${this.baseUrl}/campaigns/${id}`, payload, { params: this.businessParams(businessId) }); }
  deleteCampaign(id: number | string, businessId?: number | string): Observable<unknown> { return this.http.delete<unknown>(`${this.baseUrl}/campaigns/${id}`, { params: this.businessParams(businessId) }); }

  // AI / RAG
  getAiPerformance(businessId: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/ai/performance/${businessId}`); }
  indexBusinessKnowledge(businessId: number | string): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/ai/rag/index/${businessId}`, null); }
  askKnowledge(query: string, businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/ai/rag/ask`, { params: this.businessParams(businessId, new HttpParams().set('query', query)) }); }
  searchKnowledge(query: string, businessId?: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/ai/rag/search`, { params: this.businessParams(businessId, new HttpParams().set('query', query)) }); }
  addKnowledge(payload: { content: string; title?: string }, businessId?: number | string): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/ai/rag/add`, payload, { params: this.businessParams(businessId) }); }
  testAi(): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/ai/test`); }


  generatePosterArtwork(prompt: string, steps = 4): Observable<{ image_data_url: string }> {
    return this.http.post<{ image_data_url: string }>(
      `${this.baseUrl}/marketing-agent/generate-poster`,
      { prompt, steps }
    );
  }

  generateMarketingCampaign(
  payload: MarketingCampaignRequest
): Observable<MarketingCampaignResult> {
  return this.http.post<MarketingCampaignResult>(
    `${this.baseUrl}/marketing-agent/generate`,
    payload
  );
}

publishCampaignDemo(
  campaignId: number | string
): Observable<MarketingPublishResult> {
  return this.http.post<MarketingPublishResult>(
    `${this.baseUrl}/marketing-agent/${campaignId}/publish-demo`,
    {}
  );
}
}
