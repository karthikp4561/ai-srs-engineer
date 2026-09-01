import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth';
import { ProjectService, Project } from '../../services/project';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class Dashboard implements OnInit {
  projects: Project[] = [];
  sharedProjects: Project[] = [];
  isLoading = true;

  get totalCount(): number { return this.projects.length; }
  get draftCount(): number { return this.projects.filter(p => p.status === 'draft').length; }
  get analyzedCount(): number { return this.projects.filter(p => p.status === 'analyzed').length; }

  constructor(
    private authService: AuthService,
    private projectService: ProjectService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.loadProjects();
    this.loadSharedProjects();
  }

  loadProjects() {
    this.isLoading = true;
    this.projectService.getProjects().subscribe({
      next: (data) => {
        this.projects = data;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadSharedProjects() {
  this.projectService.getSharedProjects().subscribe({
    next: (data) => { this.sharedProjects = data; this.cdr.detectChanges(); },
    error: () => {}
  });
}

  deleteProject(id: number, event: Event) {
    event.stopPropagation();
    if (!confirm('Delete this project?')) return;

    this.projectService.deleteProject(id).subscribe({
      next: () => this.loadProjects()
    });
  }

  openProject(id: number) {
    this.router.navigate(['/projects', id]);
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  get showAdminLink(): boolean {
  return this.authService.isAdmin();
  }
}