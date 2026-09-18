import { Component, ChangeDetectorRef, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ProjectService, Project, AnalysisResult } from '../../services/project';

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
  isLoading = true;
  isAnalyzing = false;
  errorMessage = '';

  constructor(
    private route: ActivatedRoute,
    private projectService: ProjectService,
    private cdr: ChangeDetectorRef
  ) {}

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
        this.isLoading = false;
        this.cdr.detectChanges();
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
        this.errorMessage = err.error?.detail || 'Analysis failed. Please try again.';
        this.cdr.detectChanges();
      }
    });
  }
}