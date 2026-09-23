import { Component, OnInit } from '@angular/core';
import { NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { TiltDirective } from '../../shared/directives/tilt.directive';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [NgIf, FormsModule, RouterLink, TiltDirective],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss',
})
export class RegisterComponent implements OnInit {

  name = '';
  email = '';
  password = '';
  confirmPassword = '';

  showPassword = false;
  loading = false;

  errorMessage: string | null = null;

  returnUrl = '/analyze';

  constructor(
    private auth: AuthService,
    private router: Router,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    this.returnUrl =
      this.route.snapshot.queryParamMap.get('returnUrl') ?? '/analyze';
  }

  submit(): void {
    this.errorMessage = null;

    if (
      !this.name.trim() ||
      !this.email.trim() ||
      !this.password
    ) {
      this.errorMessage = 'Please fill in all fields.';
      return;
    }

    if (this.password.length < 6) {
      this.errorMessage =
        'Password must be at least 6 characters.';
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.errorMessage =
        'Passwords do not match.';
      return;
    }

    this.loading = true;

    this.auth.register(
      this.name.trim(),
      this.email.trim(),
      this.password
    ).subscribe({
      next: () => {
        this.loading = false;

        this.router.navigateByUrl(this.returnUrl);
      },

      error: (err) => {
        this.loading = false;

        this.errorMessage =
          err?.error?.detail ??
          'Registration failed. Please try again.';
      },
    });
  }
}
