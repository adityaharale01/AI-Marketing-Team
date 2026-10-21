import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { PlatformService } from '../../core/services/platform.service';

@Component({ selector: 'app-login', standalone: true, imports: [CommonModule, ReactiveFormsModule, RouterLink], templateUrl: './login.component.html', styleUrl: '../auth/auth.component.css' })
export class LoginComponent {
  error = '';
  loading = false;
  form;
  constructor(private fb: FormBuilder, private platform: PlatformService, private router: Router) {
    this.form = this.fb.nonNullable.group({ email: ['', [Validators.required, Validators.email]], password: ['', [Validators.required]] });
  }
  submit(): void {
    this.error = '';
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const { email, password } = this.form.getRawValue();
    this.loading = true;
    this.platform.login(email, password).subscribe({
      next: () => { this.loading = false; this.platform.continueAfterLogin(); },
      error: (err: HttpErrorResponse) => {
        this.loading = false;
        const detail = err.error?.detail;
        this.error = typeof detail === 'string' ? detail : (err.status === 0 ? 'Cannot reach the backend. Start FastAPI at http://127.0.0.1:8000 and check CORS.' : 'Login failed. Check your email and password.');
      }
    });
  }
}
