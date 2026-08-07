import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { delay, tap } from 'rxjs/operators';

export interface Agent {
  id: string;
  name: string;
  role: string;
  tag: 'intel' | 'planner' | 'creative' | 'optimizer';
  avatar: string;
  color: string;
  bio: string;
  status: 'Idle' | 'Thinking' | 'Working' | 'Reviewing';
}

export interface ChatMessage {
  id: string;
  sender: Agent;
  timestamp: Date;
  content: string;
  suggestedAssets?: {
    type: 'analysis' | 'plan' | 'creative' | 'optimization';
    title: string;
    body: string;
  }[];
}

export interface Campaign {
  id: string;
  title: string;
  status: 'Draft' | 'Active' | 'Completed';
  targetAudience: string;
  budget: number;
  startDate: string;
  metrics: {
    impressions: number;
    clicks: number;
    conversions: number;
    ctr: number;
    roi: number;
  };
  agentContributions: { agentTag: string; tasksCompleted: number }[];
}

@Injectable({
  providedIn: 'root'
})
export class AgentService {
  private agents: Agent[] = [
    {
      id: 'agt_1',
      name: 'Alpha (BI)',
      role: 'Business Intelligence Agent',
      tag: 'intel',
      avatar: 'https://api.dicebear.com/7.x/adventurer/svg?seed=AlphaBI',
      color: '#a37c5d', // Clay Brown
      bio: 'Analyzes product performance, extracts customer insights, forecasts demand trends, and provides business recommendations.',
      status: 'Idle'
    },
    {
      id: 'agt_2',
      name: 'Orion (Planner)',
      role: 'Marketing Planner Agent',
      tag: 'planner',
      avatar: 'https://api.dicebear.com/7.x/adventurer/svg?seed=OrionPlan',
      color: '#c95b32', // Burnt Terracotta
      bio: 'Structures strategic marketing campaigns, plans festival promotions, coordinates weekly discount rates, and configures posting schedules.',
      status: 'Idle'
    },
    {
      id: 'agt_3',
      name: 'Veda (Creative)',
      role: 'Creative Studio Agent',
      tag: 'creative',
      avatar: 'https://api.dicebear.com/7.x/adventurer/svg?seed=VedaStudio',
      color: '#dfa84a', // Amber Gold
      bio: 'Generates captions, selects hashtags, outlines promotional concepts, crafts copy, and drafts reel video ideas.',
      status: 'Idle'
    },
    {
      id: 'agt_4',
      name: 'Lyra (Optimizer)',
      role: 'Optimization Agent',
      tag: 'optimizer',
      avatar: 'https://api.dicebear.com/7.x/adventurer/svg?seed=LyraOpt',
      color: '#728b74', // Sage Green
      bio: 'Evaluates real-time performance, collects channel feedback metrics, and refines campaign targeting for maximum conversions.',
      status: 'Idle'
    }
  ];

  private campaigns: Campaign[] = [
    {
      id: 'cmp_1',
      title: 'Festival Cookware Promo',
      status: 'Active',
      targetAudience: 'Home cooks, seasonal culinary shoppers',
      budget: 15000,
      startDate: '2026-08-01',
      metrics: {
        impressions: 320000,
        clicks: 14500,
        conversions: 980,
        ctr: 4.53,
        roi: 215
      },
      agentContributions: [
        { agentTag: 'intel', tasksCompleted: 6 },
        { agentTag: 'planner', tasksCompleted: 8 },
        { agentTag: 'creative', tasksCompleted: 15 },
        { agentTag: 'optimizer', tasksCompleted: 7 }
      ]
    },
    {
      id: 'cmp_2',
      title: 'Organic Tea Launch Plan',
      status: 'Completed',
      targetAudience: 'Health enthusiasts, herbal tea consumers',
      budget: 9000,
      startDate: '2026-07-10',
      metrics: {
        impressions: 480000,
        clicks: 22000,
        conversions: 1850,
        ctr: 4.58,
        roi: 290
      },
      agentContributions: [
        { agentTag: 'intel', tasksCompleted: 4 },
        { agentTag: 'planner', tasksCompleted: 5 },
        { agentTag: 'creative', tasksCompleted: 10 },
        { agentTag: 'optimizer', tasksCompleted: 8 }
      ]
    }
  ];

  private agentsSubject = new BehaviorSubject<Agent[]>(this.agents);
  public agents$ = this.agentsSubject.asObservable();

  private campaignsSubject = new BehaviorSubject<Campaign[]>(this.campaigns);
  public campaigns$ = this.campaignsSubject.asObservable();

  private chatLogSubject = new BehaviorSubject<ChatMessage[]>([]);
  public chatLog$ = this.chatLogSubject.asObservable();

  private isSimulationRunningSubject = new BehaviorSubject<boolean>(false);
  public isSimulationRunning$ = this.isSimulationRunningSubject.asObservable();

  constructor() {
    this.resetChat();
  }

  public getAgents(): Agent[] {
    return this.agents;
  }

  public getCampaigns(): Campaign[] {
    return this.campaigns;
  }

  public addCampaign(campaign: Omit<Campaign, 'id' | 'metrics' | 'agentContributions'>): void {
    const newCampaign: Campaign = {
      ...campaign,
      id: 'cmp_' + Math.random().toString(36).substring(2, 11),
      metrics: {
        impressions: 0,
        clicks: 0,
        conversions: 0,
        ctr: 0,
        roi: 0
      },
      agentContributions: this.agents.map(a => ({ agentTag: a.tag, tasksCompleted: 0 }))
    };
    this.campaigns.push(newCampaign);
    this.campaignsSubject.next([...this.campaigns]);
  }

