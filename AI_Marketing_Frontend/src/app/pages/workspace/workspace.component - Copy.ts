
import {
  ChangeDetectorRef,
  Component,
  OnInit
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/services/api.service';
import { PlatformService } from '../../core/services/platform.service';

type ModuleKey = 'products' | 'sales' | 'campaigns' | 'ai';

type FieldDef = {
  key: string;
  label: string;
  type?: string;
  placeholder?: string;
  required?: boolean;
  options?: string[];
  help?: string;
};

@Component({
  selector: 'app-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './workspace.component.html',
  styleUrl: './workspace.component.css'
})
export class WorkspaceComponent implements OnInit {
  active: ModuleKey = 'products';

  rows: Record<string, any>[] = [];
  loading = false;
  error = '';
  notice = '';

  readonly pageSize = 50;
  visibleLimit = 50;
  columns: string[] = [];

  private fieldsCacheKey: ModuleKey | null = null;
  private fieldsCache: FieldDef[] = [];

  searchText = '';
  statusText = 'active';

  showEditor = false;
  editing = false;
  recordId = '';

  form: Record<string, any> = {};

  query = '';
  aiResult: unknown = null;
  aiLoading = false;
  aiError = '';

  knowledgeText = '';
  knowledgeTitle = '';

  constructor(
    public platform: PlatformService,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadRows();
  }

  get moduleTitle(): string {
    return {
      products: 'Products & inventory',
      sales: 'Sales',
      campaigns: 'Campaigns',
      ai: 'AI business assistant'
    }[this.active];
  }

  // Cache field definitions to prevent repeated array creation
  // during Angular change detection.
  get fields(): FieldDef[] {
    if (this.fieldsCacheKey === this.active) {
      return this.fieldsCache;
    }

    this.fieldsCacheKey = this.active;
    this.fieldsCache = this.buildFieldsForActiveModule();

    return this.fieldsCache;
  }

  private buildFieldsForActiveModule(): FieldDef[] {
    if (this.active === 'products') {
      return [
        {
          key: 'product_name',
          label: 'Product name',
          required: true,
          placeholder: 'e.g. Chocolate Cake'
        },
        {
          key: 'category',
          label: 'Category',
          required: true,
          placeholder: 'e.g. Cakes'
        },
        {
          key: 'sku',
          label: 'Product code (SKU)',
          required: true,
          placeholder: 'e.g. CAKE-CHOC-001',
          help: 'A unique code to identify this product.'
        },
        {
          key: 'price',
          label: 'Selling price (₹)',
          type: 'number',
          required: true,
          placeholder: '650'
        },
        {
          key: 'stock',
          label: 'Available stock',
          type: 'number',
          placeholder: '12'
        },
        {
          key: 'description',
          label: 'Description',
          type: 'textarea',
          placeholder: 'A short product description'
        }
      ];
    }

    if (this.active === 'sales') {
      return [
        {
          key: 'product_id',
          label: 'Product ID',
          type: 'number',
          required: true,
          placeholder: 'Product ID'
        },
        {
          key: 'quantity',
          label: 'Quantity sold',
          type: 'number',
          required: true,
          placeholder: '2'
        },
        {
          key: 'unit_price',
          label: 'Price per unit (₹)',
          type: 'number',
          required: true,
          placeholder: '650'
        },
        {
          key: 'total_amount',
          label: 'Total sale amount (₹)',
          type: 'number',
          placeholder: '1300',
          help: 'Leave blank if your backend calculates it automatically.'
        },
        {
          key: 'sale_date',
          label: 'Sale date',
          type: 'datetime-local'
        }
      ];
    }

    if (this.active === 'campaigns') {
      return [
        {
          key: 'campaign_name',
          label: 'Campaign name',
          required: true,
          placeholder: 'e.g. Weekend Cake Special'
        },
        {
          key: 'objective',
          label: 'Campaign objective',
          type: 'textarea',
          required: true,
          placeholder: 'e.g. Increase weekend cake sales'
        },
        {
          key: 'platform',
          label: 'Marketing platform',
          type: 'select',
          options: [
            'Instagram',
            'Facebook',
            'WhatsApp',
            'Google'
          ],
          required: true
        },
        {
          key: 'description',
          label: 'Campaign description',
          type: 'textarea',
          placeholder: 'Describe the promotion and its audience'
        },
        {
          key: 'status',
          label: 'Status',
          type: 'select',
          options: [
            'draft',
            'active',
            'paused',
            'completed'
          ]
        },
        {
          key: 'budget',
          label: 'Budget (₹)',
          type: 'number',
          placeholder: '5000'
        },
        {
          key: 'start_date',
          label: 'Start date',
          type: 'date'
        },
        {
          key: 'end_date',
          label: 'End date',
          type: 'date'
        }
      ];
    }

    return [];
  }

  switchModule(module: ModuleKey): void {
    this.active = module;

    this.error = '';
    this.notice = '';
    this.searchText = '';
    this.showEditor = false;

    if (module !== 'ai') {
      this.loadRows();
    }
  }

  loadRows(): void {
    if (this.active === 'ai') {
      return;
    }

    this.loading = true;
    this.error = '';

    const request =
      this.active === 'products'
        ? this.api.listProducts()
        : this.active === 'sales'
          ? this.api.listSales()
          : this.api.listCampaigns();

    request.subscribe({
      next: response => {
        this.rows = this.asRows(response);
        this.visibleLimit = this.pageSize;
        this.columns = this.buildTableColumns();
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: err => {
        this.error = this.errorText(err);
        this.loading = false;
        this.rows = [];
        this.columns = [];
        this.cdr.detectChanges();
      }
    });
  }

  searchRecords(): void {
    const term = this.searchText.trim();

    if (!term) {
      this.loadRows();
      return;
    }

    this.loading = true;
    this.error = '';

    const request =
      this.active === 'products'
        ? this.api.searchProducts(term)
        : this.active === 'campaigns'
          ? this.api.searchCampaigns(term)
          : this.api.getSalesForProduct(term);

    request.subscribe({
      next: response => {
        this.rows = this.asRows(response);
        this.visibleLimit = this.pageSize;
        this.columns = this.buildTableColumns();
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: err => {
        this.error = this.errorText(err);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  filterCampaignStatus(): void {
    this.loading = true;
    this.error = '';

    this.api.getCampaignsByStatus(this.statusText).subscribe({
      next: response => {
        this.rows = this.asRows(response);
        this.visibleLimit = this.pageSize;
        this.columns = this.buildTableColumns();
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: err => {
        this.error = this.errorText(err);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  openCreate(): void {
    this.editing = false;
    this.recordId = '';
    this.form = {};

    this.error = '';
    this.notice = '';
    this.showEditor = true;
  }

  openEdit(row: Record<string, any>): void {
    this.editing = true;

    this.recordId = String(
      row['id'] ??
      row['product_id'] ??
      row['sale_id'] ??
      row['campaign_id'] ??
      ''
    );

    this.form = {};

    for (const field of this.fields) {
      this.form[field.key] = row[field.key] ?? '';
    }

    this.error = '';
    this.notice = '';
    this.showEditor = true;
  }

  closeEditor(): void {
    this.showEditor = false;
  }

  saveRecord(): void {
    const payload: Record<string, unknown> = {};

    // Include only populated values and convert numeric fields.
    for (const field of this.fields) {
      const value = this.form[field.key];

      if (
        value !== '' &&
        value !== null &&
        value !== undefined
      ) {
        payload[field.key] =
          field.type === 'number'
            ? Number(value)
            : value;
      }
    }

    // Attach the selected business to the record.
    if (
      (this.active === 'products' ||
        this.active === 'campaigns') &&
      this.platform.activeBusiness?.id
    ) {
      payload['business_id'] =
        this.platform.activeBusiness.id;
    }

    // Calculate sale amount when it is not supplied.
    if (
      this.active === 'sales' &&
      payload['total_amount'] === undefined &&
      payload['quantity'] !== undefined &&
      payload['unit_price'] !== undefined
    ) {
      payload['total_amount'] =
        Number(payload['quantity']) *
        Number(payload['unit_price']);
    }

    if (
      this.active === 'sales' &&
      payload['sale_date']
    ) {
      payload['sale_date'] = new Date(
        String(payload['sale_date'])
      ).toISOString();
    }

    this.loading = true;
    this.error = '';
    this.notice = '';

    const request =
      this.active === 'products'
        ? this.editing
          ? this.api.updateProduct(this.recordId, payload)
          : this.api.createProduct(payload)
        : this.active === 'sales'
          ? this.editing
            ? this.api.updateSale(this.recordId, payload)
            : this.api.createSale(payload)
          : this.editing
            ? this.api.updateCampaign(this.recordId, payload)
            : this.api.createCampaign(payload);

    request.subscribe({
      next: () => {
        this.loading = false;
        this.showEditor = false;

        this.notice = this.editing
          ? 'Changes saved successfully.'
          : 'Added successfully.';

        this.cdr.detectChanges();
        this.loadRows();
      },
      error: err => {
        this.error = this.errorText(err);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  deleteRow(row: Record<string, any>): void {
    const id =
      row['id'] ??
      row['product_id'] ??
      row['sale_id'] ??
      row['campaign_id'];

    if (id === undefined) {
      this.error =
        'This record has no ID field, so it cannot be deleted from here.';
      return;
    }

    if (
      !confirm(
        `Delete "${this.rowTitle(row)}"? This action cannot be undone.`
      )
    ) {
      return;
    }

    this.loading = true;
    this.error = '';

    const request =
      this.active === 'products'
        ? this.api.deleteProduct(id)
        : this.active === 'sales'
          ? this.api.deleteSale(id)
          : this.api.deleteCampaign(id);

    request.subscribe({
      next: () => {
        this.loading = false;
        this.notice = 'Record deleted.';
        this.cdr.detectChanges();
        this.loadRows();
      },
      error: err => {
        this.loading = false;
        this.error = this.errorText(err);
        this.cdr.detectChanges();
      }
    });
  }

  runAi(
    action:
      | 'performance'
      | 'index'
      | 'ask'
      | 'search'
      | 'test'
      | 'add'
  ): void {
    const businessId = this.platform.activeBusiness?.id;

    if (
      (action === 'performance' || action === 'index') &&
      !businessId
    ) {
      this.aiError = 'Choose a business before running this action.';
      return;
    }

    if (
      (action === 'ask' || action === 'search') &&
      !this.query.trim()
    ) {
      return;
    }

    if (action === 'add' && !this.knowledgeText.trim()) {
      this.aiError = 'Enter the knowledge you want to add.';
      return;
    }

    this.aiLoading = true;
    this.aiError = '';
    this.aiResult = null;

    let request;

    if (action === 'performance') {
      request = this.api.getAiPerformance(businessId!);
    } else if (action === 'index') {
      request = this.api.indexBusinessKnowledge(businessId!);
    } else if (action === 'ask') {
      request = this.api.askKnowledge(this.query.trim());
    } else if (action === 'search') {
      request = this.api.searchKnowledge(this.query.trim());
    } else if (action === 'test') {
      request = this.api.testAi();
    } else {
      request = this.api.addKnowledge({
        content: this.knowledgeText.trim(),
        title: this.knowledgeTitle.trim() || undefined,
        metadata: {
          business_id: businessId,
          business_name: this.platform.activeBusiness?.name
        }
      });
    }

    request.subscribe({
      next: response => {
        this.aiResult = response;
        this.aiLoading = false;
        this.cdr.detectChanges();
      },
      error: err => {
        this.aiError = this.errorText(err);
        this.aiLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  get aiResultText(): string {
    if (this.aiResult == null) {
      return '';
    }

    if (typeof this.aiResult === 'string') {
      return this.aiResult;
    }

    return JSON.stringify(this.aiResult, null, 2);
  }

  rowTitle(row: Record<string, any>): string {
    return String(
      row['campaign_name'] ??
      row['product_name'] ??
      row['name'] ??
      row['id'] ??
      'Record'
    );
  }

  displayValue(
    row: Record<string, any>,
    key: string
  ): string {
    const value = row[key];

    if (
      value === null ||
      value === undefined ||
      value === ''
    ) {
      return '—';
    }

    if (typeof value === 'object') {
      return Array.isArray(value)
        ? `${value.length} items`
        : 'Available';
    }

    if (
      key.toLowerCase().includes('price') ||
      key.toLowerCase().includes('amount') ||
      key.toLowerCase().includes('revenue') ||
      key.toLowerCase() === 'budget'
    ) {
      return '₹' + Number(value).toLocaleString('en-IN');
    }

    return String(value);
  }

  private buildTableColumns(): string[] {
    if (!this.rows.length) {
      return this.active === 'products'
        ? ['product_name', 'category', 'price', 'stock']
        : this.active === 'sales'
          ? ['product_id', 'quantity', 'total_amount', 'sale_date']
          : ['campaign_name', 'platform', 'status', 'budget'];
    }

    const priority =
      this.active === 'products'
        ? ['product_name', 'category', 'price', 'stock']
        : this.active === 'sales'
          ? [
              'product_name',
              'product_id',
              'quantity',
              'total_amount',
              'sale_date'
            ]
          : [
              'campaign_name',
              'platform',
              'status',
              'budget',
              'start_date',
              'end_date'
            ];

    const keys = Object.keys(this.rows[0]);

    return priority
      .filter(key => keys.includes(key))
      .concat(
        keys.filter(
          key =>
            !priority.includes(key) &&
            ![
              'id',
              'business_id',
              'owner_id',
              'created_at',
              'updated_at'
            ].includes(key)
        )
      )
      .slice(0, 5);
  }

  get visibleRows(): Record<string, any>[] {
    return this.rows.slice(0, this.visibleLimit);
  }

  get hasMoreRows(): boolean {
    return this.visibleLimit < this.rows.length;
  }

  showMoreRows(): void {
    this.visibleLimit = Math.min(
      this.visibleLimit + this.pageSize,
      this.rows.length
    );
  }

  private asRows(
    value: unknown
  ): Record<string, any>[] {
    if (Array.isArray(value)) {
      return value.filter(
        item => item && typeof item === 'object'
      ) as Record<string, any>[];
    }

    if (value && typeof value === 'object') {
      const object = value as Record<string, any>;

      for (const key of [
        'items',
        'results',
        'data',
        'products',
        'sales',
        'campaigns'
      ]) {
        if (Array.isArray(object[key])) {
          return object[key].filter(
            (item: any) =>
              item && typeof item === 'object'
          );
        }
      }

      return [object];
    }

    return [];
  }

  private errorText(err: HttpErrorResponse): string {
    const detail = err.error?.detail;

    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map(
          (item: {
            msg?: string;
            loc?: Array<string | number>;
          }) => {
            const location = item.loc
              ?.filter(
                value =>
                  value !== 'body' &&
                  value !== 'query' &&
                  value !== 'path'
              )
              .join(' → ');

            return location
              ? `${location}: ${item.msg ?? 'Invalid value'}`
              : item.msg ?? '';
          }
        )
        .filter(Boolean)
        .join(' · ');
    }

    if (err.status === 0) {
      return 'Could not connect to FastAPI. Check that the server is running and CORS is enabled.';
    }

    return `The request failed (${err.status}). ${
      err.error?.message ??
      'Please check the fields required by your backend.'
    }`;
  }
}
