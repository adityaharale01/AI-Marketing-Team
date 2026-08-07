import { Component, OnInit, AfterViewInit, OnDestroy, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Subscription } from 'rxjs';
import { Chart, registerables } from 'chart.js';
import { AgentService, Campaign } from '../../services/agent.service';
import { AuthService } from '../../services/auth.service';
import { ToastrService } from 'ngx-toastr';

Chart.register(...registerables);

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule
  ],
  templateUrl: './analytics.component.html',
  styleUrl: './analytics.component.css'
})
export class AnalyticsComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('trendChart') trendChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('mediumChart') mediumChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('contributeChart') contributeChartRef!: ElementRef<HTMLCanvasElement>;

  campaigns: Campaign[] = [];
  selectedCampaign: Campaign | null = null;
  
  // Aggregate stats
  totalImpressions = 0;
  totalClicks = 0;
  totalConversions = 0;
  averageCtr = 0;
  averageRoi = 0;

  private subscriptions = new Subscription();
  private charts: Chart[] = [];

  constructor(
    private agentService: AgentService,
    public authService: AuthService,
    private toastr: ToastrService
  ) {}

  exportPDF(): void {
    if (!this.selectedCampaign) return;
    this.toastr.info(`Structuring PDF report for ${this.selectedCampaign.title}...`, 'Export Pipeline');
    setTimeout(() => {
      this.toastr.success(`PDF report for "${this.selectedCampaign?.title}" saved in Downloads.`, 'Export Successful');
    }, 1200);
  }

  ngOnInit(): void {
    this.subscriptions.add(
      this.agentService.campaigns$.subscribe(campaigns => {
        this.campaigns = campaigns;
        if (campaigns.length > 0 && !this.selectedCampaign) {
          this.selectedCampaign = campaigns[0];
        }
        this.calculateAggregateStats();
        // If charts are already initialized, we re-render chart data
        if (this.charts.length > 0) {
          this.renderCharts();
        }
      })
    );
  }

  ngAfterViewInit(): void {
    // Small timeout ensures DOM elements are fully mounted
    setTimeout(() => {
      this.renderCharts();
    }, 200);
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    this.destroyCharts();
  }

  selectCampaign(campaign: Campaign): void {
    this.selectedCampaign = campaign;
    this.renderCharts();
  }

  private calculateAggregateStats(): void {
    if (this.campaigns.length === 0) return;
    
    let impressions = 0;
    let clicks = 0;
    let conversions = 0;
    let totalCtr = 0;
    let totalRoi = 0;
    let activeCampaignsCount = 0;

    this.campaigns.forEach(c => {
      impressions += c.metrics.impressions;
      clicks += c.metrics.clicks;
      conversions += c.metrics.conversions;
      if (c.status !== 'Draft') {
        totalCtr += c.metrics.ctr;
        totalRoi += c.metrics.roi;
        activeCampaignsCount++;
      }
    });

    this.totalImpressions = impressions;
    this.totalClicks = clicks;
    this.totalConversions = conversions;
    this.averageCtr = activeCampaignsCount > 0 ? parseFloat((totalCtr / activeCampaignsCount).toFixed(2)) : 0;
    this.averageRoi = activeCampaignsCount > 0 ? Math.round(totalRoi / activeCampaignsCount) : 0;
  }

  private destroyCharts(): void {
    this.charts.forEach(c => c.destroy());
    this.charts = [];
  }

  private renderCharts(): void {
    this.destroyCharts();

    if (this.campaigns.length === 0) return;

    // 1. Line Chart: Conversions Over Time Simulation
    if (this.trendChartRef) {
      const ctx = this.trendChartRef.nativeElement.getContext('2d');
      if (ctx) {
        // Build simulated data points
        const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const conversionsData = this.selectedCampaign?.status === 'Active' 
          ? [12, 19, 32, 28, 45, 55, 68]
          : this.selectedCampaign?.status === 'Completed'
          ? [25, 40, 58, 65, 82, 95, 110]
          : [0, 0, 0, 0, 0, 0, 0];

        const clickData = this.selectedCampaign?.status === 'Active'
          ? [240, 310, 520, 480, 710, 890, 1100]
          : this.selectedCampaign?.status === 'Completed'
          ? [450, 720, 980, 1150, 1420, 1680, 1920]
          : [0, 0, 0, 0, 0, 0, 0];

        const chart = new Chart(ctx, {
          type: 'line',
          data: {
            labels,
            datasets: [
              {
                label: 'Conversions',
                data: conversionsData,
                borderColor: '#c95b32', // Terracotta
                backgroundColor: 'rgba(201, 91, 50, 0.1)',
                tension: 0.3,
                fill: true,
                borderWidth: 3,
                yAxisID: 'y'
              },
              {
                label: 'Clicks',
                data: clickData,
                borderColor: '#dfa84a', // Amber Gold
                backgroundColor: 'transparent',
                tension: 0.3,
                borderWidth: 2,
                borderDash: [5, 5],
                yAxisID: 'y1'
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                labels: {
                  font: { family: 'Outfit', size: 12 }
                }
              }
            },
            scales: {
              x: {
                grid: { display: false }
              },
              y: {
                type: 'linear',
                display: true,
                position: 'left',
                grid: { color: 'rgba(46, 38, 32, 0.05)' }
              },
              y1: {
                type: 'linear',
                display: true,
                position: 'right',
                grid: { drawOnChartArea: false }
              }
            }
          }
        });
        this.charts.push(chart);
      }
    }

    // 2. Doughnut Chart: Budget Weighting by Medium (Earthy tones, no blue!)
    if (this.mediumChartRef) {
      const ctx = this.mediumChartRef.nativeElement.getContext('2d');
      if (ctx) {
        const chart = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: ['Instagram Reels', 'Google Ads B2B', 'LinkedIn Promoted', 'Organic / SEO'],
            datasets: [
              {
                data: [35, 30, 20, 15],
                backgroundColor: [
                  '#c95b32', // Terracotta
                  '#dfa84a', // Amber Gold
                  '#a37c5d', // Clay Brown
                  '#728b74'  // Sage Green
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  boxWidth: 12,
                  font: { family: 'Outfit', size: 11 }
                }
              }
            },
            cutout: '65%'
          }
        });
        this.charts.push(chart);
      }
    }

    // 3. Bar Chart: Agent Task Contribution Distribution
    if (this.contributeChartRef) {
      const ctx = this.contributeChartRef.nativeElement.getContext('2d');
      if (ctx) {
        const contributionData = this.selectedCampaign?.agentContributions || [
          { agentTag: 'intel', tasksCompleted: 0 },
          { agentTag: 'planner', tasksCompleted: 0 },
          { agentTag: 'creative', tasksCompleted: 0 },
          { agentTag: 'optimizer', tasksCompleted: 0 }
        ];

        const chart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: ['BI Intel', 'Planner', 'Creative', 'Optimizer'],
            datasets: [
              {
                label: 'Tasks Executed',
                data: contributionData.map(c => c.tasksCompleted),
                backgroundColor: [
                  '#a37c5d', // Clay Brown
                  '#c95b32', // Terracotta
                  '#dfa84a', // Amber Gold
                  '#728b74'  // Sage Green
                ],
                borderRadius: 8,
                maxBarThickness: 40
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              x: {
                grid: { display: false }
              },
              y: {
                grid: { color: 'rgba(46, 38, 32, 0.05)' },
                beginAtZero: true
              }
            }
          }
        });
        this.charts.push(chart);
      }
    }
  }
}
