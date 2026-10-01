import { Component, ChangeDetectorRef, OnInit, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ProjectService, Project, AnalysisResult, DiagramResult, ApiSpecResult, TechStackResult, PlanningResult, Collaborator, ProjectVersion, VersionDiff, GitHubConnection, GitHubConnectPayload, SyncResult, TraceabilityMatrixResult, TraceabilityItem } from '../../services/project';
import mermaid from 'mermaid';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-project-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
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
  collaborators: Collaborator[] = [];
  versions: ProjectVersion[] = [];
  selectedFromVersion: number | null = null;
  selectedToVersion: number | null = null;
  versionDiff: VersionDiff | null = null;
  isLoading = true;
  isAnalyzing = false;
  isGeneratingDiagrams = false;
  isGeneratingApiSpec = false;
  isGeneratingTechStack = false;
  isGeneratingPlanning = false;
  isGeneratingTraceability = false;
  traceabilityError = '';
  traceabilityFilter: 'all' | 'fully_traced' | 'partially_traced' | 'untraced' | 'ambiguous' = 'all';
  traceabilitySearch = '';
  traceability: TraceabilityMatrixResult | null = null;
  errorMessage = '';
  diagramsRendered = false;
  isExportingPdf = false;
  isExportingDocx = false;
  inviteEmail = '';
  inviteRole = 'viewer';
  isInviting = false;
  collabError = '';
  isDiffing = false;
  diffError = '';

  // GitHub Integration state
  githubConn: GitHubConnection | null = null;
  isLoadingGithub = false;
  isConnectingGithub = false;
  isDisconnectingGithub = false;
  isSyncingGithub = false;
  githubError = '';
  githubSuccessMessage = '';
  githubPat = '';
  githubOwner = '';
  githubRepo = '';
  syncedIssuesMap: { [req: string]: string } = {};

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
        this.parseTraceability();
        this.loadCollaborators();
        this.loadVersions();
        this.loadGitHubConnection();
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
        this.loadVersions();
        this.loadGitHubConnection();
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
        this.loadVersions();
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
      this.loadVersions();
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
      this.loadVersions();
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
      this.loadVersions();
      this.cdr.detectChanges();
    },
    error: (err) => {
      this.isGeneratingPlanning = false;
      this.errorMessage = this.extractErrorMessage(err);
      this.cdr.detectChanges();
    }
  });
}

parseTraceability() {
  if (this.project?.traceability_json) {
    try {
      this.traceability = JSON.parse(this.project.traceability_json);
    } catch (e) {
      this.traceability = null;
    }
  } else {
    this.traceability = null;
  }
}

runTraceabilityGeneration() {
  if (!this.project) return;
  this.isGeneratingTraceability = true;
  this.traceabilityError = '';

  this.projectService.generateTraceability(this.project.id).subscribe({
    next: (data) => {
      this.project = data;
      this.parseTraceability();
      this.isGeneratingTraceability = false;
      this.loadVersions();
      this.cdr.detectChanges();
    },
    error: (err) => {
      this.isGeneratingTraceability = false;
      this.traceabilityError = this.extractErrorMessage(err);
      this.cdr.detectChanges();
    }
  });
}

setTraceabilityFilter(filter: 'all' | 'fully_traced' | 'partially_traced' | 'untraced' | 'ambiguous') {
  this.traceabilityFilter = filter;
}

filteredTraceabilityItems(): TraceabilityItem[] {
  if (!this.traceability?.items) return [];
  let items = this.traceability.items;

  if (this.traceabilityFilter === 'fully_traced') {
    items = items.filter(it => it.status === 'fully_traced');
  } else if (this.traceabilityFilter === 'partially_traced') {
    items = items.filter(it => it.status === 'partially_traced');
  } else if (this.traceabilityFilter === 'untraced') {
    items = items.filter(it => it.status === 'untraced');
  } else if (this.traceabilityFilter === 'ambiguous') {
    items = items.filter(it => it.is_ambiguous || (it.ambiguity_flags && it.ambiguity_flags.length > 0));
  }

  if (this.traceabilitySearch.trim()) {
    const q = this.traceabilitySearch.toLowerCase().trim();
    items = items.filter(it =>
      (it.requirement_id && it.requirement_id.toLowerCase().includes(q)) ||
      (it.requirement_text && it.requirement_text.toLowerCase().includes(q)) ||
      (it.diagram_elements && it.diagram_elements.some(d => d && d.toLowerCase().includes(q))) ||
      (it.api_endpoints && it.api_endpoints.some(a => a && a.toLowerCase().includes(q))) ||
      (it.github_issue_number && it.github_issue_number.toLowerCase().includes(q)) ||
      (it.validation_notes && it.validation_notes.toLowerCase().includes(q))
    );
  }

  return items;
}

get fullyTracedCount(): number {
  return this.traceability?.fully_traced_count || 0;
}

