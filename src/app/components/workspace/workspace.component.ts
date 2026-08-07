import { Component, OnInit, OnDestroy, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Subscription } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { AgentService, Agent, ChatMessage } from '../../services/agent.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-workspace',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule
  ],
  templateUrl: './workspace.component.html',
  styleUrl: './workspace.component.css'
})
export class WorkspaceComponent implements OnInit, OnDestroy {
  @ViewChild('chatScrollContainer') private chatScrollContainer!: ElementRef;

  agents: Agent[] = [];
  chatLog: ChatMessage[] = [];
  isSimulationRunning = false;
  campaignBrief = '';
  campaignBudget = 8500;

  private subscriptions = new Subscription();

  constructor(
    public agentService: AgentService,
    public authService: AuthService,
    private toastr: ToastrService
  ) {}

  ngOnInit(): void {
    // Sync agents
    this.subscriptions.add(
      this.agentService.agents$.subscribe(agents => {
        this.agents = agents;
      })
    );

    // Sync chat log
    this.subscriptions.add(
      this.agentService.chatLog$.subscribe(log => {
        this.chatLog = log;
        this.scrollToBottom();
      })
    );

    // Sync simulation status
    this.subscriptions.add(
      this.agentService.isSimulationRunning$.subscribe(running => {
        this.isSimulationRunning = running;
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  submitBrief(): void {
    if (!this.campaignBrief.trim()) {
      this.toastr.warning('Please enter a campaign brief descriptive prompt.', 'Brief Missing');
      return;
    }

    this.toastr.success('Multi-agent workspace initialized. Launching marketing sprint.', 'Sprint Started');
    this.agentService.runCampaignSimulation(this.campaignBrief);
    this.campaignBrief = '';
  }

  copyAssetToClipboard(title: string, content: string): void {
    navigator.clipboard.writeText(content).then(() => {
      this.toastr.info(`"${title}" copy draft copied to clipboard.`, 'Asset Copied');
    }).catch(err => {
      this.toastr.error('Failed to copy text.', 'Clipboard Error');
    });
  }

  resetWorkspace(): void {
    if (this.isSimulationRunning) {
      this.toastr.warning('Please wait for the current agent sprint to finish.', 'Sprint Running');
      return;
    }
    this.agentService.resetChat();
    this.toastr.success('Workspace logs cleared and reset to base state.', 'Workspace Reset');
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      try {
        if (this.chatScrollContainer) {
          this.chatScrollContainer.nativeElement.scrollTop = this.chatScrollContainer.nativeElement.scrollHeight;
        }
      } catch (err) {}
    }, 100);
  }
}
