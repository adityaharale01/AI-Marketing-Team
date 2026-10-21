import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
@Component({selector:'app-public-shell',standalone:true,imports:[RouterLink],template:`
<header class="site-header"><a class="brand" routerLink="/"><span class="brand-mark">✳</span><span>crumbwise<span class="brand-dot">.</span><small>AI MARKETING TEAM</small></span></a><nav><a href="#features">Features</a><a href="#how-it-works">How it works</a></nav><div class="header-actions"><a class="login-link" routerLink="/login">Log in</a><a class="button button-dark button-small" routerLink="/register">Get started ↗</a></div></header><ng-content/><footer class="site-footer"><a class="brand footer-brand" routerLink="/"><span class="brand-mark">✳</span>crumbwise.</a><span>Thoughtful growth for your bakery.</span><span>© 2026 Crumbwise · AI Marketing Team</span></footer>`})
export class PublicShellComponent {}
