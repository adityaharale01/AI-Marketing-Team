import { HttpInterceptorFn } from '@angular/common/http';
import { API_BASE_URL } from '../services/api.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem('aimarketing_access_token');
  const isBackendRequest = req.url.startsWith(API_BASE_URL);
  if (!token || !isBackendRequest || req.url.endsWith('/auth/login') || req.url.endsWith('/auth/register')) {
    return next(req);
  }
  return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};
