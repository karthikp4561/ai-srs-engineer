import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ProjectService } from '../../services/project';

@Component({
  selector: 'app-new-project',
  standalone: true,
  imports: [FormsModule, RouterLink, CommonModule],
  templateUrl: './new-project.html',
  styleUrl: './new-project.css'
})
export class NewProject {
  title = '';
  description = '';
  errorMessage = '';
  isLoading = false;

  constructor(
    private projectService: ProjectService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  onSubmit() {
    this.errorMessage = '';
    this.isLoading = true;

    this.projectService.createProject({ title: this.title, description: this.description }).subscribe({
      next: () => {
        this.isLoading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Failed to create project.';
        this.cdr.detectChanges();
      }
    });
  }
}