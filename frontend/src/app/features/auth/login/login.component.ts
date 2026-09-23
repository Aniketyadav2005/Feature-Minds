import { Component, OnInit } from '@angular/core';
import { NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';
import { TiltDirective } from '../../../shared/directives/tilt.directive';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [NgIf, FormsModule, RouterLink, TiltDirective],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent implements OnInit {

  email = '';
  password = '';

  showPassword = false;
  loading = false;

  errorMessage: string | null = null;

  returnUrl = '/analyze';

  bannerMessage: string | null = null;

  constructor(
    private auth: AuthService,
    private router: Router,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    const params = this.route.snapshot.queryParamMap;

    this.returnUrl = params.get('returnUrl') ?? '/analyze';

    if (params.get('reason') === 'analyze') {
      this.bannerMessage =
        'Sign in to run the analysis — it only takes a few seconds.';
    }
  }

  submit(): void {
    this.errorMessage = null;

    if (!this.email.trim() || !this.password) {
      this.errorMessage =
        'Please enter your email and password.';
      return;
    }

    this.loading = true;

    this.auth.login(
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
          'Login failed. Please check your email and password.';
      },
    });
  }
}
