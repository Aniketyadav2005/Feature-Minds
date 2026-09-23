import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

import {
  AnalysisResult,
  HistoryFilter,
  HistoryStats,
  Metrics,
} from '../models/analysis-result.model';

/**
 * Thin wrapper around the FastAPI backend.
 *
 * Current API:
 * - Image upload analysis
 * - History
 * - Research / metrics
 * - PDF export
 *
 * URL analysis and CSV export have been removed.
 */
@Injectable({
  providedIn: 'root',
})
export class ApiService {

  private readonly base = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  // =========================================================
  // ANALYZE
  // =========================================================

  analyzeUpload(
    files: File[],
    thresholdPct: number,
    ocrLangs: string[],
  ): Observable<AnalysisResult[]> {

    const form = new FormData();

    files.forEach((file) => {
      form.append(
        'files',
        file,
        file.name
      );
    });

    form.append(
      'threshold_pct',
      String(thresholdPct)
    );

    // Backend currently accepts one OCR language.
    form.append(
      'ocr_lang',
      ocrLangs[0] ?? ''
    );

    return this.http.post<AnalysisResult[]>(
      `${this.base}/analyze/upload`,
      form
    );
  }


  // =========================================================
  // HISTORY
  // =========================================================

  getHistory(
    filter: HistoryFilter = 'all'
  ): Observable<AnalysisResult[]> {

    return this.http.get<AnalysisResult[]>(
      `${this.base}/history`,
      {
        params: {
          filter,
        },
      }
    );
  }


  getHistoryStats(): Observable<HistoryStats> {

    return this.http.get<HistoryStats>(
      `${this.base}/history/stats`
    );
  }


  deleteHistoryItem(
    id: number
  ): Observable<unknown> {

    return this.http.delete(
      `${this.base}/history/${id}`
    );
  }


  clearHistory(): Observable<{ deleted: number }> {

    return this.http.delete<{ deleted: number }>(
      `${this.base}/history`
    );
  }


  // =========================================================
  // RESEARCH
  // =========================================================

  setGroundTruth(
    analysisId: number,
    label: 'hate' | 'safe'
  ): Observable<unknown> {

    return this.http.post(
      `${this.base}/research/ground-truth`,
      {
        analysis_id: analysisId,
        label,
      }
    );
  }

    /**
   * Export research metrics and ground-truth results as PDF.
   */
  exportMetricsPdf(): Observable<Blob> {

    return this.http.get(
      `${this.base}/export/pdf/research-metrics`,
      {
        responseType: 'blob',
      }
    );
  }


  getMetrics(): Observable<Metrics | null> {

    return this.http.get<Metrics | null>(
      `${this.base}/research/metrics`
    );
  }


    // =========================================================
  // PDF EXPORT
  // =========================================================

  /**
   * Export ONLY the analyses from the current Home-page session.
   */
  exportCurrentAnalysisPdf(
    analysisIds: number[]
  ): Observable<Blob> {

    return this.http.post(
      `${this.base}/export/pdf/batch`,
      {
        analysis_ids: analysisIds,
      },
      {
        responseType: 'blob',
      }
    );
  }


  /**
   * Export ALL analysis history belonging
   * to the logged-in user.
   */
  exportHistoryPdf(): Observable<Blob> {

    return this.http.get(
      `${this.base}/export/pdf/history`,
      {
        responseType: 'blob',
      }
    );
  }


  /**
   * Export one analysis record.
   */
  exportSinglePdf(
    analysisId: number
  ): Observable<Blob> {

    return this.http.get(
      `${this.base}/export/pdf/${analysisId}`,
      {
        responseType: 'blob',
      }
    );
  }
  // =========================================================
// IMAGE URL
// =========================================================

resolveImageUrl(
  path: string | null
): string | null {

  if (!path) {
    return null;
  }

  return `${environment.staticBaseUrl}${path}`;
}
}