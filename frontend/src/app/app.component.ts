import { Component, ElementRef, HostListener } from '@angular/core';
import { NgIf } from '@angular/common';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs/operators';

import { AuthService } from './core/services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [NgIf, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  title = 'Meme Hate Speech Detector';

  isAuthPage = false;
  isProfileOpen = false;

  constructor(public auth: AuthService, private router: Router, private elRef: ElementRef<HTMLElement>) {
    this.isAuthPage = this.matchesAuthPage(this.router.url);

    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd))
      .subscribe((e) => {
        this.isAuthPage = this.matchesAuthPage(e.urlAfterRedirects);
        this.isProfileOpen = false;
      });
  }

  private matchesAuthPage(url: string): boolean {
    return url.startsWith('/login') || url.startsWith('/register');
  }

  toggleProfile(): void {
    this.isProfileOpen = !this.isProfileOpen;
  }

  // Close the dropdown when clicking anywhere outside it.
  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.isProfileOpen) return;
    if (!this.elRef.nativeElement.querySelector('.user-area')?.contains(event.target as Node)) {
      this.isProfileOpen = false;
    }
  }

  logout(): void {
    this.auth.logout();
    this.isProfileOpen = false;
    this.router.navigate(['/login']);
  }
}