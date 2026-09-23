import { Component, EventEmitter, Input, Output } from '@angular/core';
import { DatePipe, NgIf } from '@angular/common';

import { ApiService } from '../../../core/services/api.service';
import { AnalysisResult } from '../../../core/models/analysis-result.model';
import { BadgeComponent } from '../badge/badge.component';
import { TiltDirective } from '../../directives/tilt.directive';

@Component({
  selector: 'app-result-card',
  standalone: true,
  imports: [NgIf, DatePipe, BadgeComponent, TiltDirective],
  templateUrl: './result-card.component.html',
  styleUrl: './result-card.component.scss',
})
export class ResultCardComponent {
  @Input({ required: true }) result!: AnalysisResult;
  /** Show ground-truth labelling buttons (used on the Research tab). */
  @Input() showLabelling = false;
  @Output() labelled = new EventEmitter<'hate' | 'safe'>();

  showOriginal = false;

  constructor(private api: ApiService) {}

  get displayImageUrl(): string | null {
    const path =
      this.result.is_hate && this.result.blurred_image_url
        ? this.result.blurred_image_url
        : this.result.image_url;
    return this.api.resolveImageUrl(path);
  }

  get originalImageUrl(): string | null {
    return this.api.resolveImageUrl(this.result.image_url);
  }

  toggleOriginal(): void {
    this.showOriginal = !this.showOriginal;
  }

  label(value: 'hate' | 'safe'): void {
    this.labelled.emit(value);
  }
}
