import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

// Change this if FastAPI runs on a different host or port.
export const API_BASE_URL = 'http://127.0.0.1:8000';

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
  listProducts(): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/products/`); }
  createProduct(payload: Record<string, unknown>): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/products/`, payload); }
  searchProducts(query: string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/products/search`, { params: new HttpParams().set('name', query) }); }
  getProduct(id: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/products/${id}`); }
  updateProduct(id: number | string, payload: Record<string, unknown>): Observable<unknown> { return this.http.put<unknown>(`${this.baseUrl}/products/${id}`, payload); }
  deleteProduct(id: number | string): Observable<unknown> { return this.http.delete<unknown>(`${this.baseUrl}/products/${id}`); }

  // Sales
  listSales(): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/sales/`); }
  createSale(payload: Record<string, unknown>): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/sales/`, payload); }
  getSalesForProduct(productId: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/sales/product/${productId}`); }
  getSale(id: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/sales/${id}`); }
  updateSale(id: number | string, payload: Record<string, unknown>): Observable<unknown> { return this.http.put<unknown>(`${this.baseUrl}/sales/${id}`, payload); }
  deleteSale(id: number | string): Observable<unknown> { return this.http.delete<unknown>(`${this.baseUrl}/sales/${id}`); }

  // Campaigns
  listCampaigns(): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/campaigns/`); }
  createCampaign(payload: Record<string, unknown>): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/campaigns/`, payload); }
  searchCampaigns(name: string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/campaigns/search`, { params: new HttpParams().set('name', name) }); }
  getCampaignsByStatus(status: string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/campaigns/status/${encodeURIComponent(status)}`); }
  getCampaign(id: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/campaigns/${id}`); }
  updateCampaign(id: number | string, payload: Record<string, unknown>): Observable<unknown> { return this.http.put<unknown>(`${this.baseUrl}/campaigns/${id}`, payload); }
  deleteCampaign(id: number | string): Observable<unknown> { return this.http.delete<unknown>(`${this.baseUrl}/campaigns/${id}`); }

  // AI / RAG
  getAiPerformance(businessId: number | string): Observable<unknown> { return this.http.get<unknown>(`${this.baseUrl}/ai/performance/${businessId}`); }
  indexBusinessKnowledge(businessId: number | string): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/ai/rag/index/${businessId}`, null); }
  askKnowledge(query: string): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/ai/rag/ask`, null, { params: new HttpParams().set('query', query) }); }
  searchKnowledge(query: string): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/ai/rag/search`, { query }); }
  addKnowledge(payload: Record<string, unknown>): Observable<unknown> { return this.http.post<unknown>(`${this.baseUrl}/ai/rag/add`, payload); }
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
