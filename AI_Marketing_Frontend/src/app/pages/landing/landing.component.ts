import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PublicShellComponent } from '../../shared/public-shell.component';
@Component({selector:'app-landing',standalone:true,imports:[RouterLink,PublicShellComponent],templateUrl:'./landing.component.html',styleUrl:'./landing.component.css'})
export class LandingComponent {}
