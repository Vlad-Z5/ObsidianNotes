# Performance Capacity Planning

**Focus:** Infrastructure capacity forecasting, resource growth modeling, performance trend analysis, cost optimization strategies, scalability planning, and proactive capacity management.

## Core Capacity Planning Principles

### 1. Capacity Planning Methodologies
- **Trend Analysis**: Historical performance data analysis
- **Predictive Modeling**: Future resource requirement forecasting
- **Simulation Modeling**: What-if scenario analysis
- **Benchmarking**: Performance baseline establishment
- **Growth Planning**: Scalability roadmap development

### 2. Resource Planning Categories
- **Compute Resources**: CPU, memory, processing power
- **Storage Capacity**: Disk space, I/O performance, backup needs
- **Network Bandwidth**: Traffic volume, latency requirements
- **Database Performance**: Query throughput, connection limits
- **Application Scaling**: User load, feature adoption rates

### 3. Planning Horizons
- **Short-term**: 1-3 months operational planning
- **Medium-term**: 6-12 months tactical planning
- **Long-term**: 1-3 years strategic planning
- **Peak Planning**: Event-driven capacity requirements
- **Disaster Recovery**: Failover capacity needs

### 4. Optimization Strategies
- **Right-sizing**: Optimal resource allocation
- **Auto-scaling**: Dynamic capacity adjustment
- **Load Distribution**: Geographic and temporal spreading
- **Cost Optimization**: Performance per dollar analysis

## Enterprise Capacity Planning Framework

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
import scipy.stats as stats
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import sqlite3
import asyncio
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

@dataclass
class ResourceMetric:
    timestamp: float
    metric_name: str
    value: float
    resource_type: str
    resource_id: str
    unit: str
    tags: Dict[str, str]

@dataclass
class CapacityForecast:
    resource_type: str
    metric_name: str
    current_value: float
    predicted_values: List[float]
    forecast_dates: List[str]
    confidence_interval: Tuple[List[float], List[float]]
    model_accuracy: float
    trend_direction: str
    growth_rate: float

@dataclass
class CapacityRecommendation:
    resource_type: str
    recommendation_type: str
    description: str
    urgency: str
    cost_impact: str
    timeline: str
    action_items: List[str]

