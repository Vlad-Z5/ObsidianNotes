# AWS Cost Explorer - Enterprise FinOps & Cost Management Platform

AWS Cost Explorer provides comprehensive cost visibility, optimization recommendations, and automated financial operations for enterprise-scale cloud cost management. This advanced platform enables organizations to implement FinOps practices, automate cost optimization, and maintain financial governance across multi-account environments.

## Enterprise FinOps Automation Framework

```python
import boto3
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from decimal import Decimal
import asyncio
from concurrent.futures import ThreadPoolExecutor

class TimeUnit(Enum):
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    HOURLY = "HOURLY"

class Granularity(Enum):
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    HOURLY = "HOURLY"

class GroupDefinitionType(Enum):
    DIMENSION = "DIMENSION"
    TAG = "TAG"
    COST_CATEGORY = "COST_CATEGORY"

class Metric(Enum):
    BLENDED_COST = "BlendedCost"
    UNBLENDED_COST = "UnblendedCost"
    AMORTIZED_COST = "AmortizedCost"
    NET_UNBLENDED_COST = "NetUnblendedCost"
    NET_AMORTIZED_COST = "NetAmortizedCost"
    USAGE_QUANTITY = "UsageQuantity"
    NORMALIZED_USAGE_AMOUNT = "NormalizedUsageAmount"

class RecommendationType(Enum):
    RIGHTSIZING = "RightsizingRecommendation"
    SAVINGS_PLAN = "SavingsPlansRecommendation"
    RESERVED_INSTANCE = "ReservedInstanceRecommendation"

@dataclass
class CostAnalysisRequest:
    start_date: str
    end_date: str
    granularity: Granularity
    metrics: List[Metric]
    group_by: List[Dict[str, str]] = field(default_factory=list)
    filter_expression: Dict[str, Any] = field(default_factory=dict)
    next_page_token: Optional[str] = None

@dataclass
class BudgetConfig:
    budget_name: str
    budget_limit: Decimal
    time_unit: TimeUnit
    budget_type: str = "COST"
    cost_filters: Dict[str, List[str]] = field(default_factory=dict)
    time_period: Dict[str, str] = field(default_factory=dict)
    calculated_spend: Dict[str, Decimal] = field(default_factory=dict)
    subscribers: List[Dict[str, str]] = field(default_factory=list)
    notifications: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class CostOptimizationOpportunity:
    recommendation_type: RecommendationType
    resource_id: str
    service: str
    region: str
    current_cost: Decimal
    optimized_cost: Decimal
    potential_savings: Decimal
    savings_percentage: float
    implementation_effort: str
    risk_level: str
    recommendation_details: Dict[str, Any]
    priority_score: int

class EnterpriseCostExplorerManager:
    """
    Enterprise AWS Cost Explorer manager with advanced FinOps automation,
    cost optimization recommendations, and financial governance.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.ce_client = boto3.client('ce', region_name=region)
        self.budgets_client = boto3.client('budgets', region_name=region)
        self.organizations_client = boto3.client('organizations', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        self.sns_client = boto3.client('sns', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.region = region
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Cost optimization thresholds
        self.optimization_thresholds = self._initialize_optimization_thresholds()
        
    def _initialize_optimization_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Initialize cost optimization thresholds and policies"""
        
        return {
            "rightsizing": {
                "minimum_savings": 50.0,  # USD per month
                "minimum_savings_percentage": 15.0,  # 15%
                "cpu_utilization_threshold": 20.0,  # 20%
                "memory_utilization_threshold": 20.0,  # 20%
                "evaluation_period_days": 14
            },
            "reserved_instances": {
                "minimum_savings": 100.0,  # USD per month
                "minimum_usage_hours": 8760 * 0.7,  # 70% of year
                "payment_option": "Partial Upfront",
                "term_length": "1yr"
            },
            "savings_plans": {
                "minimum_savings": 200.0,  # USD per month
                "minimum_commitment": 1000.0,  # USD per month
                "payment_option": "Partial Upfront",
                "term_length": "1yr",
                "plan_type": "Compute"
            },
            "storage": {
                "s3_intelligent_tiering_threshold": 128000,  # 128KB
                "ebs_gp2_to_gp3_threshold": 100.0,  # USD per month
                "snapshot_retention_days": 30
            }
        }
    
    def get_comprehensive_cost_analysis(self, 
                                      analysis_request: CostAnalysisRequest,
                                      include_forecast: bool = True) -> Dict[str, Any]:
        """Get comprehensive cost analysis with trends and forecasting"""
        
        try:
            # Get cost and usage data
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': analysis_request.start_date,
                    'End': analysis_request.end_date
                },
                Granularity=analysis_request.granularity.value,
                Metrics=[metric.value for metric in analysis_request.metrics],
                GroupBy=analysis_request.group_by,
                Filter=analysis_request.filter_expression if analysis_request.filter_expression else None,
                NextPageToken=analysis_request.next_page_token
            )
            
            # Process cost data
            cost_analysis = self._process_cost_data(response)
            
            # Get dimension values for enhanced analysis
            dimension_analysis = self._get_dimension_analysis(analysis_request)
            
            # Generate cost forecast if requested
            forecast_data = {}
            if include_forecast:
                forecast_data = self._generate_cost_forecast(analysis_request)
            
            # Identify cost anomalies
            anomalies = self._detect_cost_anomalies(response)
            
            # Generate optimization recommendations
            optimization_opportunities = self._get_optimization_opportunities()
            
            # Calculate cost trends
            trends_analysis = self._calculate_cost_trends(response)
            
            # Generate comprehensive report
            comprehensive_analysis = {
                'analysis_period': {
                    'start_date': analysis_request.start_date,
                    'end_date': analysis_request.end_date,
                    'granularity': analysis_request.granularity.value
                },
                'cost_summary': cost_analysis['summary'],
                'cost_breakdown': cost_analysis['breakdown'],
                'dimension_analysis': dimension_analysis,
                'trends_analysis': trends_analysis,
                'forecast_data': forecast_data,
                'anomalies': anomalies,
                'optimization_opportunities': optimization_opportunities,
                'total_potential_savings': sum([
                    opp['potential_savings'] for opp in optimization_opportunities
                ]),
                'next_page_token': response.get('NextPageToken'),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Generated comprehensive cost analysis for period {analysis_request.start_date} to {analysis_request.end_date}")
            
            return comprehensive_analysis
            
        except Exception as e:
            self.logger.error(f"Failed to generate cost analysis: {str(e)}")
            raise
    
    def _process_cost_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw cost data into structured analysis"""
        
        total_cost = Decimal('0')
        time_series_data = []
        service_breakdown = {}
        
        for result in response['ResultsByTime']:
            period_start = result['TimePeriod']['Start']
            period_end = result['TimePeriod']['End']
            
            # Process total cost for period
            if result.get('Total'):
                period_cost = Decimal(result['Total'].get('BlendedCost', {}).get('Amount', '0'))
                total_cost += period_cost
                
                time_series_data.append({
                    'period_start': period_start,
                    'period_end': period_end,
                    'cost': float(period_cost)
                })
            
            # Process grouped data (e.g., by service)
            for group in result.get('Groups', []):
                group_key = group['Keys'][0] if group['Keys'] else 'Unknown'
                group_cost = Decimal(group['Metrics'].get('BlendedCost', {}).get('Amount', '0'))
                
                if group_key not in service_breakdown:
                    service_breakdown[group_key] = {
                        'total_cost': Decimal('0'),
                        'time_series': []
                    }
                
                service_breakdown[group_key]['total_cost'] += group_cost
                service_breakdown[group_key]['time_series'].append({
                    'period_start': period_start,
                    'period_end': period_end,
                    'cost': float(group_cost)
                })
        
        # Sort services by cost
        sorted_services = sorted(
            service_breakdown.items(),
            key=lambda x: x[1]['total_cost'],
            reverse=True
        )
        
        return {
            'summary': {
                'total_cost': float(total_cost),
                'currency': 'USD',
                'number_of_periods': len(time_series_data)
            },
            'breakdown': {
                'time_series': time_series_data,
                'top_services': [
                    {
                        'service': service,
                        'cost': float(data['total_cost']),
                        'percentage': float((data['total_cost'] / total_cost) * 100) if total_cost > 0 else 0
                    }
                    for service, data in sorted_services[:10]
                ]
            }
        }
    
    def _get_dimension_analysis(self, analysis_request: CostAnalysisRequest) -> Dict[str, Any]:
        """Get dimension-based cost analysis"""
        
        dimension_analysis = {}
        
        # Analyze by key dimensions
        dimensions = ['SERVICE', 'REGION', 'LINKED_ACCOUNT', 'INSTANCE_TYPE']
        
        for dimension in dimensions:
            try:
                dimension_response = self.ce_client.get_dimension_values(
                    TimePeriod={
                        'Start': analysis_request.start_date,
                        'End': analysis_request.end_date
                    },
                    Dimension=dimension,
                    Context='COST_AND_USAGE'
                )
                
                dimension_analysis[dimension.lower()] = {
                    'total_values': len(dimension_response['DimensionValues']),
                    'top_values': [
                        {
                            'value': dv['Value'],
                            'attributes': dv.get('Attributes', {})
                        }
                        for dv in dimension_response['DimensionValues'][:10]
                    ]
                }
                
            except Exception as e:
                self.logger.warning(f"Failed to get dimension analysis for {dimension}: {str(e)}")
                dimension_analysis[dimension.lower()] = {'error': str(e)}
        
        return dimension_analysis
    
    def _generate_cost_forecast(self, analysis_request: CostAnalysisRequest) -> Dict[str, Any]:
        """Generate cost forecast using historical data"""
        
        try:
            # Calculate forecast period (next 30 days)
            forecast_start = analysis_request.end_date
            forecast_end = (datetime.strptime(forecast_start, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
            
            forecast_response = self.ce_client.get_cost_forecast(
                TimePeriod={
                    'Start': forecast_start,
                    'End': forecast_end
                },
                Metric='BLENDED_COST',
                Granularity='DAILY'
            )
            
            total_forecasted_cost = Decimal(forecast_response['Total']['Amount'])
            
            # Calculate forecast confidence
            forecast_confidence = self._calculate_forecast_confidence(
                forecast_response,
                analysis_request
            )
            
            return {
                'forecast_period': {
                    'start_date': forecast_start,
                    'end_date': forecast_end
                },
                'total_forecasted_cost': float(total_forecasted_cost),
                'mean_value': float(Decimal(forecast_response['Total']['Amount'])),
                'prediction_interval_lower': float(Decimal(forecast_response['Total']['Amount']) * Decimal('0.9')),
                'prediction_interval_upper': float(Decimal(forecast_response['Total']['Amount']) * Decimal('1.1')),
                'confidence_level': forecast_confidence,
                'currency': 'USD'
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to generate cost forecast: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_forecast_confidence(self, 
                                     forecast_response: Dict[str, Any],
                                     analysis_request: CostAnalysisRequest) -> str:
        """Calculate forecast confidence based on historical data quality"""
        
        # This is a simplified confidence calculation
        # In practice, you would analyze historical accuracy and data quality
        
        analysis_days = (
            datetime.strptime(analysis_request.end_date, '%Y-%m-%d') -
            datetime.strptime(analysis_request.start_date, '%Y-%m-%d')
        ).days
        
        if analysis_days >= 90:
            return "HIGH"
        elif analysis_days >= 30:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _detect_cost_anomalies(self, cost_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect cost anomalies in the time series data"""
        
        anomalies = []
        
        try:
            # Get anomaly detection results
            anomaly_response = self.ce_client.get_anomalies(
                DateInterval={
                    'StartDate': (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'EndDate': datetime.utcnow().strftime('%Y-%m-%d')
                }
            )
            
            for anomaly in anomaly_response['Anomalies']:
                anomalies.append({
                    'anomaly_id': anomaly['AnomalyId'],
                    'start_date': anomaly['AnomalyStartDate'],
                    'end_date': anomaly.get('AnomalyEndDate'),
                    'dimension_key': anomaly['DimensionKey'],
                    'impact': {
                        'max_impact': float(Decimal(anomaly['Impact']['MaxImpact'])),
                        'total_impact': float(Decimal(anomaly['Impact']['TotalImpact']))
                    },
                    'monitor_arn': anomaly['MonitorArn'],
                    'feedback': anomaly.get('Feedback'),
                    'root_causes': anomaly.get('RootCauses', [])
                })
                
        except Exception as e:
            self.logger.warning(f"Failed to detect cost anomalies: {str(e)}")
        
        return anomalies
    
    def _get_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Get comprehensive cost optimization opportunities"""
        
        opportunities = []
        
        # Get rightsizing recommendations
        rightsizing_opportunities = self._get_rightsizing_recommendations()
        opportunities.extend(rightsizing_opportunities)
        
        # Get Reserved Instance recommendations
        ri_opportunities = self._get_reserved_instance_recommendations()
        opportunities.extend(ri_opportunities)
        
        # Get Savings Plans recommendations
        sp_opportunities = self._get_savings_plans_recommendations()
        opportunities.extend(sp_opportunities)
        
        # Sort by potential savings
        opportunities.sort(key=lambda x: x['potential_savings'], reverse=True)
        
        return opportunities[:20]  # Return top 20 opportunities
    
    def _get_rightsizing_recommendations(self) -> List[Dict[str, Any]]:
        """Get rightsizing recommendations"""
        
        opportunities = []
        
        try:
            response = self.ce_client.get_rightsizing_recommendation(
                Service='AmazonEC2'
            )
            
            for recommendation in response['RightsizingRecommendations']:
                current_instance = recommendation['CurrentInstance']
                
                if recommendation['RightsizingType'] == 'Terminate':
                    potential_savings = float(Decimal(
                        recommendation['TerminateRecommendationDetail']['EstimatedMonthlySavings']
                    ))
                elif recommendation['RightsizingType'] == 'Modify':
                    potential_savings = float(Decimal(
                        recommendation['ModifyRecommendationDetail']['EstimatedMonthlySavings']
                    ))
                else:
                    continue
                
                if potential_savings >= self.optimization_thresholds['rightsizing']['minimum_savings']:
                    opportunities.append({
                        'recommendation_type': RecommendationType.RIGHTSIZING.value,
                        'resource_id': current_instance['InstanceId'],
                        'service': 'EC2',
                        'region': current_instance['Region'],
                        'current_cost': float(Decimal(current_instance['MonthlyCost'])),
                        'optimized_cost': float(Decimal(current_instance['MonthlyCost'])) - potential_savings,
                        'potential_savings': potential_savings,
                        'savings_percentage': (potential_savings / float(Decimal(current_instance['MonthlyCost']))) * 100,
                        'implementation_effort': 'Medium',
                        'risk_level': 'Low' if recommendation['RightsizingType'] == 'Modify' else 'Medium',
                        'recommendation_details': recommendation,
                        'priority_score': self._calculate_optimization_priority(potential_savings, 'Medium', 'Low')
                    })
                    
        except Exception as e:
            self.logger.warning(f"Failed to get rightsizing recommendations: {str(e)}")
        
        return opportunities
    
    def _get_reserved_instance_recommendations(self) -> List[Dict[str, Any]]:
        """Get Reserved Instance purchase recommendations"""
        
        opportunities = []
        
        try:
            response = self.ce_client.get_reservation_purchase_recommendation(
                Service='AmazonEC2'
            )
            
            for recommendation in response['Recommendations']:
                recommendation_details = recommendation['RecommendationDetail']
                
                estimated_monthly_savings = float(Decimal(
                    recommendation_details['EstimatedMonthlySavingsAmount']
                ))
                
                if estimated_monthly_savings >= self.optimization_thresholds['reserved_instances']['minimum_savings']:
                    opportunities.append({
                        'recommendation_type': RecommendationType.RESERVED_INSTANCE.value,
                        'resource_id': recommendation_details['InstanceDetails']['EC2InstanceDetails']['InstanceType'],
                        'service': 'EC2',
                        'region': recommendation_details['InstanceDetails']['EC2InstanceDetails']['Region'],
                        'current_cost': float(Decimal(recommendation_details['EstimatedMonthlyOnDemandCost'])),
                        'optimized_cost': float(Decimal(recommendation_details['EstimatedMonthlyOnDemandCost'])) - estimated_monthly_savings,
                        'potential_savings': estimated_monthly_savings,
                        'savings_percentage': (estimated_monthly_savings / float(Decimal(recommendation_details['EstimatedMonthlyOnDemandCost']))) * 100,
                        'implementation_effort': 'Low',
                        'risk_level': 'Low',
                        'recommendation_details': recommendation,
                        'priority_score': self._calculate_optimization_priority(estimated_monthly_savings, 'Low', 'Low')
                    })
                    
        except Exception as e:
            self.logger.warning(f"Failed to get RI recommendations: {str(e)}")
        
        return opportunities
    
    def _get_savings_plans_recommendations(self) -> List[Dict[str, Any]]:
        """Get Savings Plans purchase recommendations"""
        
        opportunities = []
        
        try:
            response = self.ce_client.get_savings_plans_purchase_recommendation(
                SavingsPlansType='COMPUTE_SP',
                TermInYears='ONE_YEAR',
                PaymentOption='PARTIAL_UPFRONT'
            )
            
            for recommendation in response['SavingsPlansRecommendations']:
                recommendation_details = recommendation['SavingsPlansDetails']
                
                estimated_monthly_savings = float(Decimal(
                    recommendation['EstimatedMonthlySavings']
                ))
                
                if estimated_monthly_savings >= self.optimization_thresholds['savings_plans']['minimum_savings']:
                    opportunities.append({
                        'recommendation_type': RecommendationType.SAVINGS_PLAN.value,
                        'resource_id': f"SP-{recommendation_details['Region']}-{recommendation_details['InstanceFamily']}",
                        'service': 'Savings Plans',
                        'region': recommendation_details['Region'],
                        'current_cost': float(Decimal(recommendation['EstimatedOnDemandCost'])),
                        'optimized_cost': float(Decimal(recommendation['EstimatedOnDemandCost'])) - estimated_monthly_savings,
                        'potential_savings': estimated_monthly_savings,
                        'savings_percentage': (estimated_monthly_savings / float(Decimal(recommendation['EstimatedOnDemandCost']))) * 100,
                        'implementation_effort': 'Low',
                        'risk_level': 'Low',
                        'recommendation_details': recommendation,
                        'priority_score': self._calculate_optimization_priority(estimated_monthly_savings, 'Low', 'Low')
                    })
                    
        except Exception as e:
            self.logger.warning(f"Failed to get Savings Plans recommendations: {str(e)}")
        
        return opportunities
    
    def _calculate_optimization_priority(self, 
                                       savings_amount: float,
                                       implementation_effort: str,
                                       risk_level: str) -> int:
        """Calculate priority score for optimization opportunity"""
        
        # Base score from savings amount
        savings_score = min(int(savings_amount / 100), 50)  # Max 50 points
        
        # Effort penalty
        effort_penalty = {
            'Low': 0,
            'Medium': 10,
            'High': 20
        }.get(implementation_effort, 10)
        
        # Risk penalty
        risk_penalty = {
            'Low': 0,
            'Medium': 5,
            'High': 15
        }.get(risk_level, 5)
        
        return max(savings_score - effort_penalty - risk_penalty, 1)
    
    def _calculate_cost_trends(self, cost_response: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost trends and growth rates"""
        
        costs = []
        dates = []
        
        for result in cost_response['ResultsByTime']:
            if result.get('Total'):
                cost = float(Decimal(result['Total'].get('BlendedCost', {}).get('Amount', '0')))
                costs.append(cost)
                dates.append(result['TimePeriod']['Start'])
        
        if len(costs) < 2:
            return {'error': 'Insufficient data for trend analysis'}
        
        # Calculate growth rates
        growth_rates = []
        for i in range(1, len(costs)):
            if costs[i-1] > 0:
                growth_rate = ((costs[i] - costs[i-1]) / costs[i-1]) * 100
                growth_rates.append(growth_rate)
        
        avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        
        return {
            'average_growth_rate_percentage': round(avg_growth_rate, 2),
            'trend_direction': 'increasing' if avg_growth_rate > 0 else 'decreasing',
            'cost_volatility': round(np.std(costs), 2) if len(costs) > 1 else 0,
            'min_cost': min(costs),
            'max_cost': max(costs),
            'cost_range_percentage': round(((max(costs) - min(costs)) / min(costs)) * 100, 2) if min(costs) > 0 else 0
        }

class FinOpsAutomationEngine:
    """
    Advanced FinOps automation engine with policy enforcement,
    budget management, and cost optimization workflows.
    """
    
    def __init__(self, cost_explorer: EnterpriseCostExplorerManager):
        self.cost_explorer = cost_explorer
        self.lambda_client = boto3.client('lambda')
        self.step_functions_client = boto3.client('stepfunctions')
        
    def create_automated_budget_management(self, 
                                         budget_configs: List[BudgetConfig]) -> Dict[str, Any]:
        """Create automated budget management with alerts and actions"""
        
        automation_results = []
        
        for budget_config in budget_configs:
            try:
                # Create the budget
                budget_response = self.cost_explorer.budgets_client.create_budget(
                    AccountId=self._get_account_id(),
                    Budget={
                        'BudgetName': budget_config.budget_name,
                        'BudgetLimit': {
                            'Amount': str(budget_config.budget_limit),
                            'Unit': 'USD'
                        },
                        'TimeUnit': budget_config.time_unit.value,
                        'BudgetType': budget_config.budget_type,
                        'CostFilters': budget_config.cost_filters,
                        'TimePeriod': budget_config.time_period
                    }
                )
                
                # Create notifications
                for notification in budget_config.notifications:
                    self.cost_explorer.budgets_client.create_notification(
                        AccountId=self._get_account_id(),
                        BudgetName=budget_config.budget_name,
                        Notification=notification,
                        Subscribers=budget_config.subscribers
                    )
                
                # Setup automated actions
                automation_actions = self._create_budget_automation_actions(budget_config)
                
                automation_results.append({
                    'budget_name': budget_config.budget_name,
                    'status': 'created',
                    'budget_limit': float(budget_config.budget_limit),
                    'time_unit': budget_config.time_unit.value,
                    'notifications_count': len(budget_config.notifications),
                    'automation_actions': automation_actions
                })
                
            except Exception as e:
                self.cost_explorer.logger.error(f"Failed to create budget {budget_config.budget_name}: {str(e)}")
                automation_results.append({
                    'budget_name': budget_config.budget_name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'automation_results': automation_results,
            'total_budgets_created': len([r for r in automation_results if r['status'] == 'created']),
            'total_failed': len([r for r in automation_results if r['status'] == 'failed'])
        }
    
    def _get_account_id(self) -> str:
        """Get current AWS account ID"""
        return boto3.client('sts').get_caller_identity()['Account']
    
    def _create_budget_automation_actions(self, budget_config: BudgetConfig) -> List[Dict[str, Any]]:
        """Create automated actions for budget management"""
        
        actions = []
        
        # Create Lambda function for budget alerts
        alert_function = {
            'function_name': f'budget-alert-{budget_config.budget_name}',
            'description': f'Automated budget alert handler for {budget_config.budget_name}',
            'handler': 'lambda_function.lambda_handler',
            'runtime': 'python3.9',
            'code': self._generate_budget_alert_code(budget_config)
        }
        actions.append(alert_function)
        
        # Create cost optimization workflow
        optimization_workflow = {
            'workflow_name': f'cost-optimization-{budget_config.budget_name}',
            'description': f'Automated cost optimization for {budget_config.budget_name}',
            'trigger_threshold': 80,  # 80% of budget
            'actions': [
                'analyze_cost_drivers',
                'identify_optimization_opportunities',
                'implement_approved_optimizations',
                'report_savings'
            ]
        }
        actions.append(optimization_workflow)
        
        return actions
    
    def _generate_budget_alert_code(self, budget_config: BudgetConfig) -> str:
        """Generate Lambda function code for budget alerts"""
        
        return f'''
import json
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Handle budget alert notifications and trigger appropriate actions"""
    
    try:
        # Parse budget alert event
        message = json.loads(event['Records'][0]['Sns']['Message'])
        
        budget_name = message.get('BudgetName', '{budget_config.budget_name}')
        actual_spend = float(message.get('ActualSpend', {{}}}).get('Amount', 0))
        budget_limit = float(message.get('BudgetLimit', {{}}}).get('Amount', {budget_config.budget_limit}))
        threshold_type = message.get('ThresholdType', 'PERCENTAGE')
        
        # Calculate utilization percentage
        utilization_percentage = (actual_spend / budget_limit) * 100 if budget_limit > 0 else 0
        
        # Determine action based on utilization
        if utilization_percentage >= 90:
            action = 'emergency_cost_reduction'
        elif utilization_percentage >= 80:
            action = 'implement_cost_optimizations'
        elif utilization_percentage >= 70:
            action = 'analyze_cost_trends'
        else:
            action = 'monitor_spending'
        
        # Execute appropriate action
        response = execute_budget_action(action, {{
            'budget_name': budget_name,
            'actual_spend': actual_spend,
            'budget_limit': budget_limit,
            'utilization_percentage': utilization_percentage
        }})
        
        return {{
            'statusCode': 200,
            'body': json.dumps({{
                'message': 'Budget alert processed successfully',
                'action_taken': action,
                'budget_name': budget_name,
                'utilization_percentage': utilization_percentage,
                'response': response
            }})
        }}
        
    except Exception as e:
        logger.error(f"Error processing budget alert: {{str(e)}}")
        return {{
            'statusCode': 500,
            'body': json.dumps({{'error': str(e)}})
        }}

def execute_budget_action(action, budget_info):
    """Execute specific budget management action"""
    
    if action == 'emergency_cost_reduction':
        return emergency_cost_reduction(budget_info)
    elif action == 'implement_cost_optimizations':
        return implement_cost_optimizations(budget_info)
    elif action == 'analyze_cost_trends':
        return analyze_cost_trends(budget_info)
    else:
        return monitor_spending(budget_info)

def emergency_cost_reduction(budget_info):
    """Implement emergency cost reduction measures"""
    
    # This would implement emergency cost reduction
    # Such as scaling down non-critical resources
    return {{'action': 'emergency_reduction', 'status': 'initiated'}}

def implement_cost_optimizations(budget_info):
    """Implement approved cost optimizations"""
    
    # This would implement pre-approved cost optimizations
    # Such as rightsizing instances or purchasing RIs
    return {{'action': 'optimization', 'status': 'initiated'}}

def analyze_cost_trends(budget_info):
    """Analyze cost trends and generate recommendations"""
    
    # This would analyze cost trends and generate recommendations
    return {{'action': 'analysis', 'status': 'completed'}}

def monitor_spending(budget_info):
    """Continue monitoring spending patterns"""
    
    # This would continue standard monitoring
    return {{'action': 'monitoring', 'status': 'active'}}
        '''

class CostOptimizationOrchestrator:
    """
    Advanced cost optimization orchestrator with automated
    implementation and continuous monitoring.
    """
    
    def __init__(self, cost_explorer: EnterpriseCostExplorerManager):
        self.cost_explorer = cost_explorer
        self.ec2_client = boto3.client('ec2')
        self.autoscaling_client = boto3.client('autoscaling')
        
    def create_optimization_pipeline(self, 
                                   optimization_policies: Dict[str, Any]) -> Dict[str, Any]:
        """Create automated cost optimization pipeline"""
        
        pipeline_config = {
            'optimization_policies': optimization_policies,
            'automation_workflows': [],
            'monitoring_config': {},
            'governance_controls': {}
        }
        
        # Create rightsizing automation workflow
        if optimization_policies.get('enable_rightsizing', True):
            rightsizing_workflow = self._create_rightsizing_workflow(
                optimization_policies.get('rightsizing_policy', {})
            )
            pipeline_config['automation_workflows'].append(rightsizing_workflow)
        
        # Create Reserved Instance automation workflow
        if optimization_policies.get('enable_ri_automation', True):
            ri_workflow = self._create_ri_automation_workflow(
                optimization_policies.get('ri_policy', {})
            )
            pipeline_config['automation_workflows'].append(ri_workflow)
        
        # Create storage optimization workflow
        if optimization_policies.get('enable_storage_optimization', True):
            storage_workflow = self._create_storage_optimization_workflow(
                optimization_policies.get('storage_policy', {})
            )
            pipeline_config['automation_workflows'].append(storage_workflow)
        
        # Setup continuous monitoring
        monitoring_config = self._setup_optimization_monitoring(optimization_policies)
        pipeline_config['monitoring_config'] = monitoring_config
        
        # Create governance controls
        governance_controls = self._create_governance_controls(optimization_policies)
        pipeline_config['governance_controls'] = governance_controls
        
        return pipeline_config
    
    def _create_rightsizing_workflow(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Create automated rightsizing workflow"""
        
        return {
            'workflow_name': 'automated-rightsizing',
            'schedule': policy.get('schedule', 'rate(7 days)'),
            'approval_required': policy.get('require_approval', True),
            'minimum_savings': policy.get('minimum_savings', 50.0),
            'steps': [
                'discover_oversized_instances',
                'analyze_utilization_patterns',
                'generate_rightsizing_recommendations',
                'validate_recommendations',
                'create_approval_request' if policy.get('require_approval', True) else 'implement_rightsizing',
                'monitor_implementation_impact'
            ]
        }
    
    def _create_ri_automation_workflow(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Create automated RI purchase workflow"""
        
        return {
            'workflow_name': 'automated-ri-purchases',
            'schedule': policy.get('schedule', 'rate(30 days)'),
            'approval_required': policy.get('require_approval', True),
            'minimum_savings': policy.get('minimum_savings', 100.0),
            'steps': [
                'analyze_usage_patterns',
                'generate_ri_recommendations',
                'calculate_roi_and_payback',
                'validate_purchase_recommendations',
                'create_purchase_approval' if policy.get('require_approval', True) else 'execute_ri_purchase',
                'monitor_ri_utilization'
            ]
        }
    
    def _create_storage_optimization_workflow(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Create automated storage optimization workflow"""
        
        return {
            'workflow_name': 'automated-storage-optimization',
            'schedule': policy.get('schedule', 'rate(7 days)'),
            'approval_required': policy.get('require_approval', False),
            'steps': [
                'analyze_storage_usage_patterns',
                'identify_lifecycle_opportunities',
                'implement_intelligent_tiering',
                'optimize_ebs_volume_types',
                'cleanup_unused_snapshots',
                'monitor_storage_costs'
            ]
        }
    
    def _setup_optimization_monitoring(self, policies: Dict[str, Any]) -> Dict[str, Any]:
        """Setup monitoring for cost optimization activities"""
        
        return {
            'dashboards': [
                'cost-optimization-overview',
                'rightsizing-progress',
                'ri-utilization-tracking',
                'storage-optimization-metrics'
            ],
            'alerts': [
                {
                    'name': 'optimization-failure-rate',
                    'threshold': 20,  # percentage
                    'action': 'notify_team'
                },
                {
                    'name': 'unexpected-cost-increase',
                    'threshold': 10,  # percentage
                    'action': 'investigate_and_alert'
                }
            ],
            'metrics': [
                'total_savings_achieved',
                'optimization_success_rate',
                'time_to_implement',
                'roi_percentage'
            ]
        }
    
    def _create_governance_controls(self, policies: Dict[str, Any]) -> Dict[str, Any]:
        """Create governance controls for cost optimization"""
        
        return {
            'approval_workflows': [
                {
                    'name': 'high_impact_changes',
                    'threshold': 1000.0,  # USD
                    'approvers': ['finops-team@company.com', 'engineering-lead@company.com']
                }
            ],
            'risk_controls': [
                {
                    'name': 'production_workload_protection',
                    'policy': 'require_manual_approval_for_prod',
                    'scope': ['production', 'critical']
                }
            ],
            'compliance_checks': [
                'ensure_backup_before_change',
                'validate_performance_impact',
                'confirm_cost_savings'
            ]
        }

# DevOps Integration Pipeline
class CostExplorerDevOpsPipeline:
    """
    DevOps pipeline integration for Cost Explorer with automated
    cost management, optimization, and financial governance.
    """
    
    def __init__(self, pipeline_name: str):
        self.pipeline_name = pipeline_name
        self.cost_explorer = EnterpriseCostExplorerManager()
        self.finops_engine = FinOpsAutomationEngine(self.cost_explorer)
        self.optimization_orchestrator = CostOptimizationOrchestrator(self.cost_explorer)
        
    def create_finops_automation_pipeline(self, 
                                        finops_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive FinOps automation pipeline"""
        
        pipeline_config = {
            'pipeline_name': self.pipeline_name,
            'finops_config': finops_config,
            'automation_stages': []
        }
        
        # Cost analysis and reporting stage
        analysis_stage = {
            'name': 'CostAnalysisAndReporting',
            'schedule': 'rate(1 day)',  # Daily analysis
            'actions': [
                'collect_cost_data',
                'generate_analysis_reports',
                'detect_anomalies',
                'update_dashboards'
            ],
            'outputs': [
                'daily_cost_report',
                'anomaly_alerts',
                'trend_analysis'
            ]
        }
        pipeline_config['automation_stages'].append(analysis_stage)
        
        # Budget management stage
        budget_stage = {
            'name': 'BudgetManagement',
            'schedule': 'rate(1 hour)',  # Hourly budget checks
            'actions': [
                'monitor_budget_utilization',
                'trigger_alerts',
                'implement_cost_controls',
                'update_forecasts'
            ],
            'thresholds': finops_config.get('budget_thresholds', {
                'warning': 70,
                'critical': 90,
                'emergency': 95
            })
        }
        pipeline_config['automation_stages'].append(budget_stage)
        
        # Optimization implementation stage
        optimization_stage = {
            'name': 'CostOptimization',
            'schedule': 'rate(7 days)',  # Weekly optimization
            'actions': [
                'discover_optimization_opportunities',
                'prioritize_by_impact',
                'implement_approved_optimizations',
                'measure_savings'
            ],
            'governance': finops_config.get('optimization_governance', {
                'require_approval': True,
                'minimum_savings': 100.0
            })
        }
        pipeline_config['automation_stages'].append(optimization_stage)
        
        # Financial governance stage
        governance_stage = {
            'name': 'FinancialGovernance',
            'schedule': 'rate(1 day)',  # Daily governance checks
            'actions': [
                'validate_spending_policies',
                'enforce_cost_controls',
                'generate_compliance_reports',
                'update_cost_allocation'
            ],
            'policies': finops_config.get('governance_policies', [])
        }
        pipeline_config['automation_stages'].append(governance_stage)
        
        return pipeline_config

# CLI Usage Examples
if __name__ == "__main__":
    # Initialize enterprise Cost Explorer manager
    cost_mgr = EnterpriseCostExplorerManager(region='us-east-1')
    
    # Create comprehensive cost analysis request
    analysis_request = CostAnalysisRequest(
        start_date='2024-01-01',
        end_date='2024-01-31',
        granularity=Granularity.DAILY,
        metrics=[Metric.BLENDED_COST, Metric.USAGE_QUANTITY],
        group_by=[
            {'Type': 'DIMENSION', 'Key': 'SERVICE'},
            {'Type': 'DIMENSION', 'Key': 'REGION'}
        ],
        filter_expression={
            'Dimensions': {
                'Key': 'SERVICE',
                'Values': ['Amazon Elastic Compute Cloud - Compute']
            }
        }
    )
    
    # Get comprehensive cost analysis
    analysis_result = cost_mgr.get_comprehensive_cost_analysis(
        analysis_request=analysis_request,
        include_forecast=True
    )
    
    # Setup FinOps automation
    finops_engine = FinOpsAutomationEngine(cost_mgr)
    
    # Create budget configurations
    budget_configs = [
        BudgetConfig(
            budget_name='monthly-compute-budget',
            budget_limit=Decimal('10000.00'),
            time_unit=TimeUnit.MONTHLY,
            cost_filters={
                'Services': ['Amazon Elastic Compute Cloud - Compute']
            },
            subscribers=[
                {'SubscriptionType': 'EMAIL', 'Address': 'finops-team@company.com'}
            ],
            notifications=[
                {
                    'NotificationType': 'ACTUAL',
                    'ComparisonOperator': 'GREATER_THAN',
                    'Threshold': 80,
                    'ThresholdType': 'PERCENTAGE'
                }
            ]
        )
    ]
    
    budget_result = finops_engine.create_automated_budget_management(budget_configs)
    
    # Setup cost optimization
    optimization_orchestrator = CostOptimizationOrchestrator(cost_mgr)
    optimization_pipeline = optimization_orchestrator.create_optimization_pipeline({
        'enable_rightsizing': True,
        'enable_ri_automation': True,
        'enable_storage_optimization': True,
        'rightsizing_policy': {
            'minimum_savings': 50.0,
            'require_approval': True,
            'schedule': 'rate(7 days)'
        },
        'ri_policy': {
            'minimum_savings': 100.0,
            'require_approval': True,
            'schedule': 'rate(30 days)'
        }
    })
    
    # Create DevOps pipeline
    pipeline = CostExplorerDevOpsPipeline('enterprise-finops')
    finops_pipeline = pipeline.create_finops_automation_pipeline({
        'budget_thresholds': {'warning': 70, 'critical': 90, 'emergency': 95},
        'optimization_governance': {'require_approval': True, 'minimum_savings': 100.0},
        'governance_policies': ['enforce_tagging', 'validate_ri_coverage', 'monitor_anomalies']
    })
    
    print(f"Enterprise FinOps setup completed")
    print(f"Total cost analysis period: {analysis_result['analysis_period']}")
    print(f"Total potential savings: ${analysis_result['total_potential_savings']:.2f}")

# Real-world Enterprise Use Cases

## Use Case 1: Multi-National Corporation FinOps
"""
Global technology company implements comprehensive FinOps across
50+ AWS accounts with automated cost optimization and governance.

Key Requirements:
- Multi-account cost allocation and chargeback
- Automated cost optimization with approval workflows
- Real-time budget monitoring and alerting
- Compliance with financial governance policies
- Cost forecasting and capacity planning
- Integration with enterprise financial systems
"""

## Use Case 2: Financial Services Cost Management
"""
Investment bank implements automated cost management with
regulatory compliance and detailed financial reporting.

Key Requirements:
- SOX compliance for financial reporting
- Automated cost allocation by business unit
- Real-time cost monitoring and alerting
- Cost optimization with risk management
- Integration with enterprise budgeting systems
- Detailed audit trails and reporting
"""

## Use Case 3: Healthcare Organization Cost Optimization
"""
Healthcare provider implements cost optimization while maintaining
HIPAA compliance and operational requirements.

Key Requirements:
- HIPAA-compliant cost management
- Automated rightsizing with safety controls
- Budget management by department
- Cost optimization without impacting patient care
- Integration with hospital financial systems
- Compliance reporting for audits
"""

# Advanced Integration Patterns

## Pattern 1: Cost Explorer + AWS Organizations
cost_explorer_organizations_integration = """
# Multi-account cost management with Organizations
# for centralized financial governance

def setup_organization_cost_management():
    import boto3
    
    organizations = boto3.client('organizations')
    cost_explorer = boto3.client('ce')
    
    # Enable cost allocation tags at organization level
    organizations.enable_aws_service_access(
        ServicePrincipal='ce.amazonaws.com'
    )
    
    # Create cost categories for organization units
    cost_categories = cost_explorer.create_cost_category_definition(
        Name='OrganizationUnits',
        RuleVersion='CostCategoryExpression.v1',
        Rules=[
            {
                'Value': 'Production',
                'Rule': {
                    'Dimensions': {
                        'Key': 'LINKED_ACCOUNT',
                        'Values': ['123456789012', '123456789013']
                    }
                }
            }
        ]
    )
"""

## Pattern 2: Cost Explorer + Business Intelligence
cost_explorer_bi_integration = """
# Integration with business intelligence tools
# for advanced cost analytics and reporting

def setup_bi_integration():
    import boto3
    
    # Create Cost and Usage Report for BI integration
    cur_client = boto3.client('cur')
    
    report_definition = {
        'ReportName': 'enterprise-cost-report',
        'TimeUnit': 'DAILY',
        'Format': 'Parquet',
        'Compression': 'GZIP',
        'AdditionalSchemaElements': ['RESOURCES'],
        'S3Bucket': 'enterprise-cost-reports',
        'S3Prefix': 'cost-data/',
        'S3Region': 'us-east-1',
        'AdditionalArtifacts': ['ATHENA'],
        'RefreshClosedReports': True,
        'ReportVersioning': 'OVERWRITE_REPORT'
    }
    
    cur_client.put_report_definition(ReportDefinition=report_definition)
"""

## DevOps Best Practices

### 1. Cost Governance
- Automated budget management and alerting
- Policy-based cost controls and approvals
- Cost allocation and chargeback automation
- Compliance monitoring and reporting

### 2. Optimization Automation
- Continuous cost optimization discovery
- Automated implementation with safety controls
- ROI tracking and measurement
- Integration with change management processes

### 3. Financial Operations
- Real-time cost monitoring and forecasting
- Anomaly detection and investigation
- Integration with enterprise financial systems
- Automated financial reporting and analytics

### 4. Organizational Alignment
- Cross-functional FinOps team coordination
- Cost awareness training and enablement
- KPI tracking and performance management
- Continuous improvement and optimization

This enterprise AWS Cost Explorer framework provides comprehensive FinOps automation, cost optimization, and financial governance capabilities for organizations requiring advanced cost management and optimization at scale.