import { Component, OnInit } from '@angular/core';

import { NgFor, NgIf } from '@angular/common';

import { ApiService } from '../../core/services/api.service';

import {
  AnalysisResult,
  Metrics
} from '../../core/models/analysis-result.model';


import jsPDF from 'jspdf';

@Component({
  selector: 'app-research',
  standalone: true,
  imports: [NgFor, NgIf],
  templateUrl: './research.component.html',
  styleUrl: './research.component.scss',
})
export class ResearchComponent implements OnInit {

  history: AnalysisResult[] = [];

  metrics: Metrics | null = null;

  loading = true;

  exportingPdf = false;

  constructor(
    private api: ApiService
  ) {}

  // =========================================================
  // INIT
  // =========================================================

  ngOnInit(): void {
    this.reload();
  }

  // =========================================================
  // LOAD DATA
  // =========================================================

  reload(): void {

    this.loading = true;

    this.api.getHistory('all').subscribe({
      next: (history) => {
        this.history = history;
        this.loading = false;
      },
      error: () => {
        this.history = [];
        this.loading = false;
      },
    });

    this.loadMetrics();
  }

  loadMetrics(): void {

    this.api.getMetrics().subscribe({
      next: (metrics) => {
        this.metrics = metrics;
      },
      error: () => {
        this.metrics = null;
      },
    });
  }

  // =========================================================
  // GROUND TRUTH
  // =========================================================

  label(
    result: AnalysisResult,
    value: 'hate' | 'safe'
  ): void {

    this.api
      .setGroundTruth(result.id, value)
      .subscribe({
        next: () => {

          result.ground_truth_label = value;

          this.loadMetrics();
        },

        error: (err) => {

          console.error(
            'Ground truth update failed:',
            err
          );

          alert(
            'Could not save the ground-truth label. Please try again.'
          );
        },
      });
  }

  // =========================================================
  // RESEARCH METRICS PDF
  // =========================================================

  exportMetricsPdf(): void {

    if (!this.metrics) {

      alert(
        'Please label at least one image before exporting the research metrics PDF.'
      );

      return;
    }

    if (this.exportingPdf) {
      return;
    }

    this.exportingPdf = true;

    try {

      const m = this.metrics;

      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      });

      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();

      // =====================================================
      // HEADER
      // =====================================================

      pdf.setFillColor(31, 20, 61);

      pdf.rect(
        0,
        0,
        pageWidth,
        32,
        'F'
      );

      pdf.setTextColor(255, 255, 255);

      pdf.setFont(
        'helvetica',
        'bold'
      );

      pdf.setFontSize(20);

      pdf.text(
        'Meme Hate Speech Detector',
        15,
        13
      );

      pdf.setFontSize(11);

      pdf.setFont(
        'helvetica',
        'normal'
      );

      pdf.text(
        'Research Metrics Report',
        15,
        21
      );

      pdf.setFontSize(8);

      pdf.text(
        `Generated: ${new Date().toLocaleString()}`,
        pageWidth - 15,
        21,
        {
          align: 'right',
        }
      );

      // =====================================================
      // TITLE
      // =====================================================

      pdf.setTextColor(35, 25, 55);

      pdf.setFont(
        'helvetica',
        'bold'
      );

      pdf.setFontSize(17);

      pdf.text(
        'Model Performance Evaluation',
        15,
        45
      );

      pdf.setFont(
        'helvetica',
        'normal'
      );

      pdf.setFontSize(9);

      pdf.setTextColor(90, 90, 100);

      pdf.text(
        `Based on ${m.labelled_count} ground-truth labelled image(s)`,
        15,
        52
      );

      // =====================================================
      // METRIC CARDS
      // =====================================================

      const cards = [
        {
          label: 'Accuracy',
          value: m.accuracy,
        },
        {
          label: 'Precision',
          value: m.precision,
        },
        {
          label: 'Recall',
          value: m.recall,
        },
        {
          label: 'F1 Score',
          value: m.f1_score,
        },
      ];

      const cardWidth = 42;
      const cardHeight = 27;
      const gap = 5;

