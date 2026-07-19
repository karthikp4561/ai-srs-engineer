import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NewProject } from './new-project';

describe('NewProject', () => {
  let component: NewProject;
  let fixture: ComponentFixture<NewProject>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NewProject],
    }).compileComponents();

    fixture = TestBed.createComponent(NewProject);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