  public resetChat(): void {
    const initialMessage: ChatMessage = {
      id: 'msg_0',
      sender: this.agents[0], // Business Intelligence Agent
      timestamp: new Date(),
      content: 'Hello Squad! I am initializing our workspace. Please upload a marketing project goal or brief. I will trigger the sales and product intelligence analysis.'
    };
    this.chatLogSubject.next([initialMessage]);
    this.updateAgentStatus('intel', 'Idle');
    this.updateAgentStatus('planner', 'Idle');
    this.updateAgentStatus('creative', 'Idle');
    this.updateAgentStatus('optimizer', 'Idle');
  }

  private updateAgentStatus(tag: Agent['tag'], status: Agent['status']): void {
    this.agents = this.agents.map(a => a.tag === tag ? { ...a, status } : a);
    this.agentsSubject.next(this.agents);
  }

  public runCampaignSimulation(brief: string): void {
    if (this.isSimulationRunningSubject.value) return;

    this.isSimulationRunningSubject.next(true);
    this.chatLogSubject.next([]);

    const steps = [
      {
        tag: 'intel' as const,
        status: 'Thinking' as const,
        content: `Running initial sales analysis and demand forecasting models for brief: "${brief}".

I have identified high buying patterns in modern segments. Projections show +35% organic demand over the next quarter. Recommended focus: Highlight product longevity and premium utility. Pass on to @Orion (Planner) to establish campaign calendar, festivals, and schedules.`,
        assets: [
          {
            type: 'analysis' as const,
            title: 'BI Sales & Product Performance Report',
            body: 'Target Demographics: 22-45 yrs, eco-aware consumers\nForecasted Conversion Lift: +2.4x\nCompetitive Advantage: Higher durability index (+18% above median benchmark).'
          }
        ],
        delayMs: 1500
      },
      {
        tag: 'planner' as const,
        status: 'Working' as const,
        content: `Structuring the weekly marketing calendar and promotional configurations based on Alpha's BI intelligence.

I've established a weekly rollout strategy:
- Kick-off with a 15% discount code: "ECOSTART15"
- Align posts to the upcoming Autumn Harvest Festival.
- Schedule weekly email newsletters and interactive social posts.

@Veda (Creative Studio), generate the copywriting assets, captions, and reel concepts.`,
        assets: [
          {
            type: 'plan' as const,
            title: 'Weekly Promotional Layout & Calendar',
            body: 'Week 1: Awareness (Festival teaser + Early Access sign-up)\nWeek 2: Conversion (Release promo code, launch influencer reels)\nWeek 3: Engagement (Customer review posts + UGC spotlight)\nPosting Schedule: Mon/Wed/Fri 10:00 AM & 6:00 PM EST'
          }
        ],
        delayMs: 4500
      },
      {
        tag: 'creative' as const,
        status: 'Working' as const,
        content: `Creative assets generated! Crafting social copies, hashtags, and a detailed video reel storyboard for Instagram/TikTok.`,
        assets: [
          {
            type: 'creative' as const,
            title: 'Instagram Post & Video Reel Concept',
            body: 'Caption: Switch to utility that nature approves 🌍 Say goodbye to wasteful cycles and hello to durability. Start your conscious journey with 15% off using code ECOSTART15.\nHashtags: #ZeroWasteLiving #EarthyAesthetics #SustainableHome #EcoFriendlyIdeas\nReel Concept: 5-second aesthetic transitions. Cut between macro textures of raw organic materials and the product in active kitchen settings. Smooth soft acoustic background track.'
          }
        ],
        delayMs: 8000
      },
      {
        tag: 'optimizer' as const,
        status: 'Working' as const,
        content: `I've set up the feedback loops and performance tracking models.

- Simulated CTR: 5.12%
- Projected ROAS: 3.4x
- Budget Weighing: 60% on Instagram Reels, 40% on Search/Pinterest.

Optimizing: I recommend tightening target criteria on eco-kitchen tags to ensure maximum conversion accuracy. We are cleared to launch. CMO review complete.`,
        assets: [
          {
            type: 'optimization' as const,
            title: 'Optimization Feedback & Performance Goals',
            body: 'CTR Target: >4.5%\nROAS Benchmark: 3.2x\nConversion Loop: A/B split testing between Veda\'s Reels variant and search ad text copies, adjusting budgets every 48 hours based on performance.'
          }
        ],
        delayMs: 11500
      }
    ];

    steps.forEach((step, index) => {
      setTimeout(() => {
        if (index > 0) {
          const prevStep = steps[index - 1];
          this.updateAgentStatus(prevStep.tag, 'Idle');
        }

        this.updateAgentStatus(step.tag, step.status);

        const currentMessages = this.chatLogSubject.value;
        const senderAgent = this.agents.find(a => a.tag === step.tag)!;
        
        const newMsg: ChatMessage = {
          id: 'msg_' + Math.random().toString(36).substring(2, 11),
          sender: senderAgent,
          timestamp: new Date(),
          content: step.content,
          suggestedAssets: step.assets
        };

        this.chatLogSubject.next([...currentMessages, newMsg]);

        if (index === steps.length - 1) {
          this.updateAgentStatus(step.tag, 'Idle');
          this.isSimulationRunningSubject.next(false);

          this.addCampaign({
            title: `${brief.length > 25 ? brief.substring(0, 22) + '...' : brief} Campaign`,
            status: 'Active',
            targetAudience: 'Sustainable demographic segment',
            budget: 12000,
            startDate: new Date().toISOString().split('T')[0]
          });
        }
      }, step.delayMs);
    });
  }
}
