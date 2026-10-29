import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { BusinessCreateRequest } from '../../core/services/api.service';
import { PlatformService } from '../../core/services/platform.service';

@Component({ selector: 'app-business-setup', standalone: true, imports: [CommonModule, ReactiveFormsModule, RouterLink], templateUrl: './business-setup.component.html', styleUrl: '../auth/auth.component.css' })
export class BusinessSetupComponent {
  error = '';
  loading = false;
  form;
  constructor(private fb: FormBuilder, public platform: PlatformService, private router: Router) {
    this.form = this.fb.nonNullable.group({
      name: ['', [Validators.required, Validators.minLength(2)]], category: ['Bakery', Validators.required],
      email: [this.platform.user?.email ?? '', [Validators.required, Validators.email]], phone: ['', Validators.required],
      address: ['', Validators.required], city: ['', Validators.required], state: ['', Validators.required],
      country: ['India', Validators.required], pincode: ['', Validators.required], description: [''], website: ['']
    });
  }
  submit(): void {
    this.error = '';
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const v = this.form.getRawValue();
    const payload: BusinessCreateRequest = {
      business_name: v.name.trim(), business_type: v.category, email: v.email.trim(), phone: v.phone.trim(),
      address: v.address.trim(), city: v.city.trim(), state: v.state.trim(), country: v.country.trim(), pincode: v.pincode.trim(),
      description: v.description.trim() || null, website: v.website.trim() || null
    };
    this.loading = true;
    this.platform.addBusiness(payload).subscribe({
      next: () => { this.loading = false; void this.router.navigateByUrl('/dashboard'); },
      error: (err: HttpErrorResponse) => {
        this.loading = false;
        const detail = err.error?.detail;
        this.error = typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail.map((x: { msg?: string }) => x.msg ?? '').join(' ') : (err.status === 0 ? 'Cannot reach the backend. Start FastAPI at http://127.0.0.1:8000 and check CORS.' : 'Business creation failed. Check the details and try again.'));
      }
    });
  }
}
