import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AdminService, AdminUser, AdminProject, AnalyticsSummary } from '../../services/admin';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './admin.html',
  styleUrl: './admin.css'
})
export class Admin implements OnInit {
  activeTab: 'overview' | 'users' | 'projects' = 'overview';
  analytics: AnalyticsSummary | null = null;
  users: AdminUser[] = [];
  projects: AdminProject[] = [];
  isLoading = true;
  errorMessage = '';

  constructor(private adminService: AdminService, private cdr: ChangeDetectorRef) {}

  ngOnInit() {
    this.loadAll();
  }

  loadAll() {
    this.isLoading = true;
    this.adminService.getAnalytics().subscribe({
      next: (data) => {
        this.analytics = data;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.errorMessage = err.error?.detail || 'Access denied or failed to load analytics.';
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
    this.adminService.getUsers().subscribe({
      next: (data) => { this.users = data; this.cdr.detectChanges(); }
    });
    this.adminService.getProjects().subscribe({
      next: (data) => { this.projects = data; this.cdr.detectChanges(); }
    });
  }

  setTab(tab: 'overview' | 'users' | 'projects') {
    this.activeTab = tab;
  }

  toggleActive(user: AdminUser) {
    this.adminService.toggleUserActive(user.id).subscribe({
      next: (updated) => {
        user.is_active = updated.is_active;
        this.cdr.detectChanges();
      },
      error: (err) => {
        alert(err.error?.detail || 'Could not update user.');
      }
    });
  }

  removeUser(user: AdminUser) {
    if (!confirm(`Delete ${user.name} (${user.email})? This also deletes their projects.`)) return;
    this.adminService.deleteUser(user.id).subscribe({
      next: () => {
        this.users = this.users.filter(u => u.id !== user.id);
        this.cdr.detectChanges();
      },
      error: (err) => {
        alert(err.error?.detail || 'Could not delete user.');
      }
    });
  }

  actionKeys(): string[] {
    return this.analytics ? Object.keys(this.analytics.ai_calls_by_action) : [];
  }

  statusKeys(): string[] {
    return this.analytics ? Object.keys(this.analytics.projects_by_status) : [];
  }
}
