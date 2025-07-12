import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

// Angular Material Modules
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatTabsModule } from '@angular/material/tabs';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatRadioModule } from '@angular/material/radio';
import { MatSliderModule } from '@angular/material/slider';

// Chart.js
import { NgChartsModule } from 'ng2-charts';

// Components
import { AppComponent } from './app.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { PortfolioComponent } from './components/portfolio/portfolio.component';
import { HoldingsComponent } from './components/holdings/holdings.component';
import { StockScreenerComponent } from './components/stock-screener/stock-screener.component';
import { AnalyticsComponent } from './components/analytics/analytics.component';
import { LoginComponent } from './components/auth/login.component';
import { NavigationComponent } from './components/navigation/navigation.component';
import { AddHoldingDialogComponent } from './components/dialogs/add-holding-dialog.component';
import { StockDetailsComponent } from './components/stock-details/stock-details.component';

// Services
import { AuthService } from './services/auth.service';
import { PortfolioService } from './services/portfolio.service';
import { StockService } from './services/stock.service';
import { AnalyticsService } from './services/analytics.service';
import { ScreeningService } from './services/screening.service';
import { AuthInterceptor } from './interceptors/auth.interceptor';

// Guards
import { AuthGuard } from './guards/auth.guard';

// Routes
import { routes } from './app-routing.module';

@NgModule({
  declarations: [
    AppComponent,
    DashboardComponent,
    PortfolioComponent,
    HoldingsComponent,
    StockScreenerComponent,
    AnalyticsComponent,
    LoginComponent,
    NavigationComponent,
    AddHoldingDialogComponent,
    StockDetailsComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    ReactiveFormsModule,
    FormsModule,
    RouterModule.forRoot(routes),
    
    // Angular Material
    MatToolbarModule,
    MatSidenavModule,
    MatButtonModule,
    MatIconModule,
    MatListModule,
    MatCardModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatDialogModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatChipsModule,
    MatTabsModule,
    MatExpansionModule,
    MatMenuModule,
    MatTooltipModule,
    MatCheckboxModule,
    MatRadioModule,
    MatSliderModule,
    
    // Charts
    NgChartsModule
  ],
  providers: [
    AuthService,
    PortfolioService,
    StockService,
    AnalyticsService,
    ScreeningService,
    AuthGuard,
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { } 