import { Component, Input } from '@angular/core';
import { NgClass, NgIf, UpperCasePipe } from '@angular/common';

@Component({
  selector: 'app-badge',
  standalone: true,
  imports: [NgClass, NgIf, UpperCasePipe],
  template: `
    <span class="badge" [ngClass]="isHate ? 'badge-hate' : 'badge-safe'">
      {{ isHate ? '🚨 HATEFUL' : '✅ SAFE' }}
    </span>
    <span *ngIf="isHate && category && category !== 'none'" class="category-pill">
      {{ category | uppercase }}
    </span>
  `,
  styleUrl: './badge.component.scss',
})
export class BadgeComponent {
  @Input({ required: true }) isHate = false;
  @Input() category: string | null = null;
}
