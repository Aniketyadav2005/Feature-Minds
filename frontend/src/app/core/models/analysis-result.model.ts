export interface AnalysisResult {
  id: number;
  filename: string;
  source: 'upload' | 'url';
  timestamp: string;
  extracted_text: string;
  caption: string;
  label: 'hate' | 'nothate';
  is_hate: boolean;
  hate_score: number;
  safe_score: number;
  category: string;
  threshold_used: number;
  image_url: string | null;
  blurred_image_url: string | null;
  has_image: boolean;
  ground_truth_label: 'hate' | 'safe' | null;
}

export interface HistoryStats {
  total: number;
  hate_count: number;
  safe_count: number;
  avg_hate_score: number;
  category_breakdown: Record<string, number>;
  timeline: { timestamp: string; hate_score: number }[];
}

export interface Metrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  tp: number;
  fp: number;
  fn: number;
  tn: number;
  labelled_count: number;
}

export type HistoryFilter = 'all' | 'hate' | 'safe';

export const CATEGORY_COLORS: Record<string, string> = {
  racism: '#e57373',
  sexism: '#f06292',
  religion: '#ffb74d',
  homophobia: '#ce93d8',
  violence: '#ef5350',
  general: '#90a4ae',
  none: '#4caf7d',
};
