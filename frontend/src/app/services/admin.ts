import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AdminUser {
  id: number;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AdminProject {
  id: number;
  title: string;
  status: string;
  owner_email: string;
  created_at: string;
}

export interface AnalyticsSummary {
  total_users: number;
  total_projects: number;
  active_users: number;
  projects_by_status: { [key: string]: number };
  ai_calls_by_action: { [key: string]: number };
  ai_calls_last_7_days: number;
}

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private apiUrl = 'http://127.0.0.1:8000/admin';

  constructor(private http: HttpClient) {}

  getUsers(): Observable<AdminUser[]> {
    return this.http.get<AdminUser[]>(`${this.apiUrl}/users`);
  }

  toggleUserActive(id: number): Observable<AdminUser> {
    return this.http.put<AdminUser>(`${this.apiUrl}/users/${id}/toggle-active`, {});
  }

  deleteUser(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/users/${id}`);
  }

  getProjects(): Observable<AdminProject[]> {
    return this.http.get<AdminProject[]>(`${this.apiUrl}/projects`);
  }

  getAnalytics(): Observable<AnalyticsSummary> {
    return this.http.get<AnalyticsSummary>(`${this.apiUrl}/analytics`);
  }
}