get partiallyTracedCount(): number {
  return this.traceability?.partially_traced_count || 0;
}

get untracedCount(): number {
  return this.traceability?.untraced_count || 0;
}

get ambiguousCount(): number {
  if (!this.traceability?.items) return 0;
  return this.traceability.items.filter(it => it.is_ambiguous || (it.ambiguity_flags && it.ambiguity_flags.length > 0)).length;
}

traceabilityStatusBadgeClass(status: string): string {
  switch (status) {
    case 'fully_traced':
      return 'status-traced-full';
    case 'partially_traced':
      return 'status-traced-partial';
    case 'untraced':
      return 'status-traced-untraced';
    default:
      return 'status-traced-unknown';
  }
}

traceabilityStatusLabel(status: string): string {
  switch (status) {
    case 'fully_traced':
      return 'Fully Traced';
    case 'partially_traced':
      return 'Partially Traced';
    case 'untraced':
      return 'Orphan / Untraced';
    default:
      return status ? status.replace(/_/g, ' ') : 'Unknown';
  }
}

coveragePercentage(score: number): number {
  return Math.round((score || 0) * 100);
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

loadCollaborators() {
  if (!this.project) return;
  this.projectService.getCollaborators(this.project.id).subscribe({
    next: (data) => { this.collaborators = data; this.cdr.detectChanges(); },
    error: () => { /* silently ignore if not owner/viewer of collaborators list */ }
  });
}

sendInvite() {
  if (!this.project || !this.inviteEmail) return;
  this.isInviting = true;
  this.collabError = '';
  this.projectService.inviteCollaborator(this.project.id, this.inviteEmail, this.inviteRole).subscribe({
    next: () => {
      this.inviteEmail = '';
      this.isInviting = false;
      this.loadCollaborators();
    },
    error: (err) => {
      this.isInviting = false;
      this.collabError = this.extractErrorMessage(err);
      this.cdr.detectChanges();
    }
  });
}

changeRole(c: Collaborator, newRole: string) {
  if (!this.project) return;
  this.projectService.updateCollaboratorRole(this.project.id, c.id, newRole).subscribe({
    next: (updated) => {
      c.role = updated.role;
      this.cdr.detectChanges();
    }
  });
}

removeCollab(c: Collaborator) {
  if (!this.project) return;
  if (!confirm(`Remove ${c.name} from this project?`)) return;
  this.projectService.removeCollaborator(this.project.id, c.id).subscribe({
    next: () => {
      this.collaborators = this.collaborators.filter(x => x.id !== c.id);
      this.cdr.detectChanges();
    }
  });
}

loadVersions() {
  if (!this.project) return;
  this.projectService.getVersions(this.project.id).subscribe({
    next: (data) => {
      this.versions = data;
      this.cdr.detectChanges();
    },
    error: () => {}
  });
}

runDiff() {
  if (!this.project || this.selectedFromVersion === null || this.selectedToVersion === null) return;
  this.isDiffing = true;
  this.diffError = '';
  this.versionDiff = null;

  this.projectService.diffVersions(this.project.id, this.selectedFromVersion, this.selectedToVersion).subscribe({
    next: (data) => {
      this.versionDiff = data;
      this.isDiffing = false;
      this.cdr.detectChanges();
    },
    error: (err) => {
      this.isDiffing = false;
      this.diffError = this.extractErrorMessage(err);
      this.cdr.detectChanges();
    }
  });
}

diffKeys(): string[] {
  return this.versionDiff ? Object.keys(this.versionDiff.changes) : [];
}

formatFieldName(key: string): string {
  return key.replace(/_json$/, '').replace(/_/g, ' ');
}

isSimpleFieldChange(key: string): boolean {
  return ['title', 'description', 'status'].includes(key);
}

isAnalysisChange(key: string): boolean {
  return key === 'analysis_json';
}

getSimpleChange(key: string): { old: any; new: any } {
  return this.versionDiff!.changes[key];
}

getAnalysisSubFields(key: string): string[] {
  return Object.keys(this.versionDiff!.changes[key] || {});
}

getAnalysisAdded(key: string, subField: string): string[] {
  return this.versionDiff!.changes[key]?.[subField]?.added || [];
}

getAnalysisRemoved(key: string, subField: string): string[] {
  return this.versionDiff!.changes[key]?.[subField]?.removed || [];
}

formatSubFieldName(key: string): string {
  return key.replace(/_/g, ' ');
}

// GitHub Integration methods
loadGitHubConnection() {
  if (!this.project) return;
  this.isLoadingGithub = true;
  this.githubError = '';
  this.projectService.getGitHubConnection(this.project.id).subscribe({
    next: (data) => {
      this.githubConn = data;
      this.syncedIssuesMap = data.synced_issues || {};
      this.isLoadingGithub = false;
      this.cdr.detectChanges();
    },
    error: (err) => {
      this.isLoadingGithub = false;
      if (err.status === 404) {
        this.githubConn = null;
        this.syncedIssuesMap = {};
      } else {
        this.githubError = this.extractErrorMessage(err);
      }
      this.cdr.detectChanges();
    }
  });
}

connectGitHub() {
  if (!this.project || !this.githubOwner.trim() || !this.githubRepo.trim() || !this.githubPat.trim()) {
    this.githubError = 'Please provide Owner, Repository Name, and Personal Access Token.';
    return;
  }
  this.isConnectingGithub = true;
  this.githubError = '';
  this.githubSuccessMessage = '';

  const payload: GitHubConnectPayload = {
    personal_access_token: this.githubPat.trim(),
    repo_owner: this.githubOwner.trim(),
    repo_name: this.githubRepo.trim()
  };

  this.projectService.connectGitHubRepo(this.project.id, payload).subscribe({
    next: (conn) => {
      this.githubConn = conn;
      this.syncedIssuesMap = conn.synced_issues || {};
      this.isConnectingGithub = false;
      this.githubPat = '';
      this.githubSuccessMessage = `Connected to ${conn.repo_owner}/${conn.repo_name} successfully!`;
      setTimeout(() => {
        this.githubSuccessMessage = '';
        this.cdr.detectChanges();
      }, 5000);
      this.cdr.detectChanges();
    },
    error: (err) => {
      this.isConnectingGithub = false;
      this.githubError = this.extractErrorMessage(err);
      this.cdr.detectChanges();
    }
  });
}

disconnectGitHub() {
  if (!this.project) return;
  const repoLabel = this.githubConn ? `${this.githubConn.repo_owner}/${this.githubConn.repo_name}` : 'repository';
  if (!confirm(`Disconnect ${repoLabel} from this project?`)) return;

  this.isDisconnectingGithub = true;
  this.githubError = '';
  this.githubSuccessMessage = '';

  this.projectService.disconnectGitHubRepo(this.project.id).subscribe({
    next: () => {
      this.githubConn = null;
      this.syncedIssuesMap = {};
      this.isDisconnectingGithub = false;
      this.githubSuccessMessage = 'Repository disconnected.';
      setTimeout(() => {
        this.githubSuccessMessage = '';
        this.cdr.detectChanges();
      }, 4000);
      this.cdr.detectChanges();
    },
    error: (err) => {
      this.isDisconnectingGithub = false;
      this.githubError = this.extractErrorMessage(err);
      this.cdr.detectChanges();
    }
  });
}

syncGitHubRequirements() {
  if (!this.project) return;
  if (!this.analysis || !this.analysis.functional_requirements?.length) {
    this.githubError = 'Analyze the project requirements first before syncing.';
    return;
  }

  this.isSyncingGithub = true;
  this.githubError = '';
  this.githubSuccessMessage = '';

  this.projectService.syncGitHubRequirements(this.project.id).subscribe({
    next: (result: SyncResult) => {
      this.isSyncingGithub = false;
      if (result.synced_issues) {
        this.syncedIssuesMap = result.synced_issues;
        if (this.githubConn) {
          this.githubConn.synced_issues = result.synced_issues;
        }
      }
      const createdMsg = `${result.created} new issue${result.created === 1 ? '' : 's'} created`;
      const skippedMsg = result.skipped > 0 ? `, ${result.skipped} already synced` : '';
      this.githubSuccessMessage = `Synced successfully: ${createdMsg}${skippedMsg}!`;
      setTimeout(() => {
        this.githubSuccessMessage = '';
        this.cdr.detectChanges();
      }, 6000);
      this.cdr.detectChanges();
    },
    error: (err) => {
      this.isSyncingGithub = false;
      this.githubError = this.extractErrorMessage(err);
      this.cdr.detectChanges();
    }
  });
}

get syncedRequirementsCount(): number {
  if (!this.analysis?.functional_requirements) return 0;
  return this.analysis.functional_requirements.filter(req => !!this.syncedIssuesMap[req]).length;
}

get totalRequirementsCount(): number {
  return this.analysis?.functional_requirements?.length || 0;
}

get syncPercentage(): number {
  if (!this.totalRequirementsCount) return 0;
  return Math.round((this.syncedRequirementsCount / this.totalRequirementsCount) * 100);
}

getIssueUrl(req: string): string | null {
  return this.syncedIssuesMap[req] || null;
}

getIssueNumber(url: string): string {
  const match = url?.match(/\/issues\/(\d+)/);
  return match ? `#${match[1]}` : '#';
}

getSyncedIssuesList(): { req: string; url: string }[] {
  if (!this.syncedIssuesMap) return [];
  return Object.entries(this.syncedIssuesMap).map(([req, url]) => ({ req, url }));
}
}