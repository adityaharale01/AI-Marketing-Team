import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { PlatformService } from '../services/platform.service';
export const authGuard:CanActivateFn=()=>{const p=inject(PlatformService);const r=inject(Router);return p.isLoggedIn?true:r.createUrlTree(['/login']);};
export const onboardingGuard:CanActivateFn=()=>{const p=inject(PlatformService);const r=inject(Router);if(!p.isLoggedIn)return r.createUrlTree(['/login']);if(!p.businesses.length)return r.createUrlTree(['/business-setup']);return true;};