      cards.forEach((card, index) => {

        const x =
          15 + index * (cardWidth + gap);

        const y = 62;

        pdf.setFillColor(
          248,
          246,
          252
        );

        pdf.setDrawColor(
          220,
          215,
          230
        );

        pdf.roundedRect(
          x,
          y,
          cardWidth,
          cardHeight,
          3,
          3,
          'FD'
        );

        pdf.setTextColor(
          90,
          85,
          105
        );

        pdf.setFontSize(8);

        pdf.setFont(
          'helvetica',
          'normal'
        );

        pdf.text(
          card.label,
          x + cardWidth / 2,
          y + 9,
          {
            align: 'center',
          }
        );

        pdf.setTextColor(
          35,
          25,
          55
        );

        pdf.setFontSize(15);

        pdf.setFont(
          'helvetica',
          'bold'
        );

        pdf.text(
          Number(card.value).toFixed(4),
          x + cardWidth / 2,
          y + 20,
          {
            align: 'center',
          }
        );
      });

      // =====================================================
      // CONFUSION MATRIX
      // =====================================================

      pdf.setTextColor(
        35,
        25,
        55
      );

      pdf.setFont(
        'helvetica',
        'bold'
      );

      pdf.setFontSize(13);

      pdf.text(
        'Confusion Matrix',
        15,
        108
      );

      pdf.setFont(
        'helvetica',
        'normal'
      );

      pdf.setFontSize(9);

      pdf.setTextColor(
        100,
        95,
        110
      );

      pdf.text(
        'Comparison between model predictions and actual ground truth.',
        15,
        115
      );

      const tableX = 15;
      const tableY = 122;

      const col1 = 50;
      const col2 = 57;
      const col3 = 57;

      const rowHeight = 16;

      // Header

      pdf.setFillColor(
        42,
        30,
        75
      );

      pdf.setTextColor(
        255,
        255,
        255
      );

      pdf.setFont(
        'helvetica',
        'bold'
      );

      pdf.setFontSize(8);

      pdf.rect(
        tableX,
        tableY,
        col1,
        rowHeight,
        'F'
      );

      pdf.rect(
        tableX + col1,
        tableY,
        col2,
        rowHeight,
        'F'
      );

      pdf.rect(
        tableX + col1 + col2,
        tableY,
        col3,
        rowHeight,
        'F'
      );

      pdf.text(
        'Actual / Predicted',
        tableX + col1 / 2,
        tableY + 10,
        {
          align: 'center',
        }
      );

      pdf.text(
        'Predicted HATE',
        tableX + col1 + col2 / 2,
        tableY + 10,
        {
          align: 'center',
        }
      );

      pdf.text(
        'Predicted SAFE',
        tableX + col1 + col2 + col3 / 2,
        tableY + 10,
        {
          align: 'center',
        }
      );

      // Body rows

      const rows = [
        [
          'Actual HATE',
          `TP = ${m.tp}`,
          `FN = ${m.fn}`,
        ],
        [
          'Actual SAFE',
          `FP = ${m.fp}`,
          `TN = ${m.tn}`,
        ],
      ];

      rows.forEach((row, rowIndex) => {

        const y =
          tableY +
          rowHeight +
          rowIndex * rowHeight;

        pdf.setFillColor(
          rowIndex % 2 === 0
            ? 249
            : 243,
          rowIndex % 2 === 0
            ? 248
            : 241,
          252
        );

        pdf.setDrawColor(
          220,
          215,
          225
        );

        pdf.rect(
          tableX,
          y,
          col1,
          rowHeight,
          'FD'
        );

        pdf.rect(
          tableX + col1,
          y,
          col2,
          rowHeight,
          'FD'
        );

        pdf.rect(
          tableX + col1 + col2,
          y,
          col3,
          rowHeight,
          'FD'
        );

        pdf.setTextColor(
          45,
          40,
          55
        );

        pdf.setFont(
          'helvetica',
          'bold'
        );

        pdf.text(
          row[0],
          tableX + col1 / 2,
          y + 10,
          {
            align: 'center',
          }
        );

        pdf.setFont(
          'helvetica',
          'normal'
        );

        pdf.text(
          row[1],
          tableX + col1 + col2 / 2,
          y + 10,
          {
            align: 'center',
          }
        );

        pdf.text(
          row[2],
          tableX + col1 + col2 + col3 / 2,
          y + 10,
          {
            align: 'center',
          }
        );
      });

