import { Routes } from '@angular/router';
import { Login } from './pages/login/login';
import { Register } from './pages/register/register';
import { Dashboard } from './pages/dashboard/dashboard';
import { NewProject } from './pages/new-project/new-project';
import { ProjectDetail } from './pages/project-detail/project-detail';
import { authGuard } from './guards/auth-guard';
import { Admin } from './pages/admin/admin';

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'register', component: Register },
  { path: 'dashboard', component: Dashboard, canActivate: [authGuard] },
  { path: 'new-project', component: NewProject, canActivate: [authGuard] },
  { path: 'projects/:id', component: ProjectDetail, canActivate: [authGuard] },
  { path: 'admin', component: Admin, canActivate: [authGuard] },
];