import { Component } from '@angular/core';
import { NgFor, NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { AnalysisResult } from '../../core/models/analysis-result.model';

import { ResultCardComponent } from '../../shared/components/result-card/result-card.component';
import { StatCardComponent } from '../../shared/components/stat-card/stat-card.component';

@Component({
  selector: 'app-analyze',
  standalone: true,
  imports: [
    NgFor,
    NgIf,
    FormsModule,
    ResultCardComponent,
    StatCardComponent,
  ],
  templateUrl: './analyze.component.html',
  styleUrl: './analyze.component.scss',
})
export class AnalyzeComponent {

  selectedFiles: File[] = [];

  thresholdPct = 50;

  maxBatch = 1;

  ocrLangOptions: { label: string; code: string }[] = [
    { label: 'English', code: 'en' },
    { label: 'Marathi', code: 'mr' },
    { label: 'Hindi', code: 'hi' },
    // { label: 'Tamil', code: 'ta' },
    // { label: 'Gujarati', code: 'gu' },
    // { label: 'Urdu', code: 'ur' },
    // { label: 'Kannada', code: 'kn' },
  ];

  selectedLangs: string[] = [];

  loading = false;

  errorMessage: string | null = null;

  batchResults: AnalysisResult[] = [];

  constructor(
    private api: ApiService,
    private auth: AuthService,
    private router: Router
  ) {}

  onFilesSelected(event: Event): void {
  const input = event.target as HTMLInputElement;

  if (!input.files) {
    return;
  }

  this.selectedFiles = Array.from(input.files).slice(0, this.maxBatch);

  this.errorMessage = null;
  this.batchResults = [];
}

/**
 * Remove a selected image from the upload list.
 */
removeSelectedFile(index: number): void {
  this.selectedFiles.splice(index, 1);

  this.errorMessage = null;
  this.batchResults = [];
}

  toggleLang(code: string): void {
    if (this.selectedLangs.includes(code)) {
      this.selectedLangs = [];
    } else {
      // Only one OCR language is allowed.
      this.selectedLangs = [code];
    }

    this.errorMessage = null;
  }

  get selectedLanguageNames(): string {
    return this.ocrLangOptions
      .filter((lang) => this.selectedLangs.includes(lang.code))
      .map((lang) => lang.label)
      .join(', ');
  }

  get selectedLanguageCode(): string {
    return this.selectedLangs[0] ?? '';
  }

  private validateOcrLanguage(): boolean {
    if (this.selectedLangs.length === 0) {
      this.errorMessage =
        'Please select an OCR language before analysing the image.';
      return false;
    }

    return true;
  }

  /**
   * Analysis requires authentication.
   * If the user is not logged in, send them to login and return to analyze.
   */
  private requireLogin(): boolean {
    if (this.auth.isLoggedIn()) {
      return true;
    }

    this.router.navigate(['/login'], {
      queryParams: {
        returnUrl: '/analyze',
        reason: 'analyze',
      },
    });

    return false;
  }

  runUploadAnalysis(): void {
    if (!this.selectedFiles.length) {
      this.errorMessage =
        'Please upload at least one image before analysing.';
      return;
    }

    if (!this.validateOcrLanguage()) {
      return;
    }

    if (!this.requireLogin()) {
      return;
    }

    this.loading = true;
    this.errorMessage = null;
    this.batchResults = [];

    this.api
      .analyzeUpload(
        this.selectedFiles,
        this.thresholdPct,
        this.selectedLangs
      )
      .subscribe({
        next: (results: AnalysisResult[]) => {
          this.batchResults = results;
          this.loading = false;
        },

        error: (err: any) => {
          this.errorMessage =
            err?.error?.detail ??
            'Analysis failed. Please try again.';

          this.loading = false;
        },
      });
  }

  get hateCount(): number {
    return this.batchResults.filter((r) => r.is_hate).length;
  }

  get safeCount(): number {
    return this.batchResults.length - this.hateCount;
  }

  /**
   * Open the PDF containing the user's analysis history.
   */
/**
 * Download the PDF containing the user's analysis history.
 */
downloadPdf(): void {
  if (!this.batchResults.length) {
    this.errorMessage =
      'Please analyse at least one meme before exporting the PDF.';
    return;
  }

  const analysisIds = this.batchResults
    .map((result) => result.id)
    .filter((id): id is number => typeof id === 'number');

  if (!analysisIds.length) {
    this.errorMessage =
      'No analysis records are available for PDF export.';
    return;
  }

  this.api.exportCurrentAnalysisPdf(analysisIds).subscribe({
    next: (blob: Blob) => {
      const url = window.URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.download = 'current-meme-analysis.pdf';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      window.URL.revokeObjectURL(url);
    },

    error: (err: any) => {
      console.error(
        'Current analysis PDF export failed:',
        err
      );

      this.errorMessage =
        err?.error?.detail ??
        'Could not export the current analysis PDF. Please try again.';
    },
  });
}
}
