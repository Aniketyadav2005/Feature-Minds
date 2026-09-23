import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'analyze', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./features/register/register.component').then((m) => m.RegisterComponent),
  },
  {
    path: 'analyze',
    loadComponent: () =>
      import('./features/analyze/analyze.component').then((m) => m.AnalyzeComponent),
  },
  {
    path: 'history',
    loadComponent: () =>
      import('./features/history/history.component').then((m) => m.HistoryComponent),
  },
  {
    path: 'research',
    loadComponent: () =>
      import('./features/research/research.component').then((m) => m.ResearchComponent),
  },
  { path: '**', redirectTo: 'analyze' },
];