      // =====================================================
      // INTERPRETATION
      // =====================================================

      pdf.setTextColor(
        35,
        25,
        55
      );

      pdf.setFont(
        'helvetica',
        'bold'
      );

      pdf.setFontSize(13);

      pdf.text(
        'Metric Interpretation',
        15,
        180
      );

      pdf.setFont(
        'helvetica',
        'normal'
      );

      pdf.setFontSize(9);

      const explanations = [
        [
          'Accuracy',
          'Percentage of all labelled images classified correctly.',
        ],
        [
          'Precision',
          'Among images predicted as hateful, the fraction that were actually hateful.',
        ],
        [
          'Recall',
          'Among actually hateful images, the fraction detected by the model.',
        ],
        [
          'F1 Score',
          'Harmonic mean of Precision and Recall.',
        ],
      ];

      let explanationY = 189;

      explanations.forEach(
        ([title, description]) => {

          pdf.setFont(
            'helvetica',
            'bold'
          );

          pdf.setTextColor(
            55,
            45,
            70
          );

          pdf.text(
            `${title}:`,
            15,
            explanationY
          );

          pdf.setFont(
            'helvetica',
            'normal'
          );

          pdf.setTextColor(
            90,
            85,
            100
          );

          const lines = pdf.splitTextToSize(
            description,
            150
          );

          pdf.text(
            lines,
            39,
            explanationY
          );

          explanationY +=
            10 + lines.length * 3;
        }
      );

      // =====================================================
      // DATA SUMMARY
      // =====================================================

      const total =
        Number(m.tp) +
        Number(m.tn) +
        Number(m.fp) +
        Number(m.fn);

      const correct =
        Number(m.tp) +
        Number(m.tn);

      const incorrect =
        Number(m.fp) +
        Number(m.fn);

      pdf.setFillColor(
        246,
        243,
        250
      );

      pdf.roundedRect(
        15,
        238,
        180,
        30,
        4,
        4,
        'F'
      );

      pdf.setTextColor(
        50,
        40,
        65
      );

      pdf.setFont(
        'helvetica',
        'bold'
      );

      pdf.setFontSize(10);

      pdf.text(
        'Evaluation Summary',
        22,
        248
      );

      pdf.setFont(
        'helvetica',
        'normal'
      );

      pdf.setFontSize(9);

      pdf.text(
        `Total labelled images: ${total}`,
        22,
        257
      );

      pdf.text(
        `Correct predictions: ${correct}`,
        85,
        257
      );

      pdf.text(
        `Incorrect predictions: ${incorrect}`,
        145,
        257
      );

      // =====================================================
      // FOOTER
      // =====================================================

      pdf.setDrawColor(
        220,
        215,
        225
      );

      pdf.line(
        15,
        pageHeight - 18,
        pageWidth - 15,
        pageHeight - 18
      );

      pdf.setTextColor(
        120,
        115,
        125
      );

      pdf.setFontSize(8);

      pdf.text(
        'Meme Hate Speech Detector • Research Metrics',
        15,
        pageHeight - 10
      );

      pdf.text(
        'Generated locally',
        pageWidth - 15,
        pageHeight - 10,
        {
          align: 'right',
        }
      );

      // =====================================================
      // SAVE
      // =====================================================

      pdf.save(
        `research-metrics-${new Date()
          .toISOString()
          .slice(0, 10)}.pdf`
      );

    } catch (error) {

      console.error(
        'Research metrics PDF export failed:',
        error
      );

      alert(
        'Could not create the research metrics PDF. Please try again.'
      );

    } finally {

      this.exportingPdf = false;
    }
  }
}