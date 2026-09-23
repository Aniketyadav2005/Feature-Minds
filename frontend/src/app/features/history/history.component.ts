import { Component, OnInit } from '@angular/core';
import { NgFor, NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';

import { ApiService } from '../../core/services/api.service';
import {
  AnalysisResult, CATEGORY_COLORS, HistoryFilter, HistoryStats,
} from '../../core/models/analysis-result.model';
import { ResultCardComponent } from '../../shared/components/result-card/result-card.component';
import { StatCardComponent } from '../../shared/components/stat-card/stat-card.component';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [NgFor, NgIf, FormsModule, BaseChartDirective, ResultCardComponent, StatCardComponent],
  templateUrl: './history.component.html',
  styleUrl: './history.component.scss',
})
export class HistoryComponent implements OnInit {
  history: AnalysisResult[] = [];
  stats: HistoryStats | null = null;
  filter: HistoryFilter = 'all';
  loading = true;

  // Pie: hate vs safe split
  pieData: ChartData<'doughnut'> = { labels: [], datasets: [{ data: [] }] };
  pieOptions: ChartConfiguration<'doughnut'>['options'] = {
    plugins: { legend: { labels: { color: '#e0e0e0' } } },
  };

  // Bar: hate category breakdown
  barData: ChartData<'bar'> = { labels: [], datasets: [{ data: [], label: 'Count' }] };
  barOptions: ChartConfiguration<'bar'>['options'] = {
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#e0e0e0' }, grid: { color: '#2a2a3b' } },
      y: { ticks: { color: '#e0e0e0' }, grid: { color: '#2a2a3b' }, beginAtZero: true },
    },
  };

  // Line: hate score over time
  lineData: ChartData<'line'> = { labels: [], datasets: [{ data: [], label: 'Hate score' }] };
  lineOptions: ChartConfiguration<'line'>['options'] = {
    plugins: { legend: { labels: { color: '#e0e0e0' } } },
    scales: {
      x: { ticks: { color: '#e0e0e0' }, grid: { color: '#2a2a3b' } },
      y: {
        ticks: { color: '#e0e0e0' }, grid: { color: '#2a2a3b' },
        beginAtZero: true, max: 100,
      },
    },
  };

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading = true;
    this.api.getHistory(this.filter).subscribe((h) => {
      this.history = h;
      this.loading = false;
    });
    this.api.getHistoryStats().subscribe((stats) => {
      this.stats = stats;
      this.buildCharts(stats);
    });
  }

  setFilter(f: HistoryFilter): void {
    this.filter = f;
    this.reload();
  }

  private buildCharts(stats: HistoryStats): void {
    this.pieData = {
      labels: ['Hateful', 'Safe'],
      datasets: [{ data: [stats.hate_count, stats.safe_count], backgroundColor: ['#e05252', '#4caf7d'] }],
    };
    

    const categoryEntries = Object.entries(
      stats.category_breakdown ?? {}
    );

    const categoryLabels = categoryEntries.map(
      ([category]) => category
    );

    const categoryValues = categoryEntries.map(
      ([, count]) => count
    );

    // Safe analyses do not have a hate category.
    // Show them explicitly instead of leaving the chart empty.
    if (stats.safe_count > 0) {
      categoryLabels.push('No Hate Category');
      categoryValues.push(stats.safe_count);
    }

    this.barData = {
      labels: categoryLabels,
      datasets: [
        {
          data: categoryValues,
          label: 'Count',
        },
      ],
    };

    this.lineData = {
      labels: stats.timeline.map((t) => new Date(t.timestamp).toLocaleString()),
      datasets: [{
        data: stats.timeline.map((t) => t.hate_score),
        label: 'Hate score',
        borderColor: '#e05252',
        pointBackgroundColor: '#e05252',
        tension: 0.2,
      }],
    };
  }

  deleteItem(id: number): void {
    this.api.deleteHistoryItem(id).subscribe(() => this.reload());
  }

  clearAll(): void {
    if (!confirm('Clear all history? This cannot be undone.')) return;
    this.api.clearHistory().subscribe(() => this.reload());
  }

downloadPdf(): void {
  this.api.exportHistoryPdf().subscribe({
    next: (blob: Blob) => {
      const url = window.URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.download = 'meme-history.pdf';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      window.URL.revokeObjectURL(url);
    },

    error: (err: any) => {
      console.error(
        'History PDF export failed:',
        err
      );

      alert(
        err?.error?.detail ??
        'Could not export history PDF. Please try again.'
      );
    },
  });
}
}
