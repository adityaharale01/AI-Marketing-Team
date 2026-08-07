import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AgentService, Agent } from '../../services/agent.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatCardModule,
    MatButtonModule,
    MatIconModule
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent implements OnInit {
  agents: Agent[] = [];
  selectedAgent: Agent | null = null;

  constructor(private agentService: AgentService) {}

  ngOnInit(): void {
    this.agents = this.agentService.getAgents();
    this.selectedAgent = this.agents.find(a => a.tag === 'planner') || this.agents[0];
  }

  selectAgent(agent: Agent): void {
    this.selectedAgent = agent;
  }
}
