import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AnalysisResult {
  objectives: string[];
  scope: string;
  target_users: string[];
  functional_requirements: string[];
  non_functional_requirements: string[];
  constraints: string[];
  assumptions: string[];
}

export interface Project {
  id: number;
  title: string;
  description: string;
  status: string;
  analysis_json: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  title: string;
  description: string;
}

@Injectable({
  providedIn: 'root'
})
export class ProjectService {
  private apiUrl = 'http://127.0.0.1:8000/projects';

  constructor(private http: HttpClient) {}

  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(`${this.apiUrl}/`);
  }

  getProject(id: number): Observable<Project> {
    return this.http.get<Project>(`${this.apiUrl}/${id}`);
  }

  createProject(payload: ProjectCreate): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/`, payload);
  }

  deleteProject(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  analyzeProject(id: number): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/${id}/analyze`, {});
  }
}