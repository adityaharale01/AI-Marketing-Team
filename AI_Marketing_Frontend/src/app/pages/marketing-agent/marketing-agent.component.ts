import { ChangeDetectorRef, Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { ApiService, MarketingCampaignRequest, MarketingCampaignResult } from '../../core/services/api.service';
import { PlatformService } from '../../core/services/platform.service';
import html2canvas from 'html2canvas';
@Component({
  selector: 'app-marketing-agent',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './marketing-agent.component.html',
  styleUrl: './marketing-agent.component.css'
})
export class MarketingAgentComponent {
  form = {
    campaign_name: 'Weekend Spotlight',
    goal: 'Increase local awareness and encourage visits this weekend',
    platform: 'Instagram',
    target_audience: 'Local customers and families',
    offer: '',
    budget: null as number | null
  };
  result: MarketingCampaignResult | null = null;
  loading = false;
  publishing = false;
  error = '';
  notice = '';
  posterImageDataUrl: string | null = null;
  posterGenerating = false;

  constructor(
    public platform: PlatformService,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  generate(): void {
    const activeBusiness = this.platform.activeBusiness;
    if (this.loading || !activeBusiness) {
      if (!activeBusiness) this.error = 'Select or create a business before generating a campaign.';
      return;
    }
    this.loading = true;
    this.error = '';
    this.notice = '';
    this.result = null;
    this.posterImageDataUrl = null;
    const payload: MarketingCampaignRequest = {
      ...this.form,
      business_id: activeBusiness.id,
      budget: this.form.budget === null || this.form.budget === ('' as any) ? null : Number(this.form.budget)
    };
    this.api.generateMarketingCampaign(payload).subscribe({
      next: value => { this.result = value; this.loading = false; this.cdr.detectChanges(); },
      error: (err: HttpErrorResponse) => {
        this.error = this.errorText(err);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  publishDemo(): void {
    if (!this.result || this.publishing) return;
    this.publishing = true;
    this.error = '';
    this.notice = '';
    this.api.publishCampaignDemo(this.result.campaign_id).subscribe({
      next: response => {
        this.result!.status = 'active';
        this.notice = response.message;
        this.publishing = false;
        this.cdr.detectChanges();
      },
      error: (err: HttpErrorResponse) => {
        this.error = this.errorText(err);
        this.publishing = false;
        this.cdr.detectChanges();
      }
    });
  }

  copyText(text: string): void {
    if (!text) return;
    const clipboard = navigator.clipboard;
    if (!clipboard) {
      this.notice = 'Clipboard access was unavailable. Select and copy the text manually.';
      return;
    }
    clipboard.writeText(text).then(
      () => { this.notice = 'Copied to clipboard.'; this.cdr.detectChanges(); },
      () => { this.notice = 'Clipboard access was unavailable. Select and copy the text manually.'; this.cdr.detectChanges(); }
    );
  }


  
  generatePosterArtwork(): void {
    if (!this.result || this.posterGenerating) return;

    this.posterGenerating = true;
    this.error = '';
    this.notice = '';

    const businessName = this.result.business.name;
    const campaignName = this.result.campaign_name;
    const headline = this.result.poster.headline;
    const subtitle = this.result.poster.subtitle;

    // Build a different visual brief from the current campaign.
    // Do not ask the image model to render any campaign text.
    const prompt = [
      'Create premium, photorealistic commercial advertising artwork.',
      `Brand context: ${businessName}.`,
      `Campaign theme: ${campaignName}.`,
      `Campaign objective: ${this.form.goal}.`,
      `Target audience: ${this.form.target_audience || 'General customers'}.`,
      `Social platform: ${this.form.platform}.`,
      `Campaign headline context: ${headline}.`,
      `Campaign message context: ${subtitle}.`,
      this.form.offer
        ? `Offer context for visual mood only: ${this.form.offer}.`
        : '',
      'Infer a suitable visual concept from the supplied campaign details.',
      'Use product-relevant imagery, professional art direction, realistic textures,',
      'balanced lighting, premium composition and a coordinated color palette.',
      'Leave a clean, uncluttered area for real text to be overlaid by the application.',
      'Generate the background artwork only.',
      'ABSOLUTELY NO text, words, letters, numbers, typography, logos,',
      'watermarks, signs, labels, banners, buttons, captions or fake writing.',
      'Do not reproduce the campaign headline or business name inside the image.'
    ].filter(Boolean).join(' ');

    this.api.generatePosterArtwork(prompt, 4).subscribe({
      next: response => {
        this.posterImageDataUrl = response.image_data_url;
        this.posterGenerating = false;
        this.notice = 'Campaign artwork generated. Review the final poster before use.';
        this.cdr.detectChanges();
      },
      error: (err: HttpErrorResponse) => {
        this.error = this.errorText(err);
        this.posterGenerating = false;
        this.cdr.detectChanges();
      }
    });
  }


  

async downloadPoster(): Promise<void> {
  if (!this.result) return;

  // Use the actual poster container from your HTML.
  const posterElement = document.querySelector(
    '.creative-poster'
  ) as HTMLElement | null;

  // If AI artwork has not been generated, use the fallback poster.
  const fallbackElement = document.querySelector(
    '.poster-preview'
  ) as HTMLElement | null;

  const elementToCapture = posterElement || fallbackElement;

  if (!elementToCapture) {
    this.error = 'Poster preview not found. Generate a campaign first.';
    return;
  }

  try {
    // Wait for the background artwork to finish loading.
    const images = Array.from(
      elementToCapture.querySelectorAll('img')
    );

    await Promise.all(
      images.map((img) => {
        if (img.complete && img.naturalWidth > 0) {
          return Promise.resolve();
        }

        return new Promise<void>((resolve) => {
          img.onload = () => resolve();
          img.onerror = () => resolve();
        });
      })
    );

    const canvas = await html2canvas(elementToCapture, {
      scale: 2,
      useCORS: true,
      allowTaint: false,
      backgroundColor: null,
      logging: false
    });

    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        (result) => {
          if (result) {
            resolve(result);
          } else {
            reject(new Error('Could not create poster image.'));
          }
        },
        'image/png'
      );
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');

    link.href = url;
    link.download =
      `crumbwise-campaign-${this.result.campaign_id}.png`;

    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(() => URL.revokeObjectURL(url), 1000);

    this.notice = 'Complete poster downloaded successfully.';
    this.error = '';

  } catch (err) {
    console.error('Poster download failed:', err);
    this.error =
      'Could not download the complete poster. Please try again.';
  }
}



  private xmlEscape(value: string): string {
    return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;');
  }

  private errorText(err: HttpErrorResponse): string {
    const detail = err.error?.detail;
    if (typeof detail === 'string') return detail;
    if (err.status === 0) return 'Cannot connect to the backend. Check that FastAPI is running on port 8000.';
    return 'The request failed. Check the backend logs and try again.';
  }
}
