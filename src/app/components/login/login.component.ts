import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  loginForm: FormGroup;
  hidePassword = true;
  isLoading = false;
  returnUrl = '/';

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private toastr: ToastrService
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]]
    });

    // Get return url from route parameters or default to '/'
    this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/workspace';

    // If already logged in, redirect
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/workspace']);
    }
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.toastr.warning('Please enter a valid email and password.', 'Validation Warning');
      return;
    }

    this.isLoading = true;
    const { email, password } = this.loginForm.value;

    this.authService.login(email, password).subscribe({
      next: (user) => {
        this.isLoading = false;
        this.toastr.success(`Welcome back, ${user.name}!`, 'Authentication Successful');
        this.router.navigateByUrl(this.returnUrl);
      },
      error: (error) => {
        this.isLoading = false;
        this.toastr.error(error.message || 'Login failed', 'Authentication Error');
      }
    });
  }

  // Pre-fill login info for demo convenience
  fillDemoCredentials(role: 'admin' | 'manager'): void {
    if (role === 'admin') {
      this.loginForm.patchValue({
        email: 'cmo@aimarketing.com',
        password: 'password123'
      });
    } else {
      this.loginForm.patchValue({
        email: 'manager@aimarketing.com',
        password: 'password123'
      });
    }
    this.toastr.info('Demo credentials pre-filled.', 'Demo Mode');
  }
}
