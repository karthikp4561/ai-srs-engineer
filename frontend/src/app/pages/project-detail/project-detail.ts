import { Component, ChangeDetectorRef, OnInit, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ProjectService, Project, AnalysisResult, DiagramResult, ApiSpecResult, TechStackResult, PlanningResult } from '../../services/project';
import mermaid from 'mermaid';

@Component({
  selector: 'app-project-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './project-detail.html',
  styleUrl: './project-detail.css'
})
export class ProjectDetail implements OnInit {
  project: Project | null = null;
  analysis: AnalysisResult | null = null;
  diagrams: DiagramResult | null = null;
  apiSpec: ApiSpecResult | null = null;
  techStack: TechStackResult | null = null;
  planning: PlanningResult | null = null;
  isLoading = true;
  isAnalyzing = false;
  isGeneratingDiagrams = false;
  isGeneratingApiSpec = false;
  isGeneratingTechStack = false;
  isGeneratingPlanning = false;
  errorMessage = '';
  diagramsRendered = false;
  isExportingPdf = false;
  isExportingDocx = false;

  constructor(
    private route: ActivatedRoute,
    private projectService: ProjectService,
    private cdr: ChangeDetectorRef
  ) {
    mermaid.initialize({ startOnLoad: false, theme: 'neutral' });
  }

  ngOnInit() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.loadProject(id);
  }

  loadProject(id: number) {
    this.isLoading = true;
    this.projectService.getProject(id).subscribe({
      next: (data) => {
        this.project = data;
        this.parseAnalysis();
        this.parseDiagrams();
        this.parseApiSpec();
        this.parseTechStack();
        this.parsePlanning();
        this.isLoading = false;
        this.cdr.detectChanges();
        this.renderDiagrams();
      },
      error: () => {
        this.errorMessage = 'Could not load project.';
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  parseAnalysis() {
    if (this.project?.analysis_json) {
      this.analysis = JSON.parse(this.project.analysis_json);
    }
  }

  parseDiagrams() {
    if (this.project?.diagrams_json) {
      this.diagrams = JSON.parse(this.project.diagrams_json);
    }
  }

  parseApiSpec() {
  if (this.project?.api_spec_json) {
    this.apiSpec = JSON.parse(this.project.api_spec_json);
  }
}

  runAnalysis() {
    if (!this.project) return;
    this.isAnalyzing = true;
    this.errorMessage = '';

    this.projectService.analyzeProject(this.project.id).subscribe({
      next: (data) => {
        this.project = data;
        this.parseAnalysis();
        this.isAnalyzing = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.isAnalyzing = false;
        this.errorMessage = this.extractErrorMessage(err);
        this.cdr.detectChanges();
      }
    });
  }

  runDiagramGeneration() {
    if (!this.project) return;
    this.isGeneratingDiagrams = true;
    this.errorMessage = '';

    this.projectService.generateDiagrams(this.project.id).subscribe({
      next: (data) => {
        this.project = data;
        this.parseDiagrams();
        this.isGeneratingDiagrams = false;
        this.cdr.detectChanges();
        setTimeout(() => this.renderDiagrams(), 0);
      },
      error: (err) => {
        this.isGeneratingDiagrams = false;
        this.errorMessage = this.extractErrorMessage(err);
        this.cdr.detectChanges();
      }
    });
  }

  runApiSpecGeneration() {
  if (!this.project) return;
  this.isGeneratingApiSpec = true;
  this.errorMessage = '';

  this.projectService.generateApiSpec(this.project.id).subscribe({
    next: (data) => {
      this.project = data;
      this.parseApiSpec();
      this.isGeneratingApiSpec = false;
      this.cdr.detectChanges();
    },
    error: (err) => {
      this.isGeneratingApiSpec = false;
      this.errorMessage = this.extractErrorMessage(err);
      this.cdr.detectChanges();
    }
  });
}

parseTechStack() {
  if (this.project?.tech_stack_json) {
    this.techStack = JSON.parse(this.project.tech_stack_json);
  }
}

runTechStackGeneration() {
  if (!this.project) return;
  this.isGeneratingTechStack = true;
  this.errorMessage = '';

  this.projectService.generateTechStack(this.project.id).subscribe({
    next: (data) => {
      this.project = data;
      this.parseTechStack();
      this.isGeneratingTechStack = false;
      this.cdr.detectChanges();
    },
    error: (err) => {
      this.isGeneratingTechStack = false;
      this.errorMessage = this.extractErrorMessage(err);
      this.cdr.detectChanges();
    }
  });
}

  private async renderDiagrams() {
    if (!this.diagrams) return;

    const targets: { id: string; code: string }[] = [
      { id: 'use-case-diagram', code: this.diagrams.use_case_diagram },
      { id: 'class-diagram', code: this.diagrams.class_diagram },
      { id: 'er-diagram', code: this.diagrams.er_diagram },
    ];

    for (const t of targets) {
      const el = document.getElementById(t.id);
      if (!el) continue;
      try {
        const { svg } = await mermaid.render(t.id + '-svg', t.code);
        el.innerHTML = svg;
      } catch (e) {
        el.innerHTML = `<p class="diagram-error">Could not render this diagram.</p>`;
        console.error('Mermaid render error:', e);
      }
    }
  }

  private extractErrorMessage(err: any): string {
    const detail = err.error?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((d: any) => d.msg).join(', ');
    }
    return 'Something went wrong. Please try again.';
  }

  parsePlanning() {
  if (this.project?.planning_json) {
    this.planning = JSON.parse(this.project.planning_json);
  }
}

runPlanningGeneration() {
  if (!this.project) return;
  this.isGeneratingPlanning = true;
  this.errorMessage = '';

  this.projectService.generatePlanning(this.project.id).subscribe({
    next: (data) => {
      this.project = data;
      this.parsePlanning();
      this.isGeneratingPlanning = false;
      this.cdr.detectChanges();
    },
    error: (err) => {
      this.isGeneratingPlanning = false;
      this.errorMessage = this.extractErrorMessage(err);
      this.cdr.detectChanges();
    }
  });
}

impactClass(impact: string): string {
  const i = impact.toLowerCase();
  if (i === 'high') return 'impact-high';
  if (i === 'medium') return 'impact-medium';
  return 'impact-low';
}

exportPdf() {
  if (!this.project) return;
  this.isExportingPdf = true;
  this.projectService.downloadExport(this.project.id, 'pdf', this.project.title);
  setTimeout(() => { this.isExportingPdf = false; this.cdr.detectChanges(); }, 1500);
}

exportDocx() {
  if (!this.project) return;
  this.isExportingDocx = true;
  this.projectService.downloadExport(this.project.id, 'docx', this.project.title);
  setTimeout(() => { this.isExportingDocx = false; this.cdr.detectChanges(); }, 1500);
}
}

