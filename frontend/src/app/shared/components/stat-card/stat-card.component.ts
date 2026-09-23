import { Component, Input } from '@angular/core';
import { TiltDirective } from '../../directives/tilt.directive';

@Component({
  selector: 'app-stat-card',
  standalone: true,
  imports: [TiltDirective],
  template: `
    <div class="stat-card card" appTilt [tiltMax]="10" [tiltScale]="1.03">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-value">{{ value }}</div>
    </div>
  `,
  styleUrl: './stat-card.component.scss',
})
export class StatCardComponent {
  @Input({ required: true }) label = '';
  @Input({ required: true }) value: string | number = '';
}