class CapacityDataCollector:
    """Collect and store capacity planning metrics"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.db_connection = self._setup_database()
        self.logger = logging.getLogger(__name__)
        
    def _setup_database(self) -> sqlite3.Connection:
        """Initialize metrics database"""
        conn = sqlite3.connect(self.config.get('db_path', 'capacity_metrics.db'))
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                metric_name TEXT,
                value REAL,
                resource_type TEXT,
                resource_id TEXT,
                unit TEXT,
                tags TEXT
            )
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp_metric 
            ON metrics(timestamp, metric_name, resource_type)
        ''')
        
        conn.commit()
        return conn
    
    def store_metric(self, metric: ResourceMetric):
        """Store resource metric in database"""
        self.db_connection.execute(
            'INSERT INTO metrics VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)',
            (
                metric.timestamp,
                metric.metric_name,
                metric.value,
                metric.resource_type,
                metric.resource_id,
                metric.unit,
                json.dumps(metric.tags)
            )
        )
        self.db_connection.commit()
    
    def get_historical_data(self, resource_type: str, metric_name: str, 
                          days: int = 90) -> pd.DataFrame:
        """Retrieve historical data for analysis"""
        start_time = time.time() - (days * 24 * 3600)
        
        query = '''
            SELECT timestamp, value, resource_id, tags
            FROM metrics
            WHERE resource_type = ? AND metric_name = ? AND timestamp >= ?
            ORDER BY timestamp
        '''
        
        cursor = self.db_connection.execute(query, (resource_type, metric_name, start_time))
        results = cursor.fetchall()
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results, columns=['timestamp', 'value', 'resource_id', 'tags'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        return df

class ForecastingModel(ABC):
    """Abstract base class for forecasting models"""
    
    @abstractmethod
    def fit(self, data: pd.DataFrame) -> None:
        pass
    
    @abstractmethod
    def predict(self, periods: int) -> Tuple[List[float], Tuple[List[float], List[float]]]:
        pass
    
    @abstractmethod
    def get_accuracy_metrics(self) -> Dict[str, float]:
        pass

class LinearTrendModel(ForecastingModel):
    """Linear trend forecasting model"""
    
    def __init__(self):
        self.model = LinearRegression()
        self.fitted = False
        self.accuracy_metrics = {}
        
    def fit(self, data: pd.DataFrame) -> None:
        """Fit linear trend model"""
        if len(data) < 10:
            raise ValueError("Insufficient data for forecasting (minimum 10 points required)")
        
        # Prepare features (time-based)
        data_sorted = data.sort_values('timestamp')
        
        # Use time elapsed as feature
        start_time = data_sorted['timestamp'].iloc[0]
        X = (data_sorted['timestamp'] - start_time).values.reshape(-1, 1)
        y = data_sorted['value'].values
        
        # Split for validation
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Fit model
        self.model.fit(X_train, y_train)
        
        # Calculate accuracy metrics
        y_pred = self.model.predict(X_test)
        self.accuracy_metrics = {
            'r2_score': r2_score(y_test, y_pred),
            'mean_absolute_error': mean_absolute_error(y_test, y_pred),
            'mean_absolute_percentage_error': np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        }
        
        self.start_time = start_time
        self.last_time = data_sorted['timestamp'].iloc[-1]
        self.fitted = True
    
    def predict(self, periods: int) -> Tuple[List[float], Tuple[List[float], List[float]]]:
        """Generate linear trend predictions"""
        if not self.fitted:
            raise ValueError("Model must be fitted before prediction")
        
        # Generate future time points
        time_interval = 24 * 3600  # Daily intervals
        future_times = []
        
        for i in range(1, periods + 1):
            future_time = self.last_time + (i * time_interval)
            future_times.append(future_time - self.start_time)
        
        future_X = np.array(future_times).reshape(-1, 1)
        predictions = self.model.predict(future_X)
        
        # Calculate confidence intervals (simplified)
        # In production, use proper statistical methods
        mse = self.accuracy_metrics.get('mean_absolute_error', 0)
        confidence_factor = 1.96  # 95% confidence
        
        lower_bound = predictions - (confidence_factor * mse)
        upper_bound = predictions + (confidence_factor * mse)
        
        return predictions.tolist(), (lower_bound.tolist(), upper_bound.tolist())
    
    def get_accuracy_metrics(self) -> Dict[str, float]:
        """Get model accuracy metrics"""
        return self.accuracy_metrics

class PolynomialTrendModel(ForecastingModel):
    """Polynomial trend forecasting model"""
    
    def __init__(self, degree: int = 2):
        self.degree = degree
        self.model = LinearRegression()
        self.poly_features = PolynomialFeatures(degree=degree)
        self.fitted = False
        self.accuracy_metrics = {}
        
    def fit(self, data: pd.DataFrame) -> None:
        """Fit polynomial trend model"""
        if len(data) < 20:
            raise ValueError("Insufficient data for polynomial forecasting (minimum 20 points required)")
        
        # Prepare features
        data_sorted = data.sort_values('timestamp')
        start_time = data_sorted['timestamp'].iloc[0]
        X = (data_sorted['timestamp'] - start_time).values.reshape(-1, 1)
        y = data_sorted['value'].values
        
        # Transform features
        X_poly = self.poly_features.fit_transform(X)
        
        # Split for validation
        X_train, X_test, y_train, y_test = train_test_split(X_poly, y, test_size=0.2, random_state=42)
        
        # Fit model
        self.model.fit(X_train, y_train)
        
        # Calculate accuracy metrics
        y_pred = self.model.predict(X_test)
        self.accuracy_metrics = {
            'r2_score': r2_score(y_test, y_pred),
            'mean_absolute_error': mean_absolute_error(y_test, y_pred),
            'mean_absolute_percentage_error': np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        }
        
        self.start_time = start_time
        self.last_time = data_sorted['timestamp'].iloc[-1]
        self.fitted = True
    
    def predict(self, periods: int) -> Tuple[List[float], Tuple[List[float], List[float]]]:
        """Generate polynomial trend predictions"""
        if not self.fitted:
            raise ValueError("Model must be fitted before prediction")
        
        # Generate future time points
        time_interval = 24 * 3600
        future_times = []
        
        for i in range(1, periods + 1):
            future_time = self.last_time + (i * time_interval)
            future_times.append(future_time - self.start_time)
        
        future_X = np.array(future_times).reshape(-1, 1)
        future_X_poly = self.poly_features.transform(future_X)
        predictions = self.model.predict(future_X_poly)
        
        # Calculate confidence intervals
        mse = self.accuracy_metrics.get('mean_absolute_error', 0)
        confidence_factor = 1.96
        
        lower_bound = predictions - (confidence_factor * mse)
        upper_bound = predictions + (confidence_factor * mse)
        
        return predictions.tolist(), (lower_bound.tolist(), upper_bound.tolist())
    
    def get_accuracy_metrics(self) -> Dict[str, float]:
        return self.accuracy_metrics

class SeasonalDecompositionModel(ForecastingModel):
    """Seasonal decomposition forecasting model"""
    
    def __init__(self, seasonal_periods: int = 7):
        self.seasonal_periods = seasonal_periods
        self.fitted = False
        self.trend_component = None
        self.seasonal_component = None
        self.residual_component = None
        self.accuracy_metrics = {}
        
    def fit(self, data: pd.DataFrame) -> None:
        """Fit seasonal decomposition model"""
        if len(data) < self.seasonal_periods * 3:
            raise ValueError(f"Insufficient data for seasonal analysis (minimum {self.seasonal_periods * 3} points required)")
        
        # Prepare time series
        data_sorted = data.sort_values('timestamp')
        ts = data_sorted.set_index('datetime')['value']
        ts = ts.asfreq('D', method='pad')  # Daily frequency
        
        # Perform seasonal decomposition (simplified)
        self._decompose_series(ts)
        
        self.ts = ts
        self.fitted = True
    
    def _decompose_series(self, ts: pd.Series):
        """Decompose time series into trend, seasonal, and residual components"""
        # Simple moving average for trend
        trend = ts.rolling(window=self.seasonal_periods, center=True).mean()
        
        # Seasonal component
        detrended = ts - trend
        seasonal = detrended.groupby(detrended.index.dayofweek).mean()
        
        # Residual component
        seasonal_extended = pd.Series(index=ts.index)
        for i, value in enumerate(ts.values):
            seasonal_extended.iloc[i] = seasonal.iloc[ts.index[i].dayofweek]
        
        residual = ts - trend - seasonal_extended
        
        self.trend_component = trend
        self.seasonal_component = seasonal
        self.residual_component = residual
        
        # Calculate accuracy metrics
        fitted_values = trend + seasonal_extended
        mask = ~np.isnan(fitted_values)
        
        if mask.sum() > 0:
            actual = ts[mask]
            fitted = fitted_values[mask]
            
            self.accuracy_metrics = {
                'r2_score': r2_score(actual, fitted),
                'mean_absolute_error': mean_absolute_error(actual, fitted),
                'mean_absolute_percentage_error': np.mean(np.abs((actual - fitted) / actual)) * 100
            }
    
    def predict(self, periods: int) -> Tuple[List[float], Tuple[List[float], List[float]]]:
        """Generate seasonal forecast predictions"""
        if not self.fitted:
            raise ValueError("Model must be fitted before prediction")
        
        # Extend trend (linear extrapolation)
        trend_slope = self.trend_component.diff().mean()
        last_trend = self.trend_component.dropna().iloc[-1]
        
        predictions = []
        for i in range(1, periods + 1):
            trend_value = last_trend + (i * trend_slope)
            seasonal_value = self.seasonal_component.iloc[i % self.seasonal_periods]
            prediction = trend_value + seasonal_value
            predictions.append(prediction)
        
        # Calculate confidence intervals
        mse = self.accuracy_metrics.get('mean_absolute_error', 0)
        confidence_factor = 1.96
        
        lower_bound = [p - (confidence_factor * mse) for p in predictions]
        upper_bound = [p + (confidence_factor * mse) for p in predictions]
        
        return predictions, (lower_bound, upper_bound)
    
    def get_accuracy_metrics(self) -> Dict[str, float]:
        return self.accuracy_metrics

class CapacityPlanningEngine:
    """Enterprise capacity planning engine"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.data_collector = CapacityDataCollector(config)
        self.forecasting_models = self._initialize_models()
        self.forecasts = {}
        self.recommendations = []
        self.logger = logging.getLogger(__name__)
        
    def _initialize_models(self) -> Dict[str, ForecastingModel]:
        """Initialize forecasting models"""
        models = {
            'linear': LinearTrendModel(),
            'polynomial': PolynomialTrendModel(degree=2),
            'seasonal': SeasonalDecompositionModel(seasonal_periods=7)
        }
        
        return models
    
    def analyze_resource_trends(self, resource_type: str, metric_name: str, 
                              analysis_days: int = 90) -> Dict[str, Any]:
        """Analyze historical trends for a specific resource metric"""
        self.logger.info(f"Analyzing trends for {resource_type}.{metric_name}")
        
        # Get historical data
        historical_data = self.data_collector.get_historical_data(
            resource_type, metric_name, analysis_days
        )
        
        if historical_data.empty:
            return {'error': 'No historical data available'}
        
        # Calculate basic statistics
        stats_analysis = self._calculate_trend_statistics(historical_data)
        
        # Detect patterns
        patterns = self._detect_patterns(historical_data)
        
        # Identify anomalies
        anomalies = self._detect_anomalies(historical_data)
        
        return {
            'resource_type': resource_type,
            'metric_name': metric_name,
            'data_points': len(historical_data),
            'analysis_period_days': analysis_days,
            'statistics': stats_analysis,
            'patterns': patterns,
            'anomalies': anomalies
        }
    
    def generate_capacity_forecast(self, resource_type: str, metric_name: str,
                                 forecast_periods: int = 90, 
                                 model_type: str = 'auto') -> CapacityForecast:
        """Generate capacity forecast for specified resource"""
        self.logger.info(f"Generating forecast for {resource_type}.{metric_name}")
        
        # Get historical data
        historical_data = self.data_collector.get_historical_data(resource_type, metric_name)
        
        if historical_data.empty:
            raise ValueError("No historical data available for forecasting")
        
        # Select best model
        if model_type == 'auto':
            selected_model = self._select_best_model(historical_data)
        else:
            selected_model = self.forecasting_models.get(model_type)
            if not selected_model:
                raise ValueError(f"Unknown model type: {model_type}")
        
        # Fit model and generate predictions
        selected_model.fit(historical_data)
        predictions, confidence_interval = selected_model.predict(forecast_periods)
        
        # Generate forecast dates
        start_date = datetime.now()
        forecast_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') 
                         for i in range(1, forecast_periods + 1)]
        
        # Calculate trend metrics
        current_value = historical_data['value'].iloc[-1]
        trend_direction, growth_rate = self._calculate_trend_metrics(
            current_value, predictions
        )
        
        forecast = CapacityForecast(
            resource_type=resource_type,
            metric_name=metric_name,
            current_value=current_value,
            predicted_values=predictions,
            forecast_dates=forecast_dates,
            confidence_interval=confidence_interval,
            model_accuracy=selected_model.get_accuracy_metrics().get('r2_score', 0),
            trend_direction=trend_direction,
            growth_rate=growth_rate
        )
        
        # Store forecast
        forecast_key = f"{resource_type}.{metric_name}"
        self.forecasts[forecast_key] = forecast
        
        return forecast
    
    def _select_best_model(self, data: pd.DataFrame) -> ForecastingModel:
        """Select best forecasting model based on data characteristics"""
        model_scores = {}
        
        # Test each model
        for model_name, model in self.forecasting_models.items():
            try:
                # Split data for validation
                split_point = int(len(data) * 0.8)
                train_data = data.iloc[:split_point]
                test_data = data.iloc[split_point:]
                
                if len(train_data) < 10:
                    continue
                
                # Fit and evaluate model
                model.fit(train_data)
                
                # Calculate validation score
                test_periods = len(test_data)
                if test_periods > 0:
                    predictions, _ = model.predict(test_periods)
                    actual_values = test_data['value'].values[:len(predictions)]
                    
                    if len(actual_values) > 0:
                        score = r2_score(actual_values, predictions)
                        model_scores[model_name] = score
                
            except Exception as e:
                self.logger.warning(f"Model {model_name} failed validation: {e}")
        
        # Select best model
        if model_scores:
            best_model_name = max(model_scores.keys(), key=model_scores.get)
            self.logger.info(f"Selected model: {best_model_name} (score: {model_scores[best_model_name]:.3f})")
            return self.forecasting_models[best_model_name]
        else:
            # Fallback to linear model
            return self.forecasting_models['linear']
    
    def _calculate_trend_statistics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate trend statistics"""
        values = data['value'].values
        
        return {
            'mean': np.mean(values),
            'median': np.median(values),
            'std_dev': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'p95': np.percentile(values, 95),
            'p99': np.percentile(values, 99),
            'coefficient_of_variation': np.std(values) / np.mean(values) if np.mean(values) > 0 else 0
        }
    
    def _detect_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect patterns in time series data"""
        data_sorted = data.sort_values('timestamp')
        values = data_sorted['value'].values
        
        patterns = {}
        
        # Trend detection
        if len(values) > 1:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                range(len(values)), values
            )
            
            patterns['linear_trend'] = {
                'slope': slope,
                'r_squared': r_value ** 2,
                'p_value': p_value,
                'significant': p_value < 0.05
            }
        
        # Seasonality detection (simplified)
        if len(values) >= 14:  # At least 2 weeks of data
            day_of_week_pattern = self._analyze_weekly_pattern(data_sorted)
            patterns['weekly_seasonality'] = day_of_week_pattern
        
        return patterns
    
    def _analyze_weekly_pattern(self, data: pd.DataFrame) -> Dict[str, float]:
        """Analyze weekly seasonality pattern"""
        data['day_of_week'] = data['datetime'].dt.dayofweek
        weekly_means = data.groupby('day_of_week')['value'].mean()
        
        # Calculate coefficient of variation for weekly pattern
        weekly_cv = weekly_means.std() / weekly_means.mean() if weekly_means.mean() > 0 else 0
        
        return {
            'coefficient_of_variation': weekly_cv,
            'significant_pattern': weekly_cv > 0.1,
            'day_of_week_means': weekly_means.to_dict()
        }
    
    def _detect_anomalies(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in time series data"""
        values = data['value'].values
        
        # Use z-score method for anomaly detection
        z_scores = np.abs(stats.zscore(values))
        threshold = 3.0
        
        anomalies = []
        anomaly_indices = np.where(z_scores > threshold)[0]
        
        for idx in anomaly_indices:
            anomalies.append({
                'timestamp': data.iloc[idx]['timestamp'],
                'datetime': data.iloc[idx]['datetime'].isoformat(),
                'value': values[idx],
                'z_score': z_scores[idx],
                'deviation_from_mean': values[idx] - np.mean(values)
            })
        
        return anomalies
    
    def _calculate_trend_metrics(self, current_value: float, 
                               predictions: List[float]) -> Tuple[str, float]:
        """Calculate trend direction and growth rate"""
        if not predictions:
            return 'stable', 0.0
        
        final_prediction = predictions[-1]
        
        # Calculate growth rate
        if current_value > 0:
            growth_rate = ((final_prediction - current_value) / current_value) * 100
        else:
            growth_rate = 0.0
        
        # Determine trend direction
        if growth_rate > 5:
            trend_direction = 'increasing'
        elif growth_rate < -5:
            trend_direction = 'decreasing'
        else:
            trend_direction = 'stable'
        
        return trend_direction, growth_rate
    
    def generate_capacity_recommendations(self, 
                                        forecasts: List[CapacityForecast]) -> List[CapacityRecommendation]:
        """Generate capacity planning recommendations"""
        recommendations = []
        
        for forecast in forecasts:
            recs = self._analyze_forecast_for_recommendations(forecast)
            recommendations.extend(recs)
        
        # Prioritize recommendations
        recommendations.sort(key=lambda x: self._get_urgency_priority(x.urgency), reverse=True)
        
        self.recommendations = recommendations
        return recommendations
    
    def _analyze_forecast_for_recommendations(self, 
                                           forecast: CapacityForecast) -> List[CapacityRecommendation]:
        """Analyze individual forecast for recommendations"""
        recommendations = []
        
        # Growth rate analysis
        if forecast.growth_rate > 50:  # > 50% growth expected
            recommendations.append(CapacityRecommendation(
                resource_type=forecast.resource_type,
                recommendation_type='capacity_expansion',
                description=f"High growth rate ({forecast.growth_rate:.1f}%) predicted for {forecast.metric_name}",
                urgency='HIGH',
                cost_impact='HIGH',
                timeline='1-3 months',
                action_items=[
                    'Plan infrastructure scaling',
                    'Evaluate auto-scaling options',
                    'Budget for resource expansion',
                    'Test scaling procedures'
                ]
            ))
        elif forecast.growth_rate > 20:  # > 20% growth
            recommendations.append(CapacityRecommendation(
                resource_type=forecast.resource_type,
                recommendation_type='capacity_monitoring',
                description=f"Moderate growth rate ({forecast.growth_rate:.1f}%) predicted for {forecast.metric_name}",
                urgency='MEDIUM',
                cost_impact='MEDIUM',
                timeline='3-6 months',
                action_items=[
                    'Enhanced monitoring setup',
                    'Evaluate current limits',
                    'Plan capacity testing',
                    'Review scaling policies'
                ]
            ))
        
        # Capacity utilization analysis
        current_utilization = self._estimate_utilization(forecast)
        
        if current_utilization > 80:
            recommendations.append(CapacityRecommendation(
                resource_type=forecast.resource_type,
                recommendation_type='immediate_attention',
                description=f"Current utilization ({current_utilization:.1f}%) approaching limits for {forecast.metric_name}",
                urgency='CRITICAL',
                cost_impact='HIGH',
                timeline='Immediate',
                action_items=[
                    'Immediate capacity review',
                    'Emergency scaling procedures',
                    'Performance optimization',
                    'Load balancing review'
                ]
            ))
        
        # Model accuracy considerations
        if forecast.model_accuracy < 0.7:  # Low model accuracy
            recommendations.append(CapacityRecommendation(
                resource_type=forecast.resource_type,
                recommendation_type='data_quality',
                description=f"Low forecast accuracy ({forecast.model_accuracy:.2f}) for {forecast.metric_name}",
                urgency='LOW',
                cost_impact='LOW',
                timeline='Ongoing',
                action_items=[
                    'Improve data collection',
                    'Enhanced monitoring',
                    'Data quality validation',
                    'Model refinement'
                ]
            ))
        
        return recommendations
    
    def _estimate_utilization(self, forecast: CapacityForecast) -> float:
        """Estimate current resource utilization percentage"""
        # This is a simplified estimation
        # In production, this would be based on actual capacity limits
        
        metric_thresholds = {
            'cpu_usage': 100,
            'memory_usage': 100,
            'disk_usage': 100,
            'network_usage': 1000,  # Mbps
            'connections': 10000,
            'requests_per_second': 1000
        }
        
        threshold = metric_thresholds.get(forecast.metric_name, 100)
        return (forecast.current_value / threshold) * 100
    
    def _get_urgency_priority(self, urgency: str) -> int:
        """Get numerical priority for urgency levels"""
        priorities = {
            'CRITICAL': 4,
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1
        }
        return priorities.get(urgency, 0)
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive capacity planning report"""
        current_time = time.time()
        
        # Collect all forecasts
        all_forecasts = list(self.forecasts.values())
        
        # Generate recommendations if not already done
        if not self.recommendations and all_forecasts:
            self.generate_capacity_recommendations(all_forecasts)
        
        # Summary statistics
        growth_rates = [f.growth_rate for f in all_forecasts if f.growth_rate is not None]
        avg_growth_rate = np.mean(growth_rates) if growth_rates else 0
        
        high_growth_resources = len([f for f in all_forecasts if f.growth_rate > 20])
        critical_recommendations = len([r for r in self.recommendations if r.urgency == 'CRITICAL'])
        
        report = {
            'report_timestamp': datetime.fromtimestamp(current_time).isoformat(),
            'summary': {
                'total_forecasts': len(all_forecasts),
                'average_growth_rate': avg_growth_rate,
                'high_growth_resources': high_growth_resources,
                'total_recommendations': len(self.recommendations),
                'critical_recommendations': critical_recommendations
            },
            'forecasts': [asdict(f) for f in all_forecasts],
            'recommendations': [asdict(r) for r in self.recommendations],
            'key_insights': self._generate_key_insights(all_forecasts, self.recommendations)
        }
        
        return report
    
    def _generate_key_insights(self, forecasts: List[CapacityForecast], 
                             recommendations: List[CapacityRecommendation]) -> List[str]:
        """Generate key insights from analysis"""
        insights = []
        
        # Growth trends
        high_growth = [f for f in forecasts if f.growth_rate > 30]
        if high_growth:
            insights.append(f"{len(high_growth)} resources showing high growth (>30%) requiring attention")
        
        # Resource types with concerns
        resource_concerns = {}
        for rec in recommendations:
            if rec.urgency in ['CRITICAL', 'HIGH']:
                resource_concerns[rec.resource_type] = resource_concerns.get(rec.resource_type, 0) + 1
        
        for resource_type, count in resource_concerns.items():
            if count > 1:
                insights.append(f"{resource_type} resources need immediate capacity planning attention")
        
        # Model accuracy insights
        low_accuracy_forecasts = [f for f in forecasts if f.model_accuracy < 0.6]
        if low_accuracy_forecasts:
            insights.append(f"{len(low_accuracy_forecasts)} forecasts have low accuracy - improve data collection")
        
        # General recommendations
        if any(r.urgency == 'CRITICAL' for r in recommendations):
            insights.append("Critical capacity issues identified - immediate action required")
        
        if not insights:
            insights.append("No immediate capacity concerns identified - continue monitoring")
        
        return insights

# Configuration Example
capacity_planning_config = {
    'db_path': 'capacity_planning.db',
    'analysis_days': 90,
    'forecast_periods': 90,
    'models': {
        'linear_trend': {'enabled': True},
        'polynomial_trend': {'enabled': True, 'degree': 2},
        'seasonal_decomposition': {'enabled': True, 'periods': 7}
    },
    'thresholds': {
        'high_growth_rate': 20,
        'critical_utilization': 80,
        'low_accuracy': 0.6
    }
}

# Usage Example
def simulate_historical_data(engine: CapacityPlanningEngine):
    """Simulate historical data for demonstration"""
    import random
    
    # Simulate 90 days of CPU usage data
    base_time = time.time() - (90 * 24 * 3600)
    
    for i in range(90):
        timestamp = base_time + (i * 24 * 3600)
        
        # Simulate growing CPU usage with some seasonality
        base_value = 30 + (i * 0.5)  # Growing trend
        seasonal_factor = 10 * np.sin(2 * np.pi * i / 7)  # Weekly pattern
        noise = random.uniform(-5, 5)
        
        cpu_usage = max(0, base_value + seasonal_factor + noise)
        
        metric = ResourceMetric(
            timestamp=timestamp,
            metric_name='cpu_usage',
            value=cpu_usage,
            resource_type='compute',
            resource_id='web-server-01',
            unit='percent',
            tags={'environment': 'production', 'service': 'web'}
        )
        
        engine.data_collector.store_metric(metric)

async def main():
    # Initialize capacity planning engine
    engine = CapacityPlanningEngine(capacity_planning_config)
    
    # Simulate historical data
    simulate_historical_data(engine)
    
    # Analyze trends
    trend_analysis = engine.analyze_resource_trends('compute', 'cpu_usage')
    print("Trend Analysis:")
    print(json.dumps(trend_analysis, indent=2, default=str))
    
    # Generate forecast
    forecast = engine.generate_capacity_forecast('compute', 'cpu_usage', 90)
    print(f"\nForecast - Current: {forecast.current_value:.1f}%, "
          f"Growth: {forecast.growth_rate:.1f}%, "
          f"Trend: {forecast.trend_direction}")
    
    # Generate recommendations
    recommendations = engine.generate_capacity_recommendations([forecast])
    print(f"\nRecommendations ({len(recommendations)}):")
    for rec in recommendations:
        print(f"- {rec.urgency}: {rec.description}")
    
    # Generate comprehensive report
    report = engine.generate_comprehensive_report()
    
    # Save report
    with open('capacity_planning_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nGenerated comprehensive capacity planning report")
    print(f"Key Insights: {len(report['key_insights'])}")
    for insight in report['key_insights']:
        print(f"- {insight}")

if __name__ == "__main__":
    asyncio.run(main())
```

This comprehensive capacity planning framework provides:

1. **Forecasting Models**: Linear, polynomial, and seasonal decomposition models
2. **Trend Analysis**: Pattern detection, anomaly identification, seasonality analysis
3. **Growth Prediction**: Multi-period forecasting with confidence intervals
4. **Recommendation Engine**: Automated capacity planning recommendations
5. **Resource Monitoring**: Historical data collection and storage
6. **Performance Analytics**: Model accuracy and validation metrics
7. **Comprehensive Reporting**: Executive-level capacity planning reports
8. **Proactive Planning**: Early warning systems and capacity alerts

The system enables infrastructure teams to make data-driven capacity planning decisions with predictive analytics and automated recommendations for enterprise environments.