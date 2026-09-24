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

export interface DiagramResult {
  use_case_diagram: string;
  class_diagram: string;
  er_diagram: string;
}

export interface ApiEndpoint {
  method: string;
  path: string;
  description: string;
  request_body: any;
  response_body: any;
}

export interface ApiSpecResult {
  endpoints: ApiEndpoint[];
}

export interface TechRecommendation {
  technology: string;
  reason: string;
}

export interface TechStackResult {
  frontend: TechRecommendation;
  backend: TechRecommendation;
  database: TechRecommendation;
  cloud_deployment: TechRecommendation;
  third_party_integrations: TechRecommendation[];
}

export interface Project {
  id: number;
  title: string;
  description: string;
  status: string;
  analysis_json: string | null;
  diagrams_json: string | null;
  api_spec_json: string | null;
  tech_stack_json: string | null;
  planning_json: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  title: string;
  description: string;
}

export interface ProjectPhase {
  name: string;
  duration_weeks: number;
  description: string;
}

export interface Sprint {
  name: string;
  duration_weeks: number;
  goals: string[];
}

export interface Milestone {
  name: string;
  description: string;
}

export interface Risk {
  risk: string;
  impact: string;
  mitigation: string;
}

export interface PlanningResult {
  estimated_duration_weeks: number;
  phases: ProjectPhase[];
  sprints: Sprint[];
  milestones: Milestone[];
  risks: Risk[];
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

  generateDiagrams(id: number): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/${id}/diagrams`, {});
  }

  generateApiSpec(id: number): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/${id}/api-spec`, {});
  }

  generateTechStack(id: number): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/${id}/tech-stack`, {});
  }

  generatePlanning(id: number): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/${id}/planning`, {});
  }

  getExportUrl(id: number, format: 'pdf' | 'docx'): string {
    return `${this.apiUrl}/${id}/export/${format}`;
  }

  downloadExport(id: number, format: 'pdf' | 'docx', title: string): void {
    const token = localStorage.getItem('access_token');
    fetch(this.getExportUrl(id, format), {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('Export failed');
        return res.blob();
      })
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title.replace(/\s+/g, '_')}_SRS.${format}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      })
      .catch(err => console.error('Download failed', err));
  }
}


