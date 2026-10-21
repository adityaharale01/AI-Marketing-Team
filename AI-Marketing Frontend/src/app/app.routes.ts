import { Routes } from '@angular/router';
import { LandingComponent } from './pages/landing/landing.component';
import { RegisterComponent } from './pages/register/register.component';
import { LoginComponent } from './pages/login/login.component';
import { BusinessSetupComponent } from './pages/business-setup/business-setup.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { WorkspaceComponent } from './pages/workspace/workspace.component';
import { authGuard, onboardingGuard } from './core/guards/auth.guard';
export const routes: Routes = [
 { path: '', component: LandingComponent },
 { path: 'register', component: RegisterComponent },
 { path: 'login', component: LoginComponent },
 { path: 'business-setup', component: BusinessSetupComponent, canActivate: [authGuard] },
 { path: 'dashboard', component: DashboardComponent, canActivate: [onboardingGuard] },
 { path: 'workspace', component: WorkspaceComponent, canActivate: [onboardingGuard] },
 { path: '**', redirectTo: '' }
];
