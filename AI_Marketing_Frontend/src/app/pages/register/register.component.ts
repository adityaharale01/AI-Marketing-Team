import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { PlatformService } from '../../core/services/platform.service';

@Component({ selector: 'app-register', standalone: true, imports: [CommonModule, ReactiveFormsModule, RouterLink], templateUrl: './register.component.html', styleUrl: '../auth/auth.component.css' })
export class RegisterComponent {
  error = '';
  loading = false;
  form;
  constructor(private fb: FormBuilder, private platform: PlatformService, private router: Router) {
    this.form = this.fb.nonNullable.group({ name: ['', [Validators.required, Validators.minLength(2)]], email: ['', [Validators.required, Validators.email]], password: ['', [Validators.required, Validators.minLength(8)]], confirmPassword: ['', [Validators.required]] });
  }
  submit(): void {
    this.error = '';
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const { name, email, password, confirmPassword } = this.form.getRawValue();
    if (password !== confirmPassword) { this.error = 'Your passwords do not match.'; return; }
    this.loading = true;
    this.platform.register(name, email, password).subscribe({
      next: () => this.platform.login(email, password).subscribe({
        next: () => { this.loading = false; void this.router.navigateByUrl('/business-setup'); },
        error: (err: HttpErrorResponse) => { this.loading = false; this.error = this.errorMessage(err, 'Account created, but automatic login failed. Please log in.'); void this.router.navigateByUrl('/login'); }
      }),
      error: (err: HttpErrorResponse) => { this.loading = false; this.error = this.errorMessage(err, 'Registration failed. Please try again.'); }
    });
  }
  private errorMessage(err: HttpErrorResponse, fallback: string): string {
    const detail = err.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((item: { msg?: string }) => item.msg ?? '').filter(Boolean).join(' ');
    return err.status === 0 ? 'Cannot reach the backend. Start FastAPI at http://127.0.0.1:8000 and check CORS.' : fallback;
  }
}
