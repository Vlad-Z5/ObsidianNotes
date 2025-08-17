# Architecture Financial Services

## Financial Architecture Patterns

Financial services architecture requires specialized patterns for handling regulatory compliance, real-time processing, high-frequency trading, risk management, and payment processing. This guide provides comprehensive implementations and best practices for building secure, scalable, and compliant financial systems.

### High-Frequency Trading

High-frequency trading (HFT) systems require ultra-low latency, high throughput, and deterministic performance. These systems must process market data and execute trades within microseconds.

#### Low-Latency Design Implementation

```python
import asyncio
import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque
import struct
import socket
import mmap

@dataclass
class MarketData:
    symbol: str
    bid: float
    ask: float
    timestamp: int
    volume: int

@dataclass
class Order:
    order_id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    timestamp: int

class LowLatencyOrderProcessor:
    """Ultra-low latency order processing system for HFT"""
    
    def __init__(self, buffer_size: int = 10000):
        self.buffer_size = buffer_size
        self.order_buffer = deque(maxlen=buffer_size)
        self.market_data_buffer = deque(maxlen=buffer_size)
        self.processing_times = deque(maxlen=1000)
        self.lock = threading.RLock()
        
        # Memory-mapped files for ultra-fast I/O
        self.order_file = open('orders.dat', 'r+b')
        self.order_mmap = mmap.mmap(self.order_file.fileno(), 0)
        
        # Pre-allocated buffers to avoid GC pressure
        self.message_buffer = bytearray(1024)
        
    def process_market_data(self, data: MarketData) -> None:
        """Process incoming market data with minimal latency"""
        start_time = time.perf_counter_ns()
        
        with self.lock:
            self.market_data_buffer.append(data)
            
            # Trigger trading logic
            self._evaluate_trading_opportunity(data)
            
        end_time = time.perf_counter_ns()
        self.processing_times.append(end_time - start_time)
    
    def _evaluate_trading_opportunity(self, data: MarketData) -> None:
        """Evaluate trading opportunities based on market data"""
        # Simple spread trading strategy
        spread = data.ask - data.bid
        
        if spread > 0.05:  # Opportunity threshold
            order = Order(
                order_id=f"HFT_{time.time_ns()}",
                symbol=data.symbol,
                side="BUY",
                quantity=100,
                price=data.bid + 0.01,
                timestamp=time.time_ns()
            )
            self._submit_order(order)
    
    def _submit_order(self, order: Order) -> None:
        """Submit order with ultra-low latency"""
        # Pack order data into binary format for speed
        order_data = struct.pack(
            'Q20s4sifQ',
            int(order.order_id.split('_')[1]),
            order.symbol.encode()[:20],
            order.side.encode()[:4],
            order.quantity,
            order.price,
            order.timestamp
        )
        
        # Write directly to memory-mapped file
        offset = len(self.order_buffer) * 64
        self.order_mmap[offset:offset+64] = order_data
        self.order_mmap.flush()
        
        self.order_buffer.append(order)
    
    def get_latency_stats(self) -> Dict[str, float]:
        """Get processing latency statistics"""
        if not self.processing_times:
            return {}
        
        times = list(self.processing_times)
        return {
            'avg_latency_ns': sum(times) / len(times),
            'min_latency_ns': min(times),
            'max_latency_ns': max(times),
            'p99_latency_ns': sorted(times)[int(len(times) * 0.99)]
        }
```

#### Market Data Processing Pipeline

```python
import asyncio
import zmq
import json
from typing import Callable, List
import numpy as np
from concurrent.futures import ThreadPoolExecutor

class MarketDataFeed:
    """High-performance market data processing pipeline"""
    
    def __init__(self, feed_url: str, symbols: List[str]):
        self.feed_url = feed_url
        self.symbols = symbols
        self.subscribers = []
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Performance monitoring
        self.message_count = 0
        self.last_heartbeat = time.time()
        
    def subscribe(self, callback: Callable[[MarketData], None]) -> None:
        """Subscribe to market data updates"""
        self.subscribers.append(callback)
    
    async def start_feed(self) -> None:
        """Start the market data feed"""
        self.socket.connect(self.feed_url)
        
        # Subscribe to all symbols
        for symbol in self.symbols:
            self.socket.setsockopt(zmq.SUBSCRIBE, symbol.encode())
        
        self.is_running = True
        
        while self.is_running:
            try:
                # Non-blocking receive with timeout
                data = self.socket.recv_string(zmq.NOBLOCK)
                await self._process_message(data)
                self.message_count += 1
                
            except zmq.Again:
                # No message available
                await asyncio.sleep(0.001)  # 1ms sleep
                
            except Exception as e:
                print(f"Error processing market data: {e}")
                
        self.socket.close()
        self.context.term()
    
    async def _process_message(self, message: str) -> None:
        """Process incoming market data message"""
        try:
            data = json.loads(message)
            market_data = MarketData(
                symbol=data['symbol'],
                bid=data['bid'],
                ask=data['ask'],
                timestamp=data['timestamp'],
                volume=data['volume']
            )
            
            # Notify all subscribers asynchronously
            tasks = []
            for callback in self.subscribers:
                task = asyncio.create_task(
                    self._call_subscriber(callback, market_data)
                )
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            print(f"Error parsing market data: {e}")
    
    async def _call_subscriber(self, callback: Callable, data: MarketData) -> None:
        """Call subscriber callback asynchronously"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                # Run blocking callback in thread pool
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, callback, data
                )
        except Exception as e:
            print(f"Error in subscriber callback: {e}")
```

### Risk Management

Real-time risk management is critical for financial systems to prevent catastrophic losses and ensure regulatory compliance.

#### Real-Time Risk Calculation Engine

```python
import asyncio
import redis
from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
from datetime import datetime, timedelta
import logging

@dataclass
class Position:
    symbol: str
    quantity: int
    average_price: float
    market_value: float
    unrealized_pnl: float

@dataclass
class RiskMetrics:
    portfolio_value: float
    total_exposure: float
    var_95: float  # Value at Risk 95%
    expected_shortfall: float
    max_drawdown: float
    leverage_ratio: float
    concentration_risk: Dict[str, float]

class RealTimeRiskEngine:
    """Real-time risk calculation and monitoring system"""
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.positions: Dict[str, Position] = {}
        self.risk_limits = {
            'max_position_size': 1000000,  # $1M per position
            'max_portfolio_var': 50000,    # $50K daily VaR
            'max_leverage': 3.0,           # 3:1 leverage
            'max_concentration': 0.25      # 25% max in single asset
        }
        self.price_history: Dict[str, List[float]] = {}
        self.logger = logging.getLogger(__name__)
        
    async def update_position(self, symbol: str, quantity: int, price: float) -> None:
        """Update position and recalculate risk metrics"""
        try:
            # Update position
            if symbol in self.positions:
                pos = self.positions[symbol]
                total_quantity = pos.quantity + quantity
                if total_quantity != 0:
                    avg_price = ((pos.quantity * pos.average_price) + 
                               (quantity * price)) / total_quantity
                    pos.quantity = total_quantity
                    pos.average_price = avg_price
                else:
                    del self.positions[symbol]
            else:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=quantity,
                    average_price=price,
                    market_value=quantity * price,
                    unrealized_pnl=0
                )
            
            # Update risk metrics
            await self._calculate_risk_metrics()
            
            # Check risk limits
            violations = await self._check_risk_limits()
            if violations:
                await self._handle_risk_violations(violations)
                
        except Exception as e:
            self.logger.error(f"Error updating position: {e}")
    
    async def _calculate_risk_metrics(self) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        if not self.positions:
            return RiskMetrics(0, 0, 0, 0, 0, 0, {})
        
        # Portfolio value and exposure
        portfolio_value = sum(pos.market_value for pos in self.positions.values())
        total_exposure = sum(abs(pos.market_value) for pos in self.positions.values())
        
        # Calculate VaR using historical simulation
        var_95 = await self._calculate_var(confidence=0.95)
        expected_shortfall = await self._calculate_expected_shortfall()
        
        # Calculate concentration risk
        concentration_risk = {}
        for symbol, pos in self.positions.items():
            concentration = abs(pos.market_value) / total_exposure if total_exposure > 0 else 0
            concentration_risk[symbol] = concentration
        
        # Leverage ratio
        leverage_ratio = total_exposure / portfolio_value if portfolio_value > 0 else 0
        
        risk_metrics = RiskMetrics(
            portfolio_value=portfolio_value,
            total_exposure=total_exposure,
            var_95=var_95,
            expected_shortfall=expected_shortfall,
            max_drawdown=await self._calculate_max_drawdown(),
            leverage_ratio=leverage_ratio,
            concentration_risk=concentration_risk
        )
        
        # Cache in Redis for real-time access
        await self._cache_risk_metrics(risk_metrics)
        
        return risk_metrics
    
    async def _calculate_var(self, confidence: float = 0.95, window: int = 252) -> float:
        """Calculate Value at Risk using historical simulation"""
        try:
            portfolio_returns = []
            
            # Get historical returns for all positions
            for symbol, position in self.positions.items():
                prices = await self._get_price_history(symbol, window + 1)
                if len(prices) < 2:
                    continue
                
                returns = np.diff(prices) / prices[:-1]
                position_returns = returns * position.quantity * position.average_price
                portfolio_returns.append(position_returns)
            
            if not portfolio_returns:
                return 0.0
            
            # Sum returns across all positions
            total_returns = np.sum(portfolio_returns, axis=0)
            
            # Calculate VaR at specified confidence level
            var_percentile = (1 - confidence) * 100
            var = np.percentile(total_returns, var_percentile)
            
            return abs(var)
            
        except Exception as e:
            self.logger.error(f"Error calculating VaR: {e}")
            return 0.0
    
    async def _calculate_expected_shortfall(self) -> float:
        """Calculate Expected Shortfall (Conditional VaR)"""
        try:
            var_95 = await self._calculate_var(0.95)
            
            # Calculate average loss beyond VaR
            portfolio_returns = []
            for symbol, position in self.positions.items():
                prices = await self._get_price_history(symbol, 253)
                if len(prices) < 2:
                    continue
                
                returns = np.diff(prices) / prices[:-1]
                position_returns = returns * position.quantity * position.average_price
                portfolio_returns.append(position_returns)
            
            if not portfolio_returns:
                return 0.0
            
            total_returns = np.sum(portfolio_returns, axis=0)
            tail_losses = total_returns[total_returns <= -var_95]
            
            return abs(np.mean(tail_losses)) if len(tail_losses) > 0 else var_95
            
        except Exception as e:
            self.logger.error(f"Error calculating Expected Shortfall: {e}")
            return 0.0
    
    async def _check_risk_limits(self) -> List[str]:
        """Check for risk limit violations"""
        violations = []
        risk_metrics = await self._calculate_risk_metrics()
        
        # Check position size limits
        for symbol, position in self.positions.items():
            if abs(position.market_value) > self.risk_limits['max_position_size']:
                violations.append(f"Position size limit exceeded for {symbol}: "
                                f"${abs(position.market_value):,.2f}")
        
        # Check portfolio VaR limit
        if risk_metrics.var_95 > self.risk_limits['max_portfolio_var']:
            violations.append(f"Portfolio VaR limit exceeded: "
                            f"${risk_metrics.var_95:,.2f}")
        
        # Check leverage limit
        if risk_metrics.leverage_ratio > self.risk_limits['max_leverage']:
            violations.append(f"Leverage limit exceeded: {risk_metrics.leverage_ratio:.2f}")
        
        # Check concentration limits
        for symbol, concentration in risk_metrics.concentration_risk.items():
            if concentration > self.risk_limits['max_concentration']:
                violations.append(f"Concentration limit exceeded for {symbol}: "
                                f"{concentration:.1%}")
        
        return violations
    
    async def _handle_risk_violations(self, violations: List[str]) -> None:
        """Handle risk limit violations"""
        for violation in violations:
            self.logger.warning(f"Risk violation: {violation}")
            
            # Send alert to risk management team
            await self._send_risk_alert(violation)
            
            # Implement automatic risk reduction if configured
            if "Position size limit exceeded" in violation:
                symbol = violation.split()[6].rstrip(':')
                await self._reduce_position(symbol, 0.5)  # Reduce by 50%
    
    async def _send_risk_alert(self, message: str) -> None:
        """Send risk alert to monitoring system"""
        alert_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'HIGH',
            'message': message,
            'source': 'RiskEngine'
        }
        
        # Publish to Redis channel for real-time alerts
        await asyncio.get_event_loop().run_in_executor(
            None, 
            self.redis_client.publish, 
            'risk_alerts', 
            json.dumps(alert_data)
        )
```

### Payment Processing

Secure and reliable payment processing requires robust architecture patterns for handling transactions, settlement, fraud detection, and compliance.

#### Payment Rails Implementation

```python
import asyncio
import uuid
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import aiohttp
import asyncpg

class PaymentStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class PaymentMethod(Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    ACH = "ACH"
    WIRE = "WIRE"
    CRYPTO = "CRYPTO"

@dataclass
class PaymentRequest:
    payment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    amount: float = 0.0
    currency: str = "USD"
    payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD
    merchant_id: str = ""
    customer_id: str = ""
    description: str = ""
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PaymentResponse:
    payment_id: str
    status: PaymentStatus
    amount: float
    currency: str
    transaction_id: Optional[str] = None
    gateway_response: Optional[Dict] = None
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None

class PaymentProcessor:
    """Multi-gateway payment processing system"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.gateways = {
            PaymentMethod.CREDIT_CARD: StripeGateway(),
            PaymentMethod.DEBIT_CARD: StripeGateway(),
            PaymentMethod.ACH: PlaidGateway(),
            PaymentMethod.WIRE: BankGateway(),
            PaymentMethod.CRYPTO: CoinbaseGateway()
        }
        self.fraud_detector = FraudDetector()
        self.compliance_checker = ComplianceChecker()
        
    async def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Process payment through appropriate gateway"""
        try:
            # Validate request
            validation_result = await self._validate_payment_request(request)
            if not validation_result.is_valid:
                return PaymentResponse(
                    payment_id=request.payment_id,
                    status=PaymentStatus.FAILED,
                    amount=request.amount,
                    currency=request.currency,
                    error_message=validation_result.error_message
                )
            
            # Fraud detection
            fraud_score = await self.fraud_detector.analyze_payment(request)
            if fraud_score > 0.8:  # High fraud risk
                await self._flag_suspicious_payment(request, fraud_score)
                return PaymentResponse(
                    payment_id=request.payment_id,
                    status=PaymentStatus.FAILED,
                    amount=request.amount,
                    currency=request.currency,
                    error_message="Payment blocked due to fraud risk"
                )
            
            # Compliance check
            compliance_result = await self.compliance_checker.check_payment(request)
            if not compliance_result.approved:
                return PaymentResponse(
                    payment_id=request.payment_id,
                    status=PaymentStatus.FAILED,
                    amount=request.amount,
                    currency=request.currency,
                    error_message=f"Compliance check failed: {compliance_result.reason}"
                )
            
            # Store payment request
            await self._store_payment_request(request)
            
            # Process through gateway
            gateway = self.gateways[request.payment_method]
            response = await gateway.process_payment(request)
            
            # Update payment status
            await self._update_payment_status(response)
            
            # Send notifications
            await self._send_payment_notification(response)
            
            return response
            
        except Exception as e:
            error_response = PaymentResponse(
                payment_id=request.payment_id,
                status=PaymentStatus.FAILED,
                amount=request.amount,
                currency=request.currency,
                error_message=str(e)
            )
            await self._update_payment_status(error_response)
            return error_response
    
    async def _validate_payment_request(self, request: PaymentRequest) -> 'ValidationResult':
        """Validate payment request"""
        if request.amount <= 0:
            return ValidationResult(False, "Invalid amount")
        
        if not request.merchant_id:
            return ValidationResult(False, "Merchant ID required")
        
        if not request.customer_id:
            return ValidationResult(False, "Customer ID required")
        
        # Check daily limits
        daily_amount = await self._get_daily_payment_amount(request.customer_id)
        if daily_amount + request.amount > 10000:  # $10K daily limit
            return ValidationResult(False, "Daily payment limit exceeded")
        
        return ValidationResult(True, "Valid")
    
    async def _store_payment_request(self, request: PaymentRequest) -> None:
        """Store payment request in database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO payments (
                    payment_id, amount, currency, payment_method,
                    merchant_id, customer_id, description, metadata,
                    status, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, 
            request.payment_id, request.amount, request.currency,
            request.payment_method.value, request.merchant_id,
            request.customer_id, request.description,
            json.dumps(request.metadata), PaymentStatus.PENDING.value,
            request.created_at)

class StripeGateway:
    """Stripe payment gateway implementation"""
    
    def __init__(self):
        self.api_key = "sk_test_..."  # Use environment variable
        self.api_url = "https://api.stripe.com/v1"
    
    async def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Process payment through Stripe"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                
                data = {
                    'amount': int(request.amount * 100),  # Convert to cents
                    'currency': request.currency.lower(),
                    'description': request.description,
                    'metadata[payment_id]': request.payment_id,
                    'metadata[customer_id]': request.customer_id
                }
                
                async with session.post(
                    f"{self.api_url}/payment_intents",
                    headers=headers,
                    data=data
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        return PaymentResponse(
                            payment_id=request.payment_id,
                            status=PaymentStatus.COMPLETED,
                            amount=request.amount,
                            currency=request.currency,
                            transaction_id=result['id'],
                            gateway_response=result,
                            processed_at=datetime.utcnow()
                        )
                    else:
                        return PaymentResponse(
                            payment_id=request.payment_id,
                            status=PaymentStatus.FAILED,
                            amount=request.amount,
                            currency=request.currency,
                            error_message=result.get('error', {}).get('message', 'Unknown error')
                        )
                        
        except Exception as e:
            return PaymentResponse(
                payment_id=request.payment_id,
                status=PaymentStatus.FAILED,
                amount=request.amount,
                currency=request.currency,
                error_message=str(e)
            )

class FraudDetector:
    """Machine learning-based fraud detection system"""
    
    def __init__(self):
        self.risk_rules = [
            self._check_velocity_patterns,
            self._check_geographic_anomalies,
            self._check_amount_patterns,
            self._check_device_fingerprint
        ]
    
    async def analyze_payment(self, request: PaymentRequest) -> float:
        """Analyze payment for fraud risk (0.0 = low risk, 1.0 = high risk)"""
        risk_scores = []
        
        for rule in self.risk_rules:
            score = await rule(request)
            risk_scores.append(score)
        
        # Weighted average of risk scores
        weights = [0.3, 0.2, 0.3, 0.2]
        weighted_score = sum(score * weight for score, weight in zip(risk_scores, weights))
        
        return min(1.0, max(0.0, weighted_score))
    
    async def _check_velocity_patterns(self, request: PaymentRequest) -> float:
        """Check for suspicious velocity patterns"""
        # Check payment frequency for customer
        recent_payments = await self._get_recent_payments(
            request.customer_id, 
            hours=1
        )
        
        if len(recent_payments) > 5:  # More than 5 payments in 1 hour
            return 0.8
        elif len(recent_payments) > 3:
            return 0.5
        
        return 0.1
    
    async def _check_geographic_anomalies(self, request: PaymentRequest) -> float:
        """Check for geographic anomalies"""
        # Get customer's typical location
        typical_location = await self._get_customer_location(request.customer_id)
        current_location = request.metadata.get('location')
        
        if typical_location and current_location:
            distance = self._calculate_distance(typical_location, current_location)
            if distance > 1000:  # More than 1000 miles from typical location
                return 0.7
        
        return 0.1
```

### Regulatory Systems

Financial institutions must comply with numerous regulations including PCI DSS, SOX, Basel III, and jurisdiction-specific requirements.

#### Regulatory Reporting Framework

```python
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import xml.etree.ElementTree as ET
import json

class ReportType(Enum):
    DAILY_POSITION = "DAILY_POSITION"
    RISK_METRICS = "RISK_METRICS"
    TRANSACTION_SUMMARY = "TRANSACTION_SUMMARY"
    LIQUIDITY_REPORT = "LIQUIDITY_REPORT"
    CAPITAL_ADEQUACY = "CAPITAL_ADEQUACY"

class RegulationType(Enum):
    FINRA = "FINRA"
    SEC = "SEC"
    CFTC = "CFTC"
    BASEL_III = "BASEL_III"
    MIFID_II = "MIFID_II"

@dataclass
class RegulatoryReport:
    report_id: str
    report_type: ReportType
    regulation: RegulationType
    reporting_date: datetime
    data: Dict[str, Any]
    status: str = "PENDING"
    file_path: Optional[str] = None

class RegulatoryReportingEngine:
    """Automated regulatory reporting system"""
    
    def __init__(self, db_pool: Any):
        self.db_pool = db_pool
        self.report_generators = {
            ReportType.DAILY_POSITION: self._generate_position_report,
            ReportType.RISK_METRICS: self._generate_risk_report,
            ReportType.TRANSACTION_SUMMARY: self._generate_transaction_report,
            ReportType.LIQUIDITY_REPORT: self._generate_liquidity_report,
            ReportType.CAPITAL_ADEQUACY: self._generate_capital_report
        }
        self.formatters = {
            RegulationType.FINRA: self._format_finra_xml,
            RegulationType.SEC: self._format_sec_json,
            RegulationType.CFTC: self._format_cftc_csv,
            RegulationType.BASEL_III: self._format_basel_xml
        }
    
    async def generate_scheduled_reports(self) -> List[RegulatoryReport]:
        """Generate all scheduled regulatory reports"""
        reports = []
        current_date = datetime.now().date()
        
        # Daily reports
        daily_reports = [
            (ReportType.DAILY_POSITION, RegulationType.FINRA),
            (ReportType.RISK_METRICS, RegulationType.SEC),
            (ReportType.TRANSACTION_SUMMARY, RegulationType.CFTC)
        ]
        
        for report_type, regulation in daily_reports:
            try:
                report = await self._generate_report(report_type, regulation, current_date)
                reports.append(report)
            except Exception as e:
                print(f"Error generating {report_type.value} report: {e}")
        
        # Weekly reports (Fridays)
        if current_date.weekday() == 4:  # Friday
            weekly_report = await self._generate_report(
                ReportType.LIQUIDITY_REPORT, 
                RegulationType.BASEL_III, 
                current_date
            )
            reports.append(weekly_report)
        
        # Monthly reports (last business day)
        if self._is_last_business_day(current_date):
            monthly_report = await self._generate_report(
                ReportType.CAPITAL_ADEQUACY,
                RegulationType.BASEL_III,
                current_date
            )
            reports.append(monthly_report)
        
        return reports
    
    async def _generate_report(
        self, 
        report_type: ReportType, 
        regulation: RegulationType,
        reporting_date: datetime.date
    ) -> RegulatoryReport:
        """Generate a specific regulatory report"""
        
        # Generate report data
        generator = self.report_generators[report_type]
        report_data = await generator(reporting_date)
        
        # Format according to regulation requirements
        formatter = self.formatters[regulation]
        formatted_data = await formatter(report_data, report_type)
        
        # Create report object
        report = RegulatoryReport(
            report_id=f"{report_type.value}_{regulation.value}_{reporting_date.strftime('%Y%m%d')}",
            report_type=report_type,
            regulation=regulation,
            reporting_date=datetime.combine(reporting_date, datetime.min.time()),
            data=formatted_data
        )
        
        # Save to file system
        file_path = await self._save_report_to_file(report)
        report.file_path = file_path
        report.status = "COMPLETED"
        
        # Store in database
        await self._store_report_metadata(report)
        
        return report
    
    async def _generate_position_report(self, date: datetime.date) -> Dict[str, Any]:
        """Generate daily position report"""
        async with self.db_pool.acquire() as conn:
            # Get all positions as of end of day
            positions = await conn.fetch("""
                SELECT 
                    symbol,
                    SUM(quantity) as net_position,
                    AVG(price) as avg_price,
                    SUM(quantity * price) as market_value
                FROM trades 
                WHERE DATE(trade_date) <= $1
                GROUP BY symbol
                HAVING SUM(quantity) != 0
                ORDER BY symbol
            """, date)
            
            # Calculate portfolio metrics
            total_value = sum(float(pos['market_value']) for pos in positions)
            position_count = len(positions)
            
            report_data = {
                'reporting_date': date.isoformat(),
                'total_portfolio_value': total_value,
                'position_count': position_count,
                'positions': [
                    {
                        'symbol': pos['symbol'],
                        'net_position': float(pos['net_position']),
                        'average_price': float(pos['avg_price']),
                        'market_value': float(pos['market_value']),
                        'weight': float(pos['market_value']) / total_value if total_value > 0 else 0
                    }
                    for pos in positions
                ]
            }
            
            return report_data
    
    async def _format_finra_xml(self, data: Dict[str, Any], report_type: ReportType) -> str:
        """Format report data as FINRA-compliant XML"""
        root = ET.Element("FinraReport")
        
        # Header
        header = ET.SubElement(root, "ReportHeader")
        ET.SubElement(header, "ReportType").text = report_type.value
        ET.SubElement(header, "ReportingDate").text = data['reporting_date']
        ET.SubElement(header, "FirmCRD").text = "12345"  # Firm's CRD number
        
        # Positions section
        if report_type == ReportType.DAILY_POSITION:
            positions_elem = ET.SubElement(root, "Positions")
            
            for position in data['positions']:
                pos_elem = ET.SubElement(positions_elem, "Position")
                ET.SubElement(pos_elem, "Symbol").text = position['symbol']
                ET.SubElement(pos_elem, "NetPosition").text = str(position['net_position'])
                ET.SubElement(pos_elem, "MarketValue").text = str(position['market_value'])
                ET.SubElement(pos_elem, "Weight").text = f"{position['weight']:.4f}"
        
        return ET.tostring(root, encoding='unicode')
    
    async def _validate_report_data(self, report: RegulatoryReport) -> List[str]:
        """Validate report data for compliance"""
        validation_errors = []
        
        # Common validations
        if not report.data:
            validation_errors.append("Report data is empty")
        
        if report.report_type == ReportType.DAILY_POSITION:
            positions = report.data.get('positions', [])
            total_weight = sum(pos.get('weight', 0) for pos in positions)
            
            if abs(total_weight - 1.0) > 0.01:  # Allow 1% tolerance
                validation_errors.append(f"Position weights sum to {total_weight:.4f}, expected 1.0")
            
            # Check for concentration limits
            max_position_weight = max((pos.get('weight', 0) for pos in positions), default=0)
            if max_position_weight > 0.25:  # 25% concentration limit
                validation_errors.append(f"Position concentration exceeds limit: {max_position_weight:.2%}")
        
        return validation_errors
```

### Core Banking

Core banking systems handle fundamental banking operations including account management, transaction processing, and regulatory compliance.

#### Core Banking Transaction Engine

```python
import asyncio
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncpg

class AccountType(Enum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CREDIT = "CREDIT"
    LOAN = "LOAN"
    INVESTMENT = "INVESTMENT"

class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    INTEREST = "INTEREST"
    FEE = "FEE"

class TransactionStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"

@dataclass
class Account:
    account_id: str
    customer_id: str
    account_type: AccountType
    balance: Decimal
    available_balance: Decimal
    currency: str = "USD"
    status: str = "ACTIVE"
    interest_rate: Decimal = Decimal('0.0')
    created_at: datetime = None
    
@dataclass
class Transaction:
    transaction_id: str
    account_id: str
    transaction_type: TransactionType
    amount: Decimal
    balance_after: Decimal
    description: str
    reference_id: Optional[str] = None
    counterparty_account: Optional[str] = None
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = None
    processed_at: Optional[datetime] = None

class CoreBankingEngine:
    """Core banking transaction processing engine"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.transaction_limits = {
            AccountType.CHECKING: {
                'daily_withdrawal': Decimal('5000'),
                'daily_transfer': Decimal('10000'),
                'transaction_max': Decimal('2500')
            },
            AccountType.SAVINGS: {
                'daily_withdrawal': Decimal('1000'),
                'daily_transfer': Decimal('5000'),
                'transaction_max': Decimal('1000')
            }
        }
        
    async def create_account(
        self,
        customer_id: str,
        account_type: AccountType,
        initial_deposit: Decimal = Decimal('0'),
        currency: str = "USD"
    ) -> Account:
        """Create a new bank account"""
        
        account = Account(
            account_id=str(uuid.uuid4()),
            customer_id=customer_id,
            account_type=account_type,
            balance=initial_deposit,
            available_balance=initial_deposit,
            currency=currency,
            created_at=datetime.utcnow()
        )
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Create account record
                await conn.execute("""
                    INSERT INTO accounts (
                        account_id, customer_id, account_type, balance,
                        available_balance, currency, status, interest_rate, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, 
                account.account_id, account.customer_id, account.account_type.value,
                account.balance, account.available_balance, account.currency,
                account.status, account.interest_rate, account.created_at)
                
                # Record initial deposit if any
                if initial_deposit > 0:
                    transaction = Transaction(
                        transaction_id=str(uuid.uuid4()),
                        account_id=account.account_id,
                        transaction_type=TransactionType.DEPOSIT,
                        amount=initial_deposit,
                        balance_after=initial_deposit,
                        description="Initial deposit",
                        status=TransactionStatus.COMPLETED,
                        created_at=datetime.utcnow(),
                        processed_at=datetime.utcnow()
                    )
                    
                    await self._record_transaction(conn, transaction)
        
        return account
    
    async def process_transaction(
        self,
        account_id: str,
        transaction_type: TransactionType,
        amount: Decimal,
        description: str,
        counterparty_account: Optional[str] = None,
        reference_id: Optional[str] = None
    ) -> Transaction:
        """Process a banking transaction"""
        
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            account_id=account_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=Decimal('0'),  # Will be calculated
            description=description,
            counterparty_account=counterparty_account,
            reference_id=reference_id,
            created_at=datetime.utcnow()
        )
        
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Get account with lock
                    account_data = await conn.fetchrow("""
                        SELECT * FROM accounts 
                        WHERE account_id = $1 
                        FOR UPDATE
                    """, account_id)
                    
                    if not account_data:
                        raise ValueError(f"Account {account_id} not found")
                    
                    account = Account(**dict(account_data))
                    
                    # Validate transaction
                    await self._validate_transaction(account, transaction)
                    
                    # Calculate new balance
                    if transaction_type in [TransactionType.DEPOSIT, TransactionType.INTEREST]:
                        new_balance = account.balance + amount
                        new_available = account.available_balance + amount
                    elif transaction_type in [TransactionType.WITHDRAWAL, TransactionType.PAYMENT, TransactionType.FEE]:
                        new_balance = account.balance - amount
                        new_available = account.available_balance - amount
                    elif transaction_type == TransactionType.TRANSFER:
                        if counterparty_account:
                            # This is the sending side of transfer
                            new_balance = account.balance - amount
                            new_available = account.available_balance - amount
                        else:
                            # This is the receiving side
                            new_balance = account.balance + amount
                            new_available = account.available_balance + amount
                    else:
                        raise ValueError(f"Unsupported transaction type: {transaction_type}")
                    
                    # Check sufficient funds
                    if new_available < 0:
                        raise ValueError("Insufficient funds")
                    
                    # Update account balance
                    await conn.execute("""
                        UPDATE accounts 
                        SET balance = $1, available_balance = $2,
                            updated_at = $3
                        WHERE account_id = $4
                    """, new_balance, new_available, datetime.utcnow(), account_id)
                    
                    # Record transaction
                    transaction.balance_after = new_balance
                    transaction.status = TransactionStatus.COMPLETED
                    transaction.processed_at = datetime.utcnow()
                    
                    await self._record_transaction(conn, transaction)
                    
                    # Handle transfer counterparty
                    if transaction_type == TransactionType.TRANSFER and counterparty_account:
                        counterparty_transaction = Transaction(
                            transaction_id=str(uuid.uuid4()),
                            account_id=counterparty_account,
                            transaction_type=TransactionType.TRANSFER,
                            amount=amount,
                            balance_after=Decimal('0'),  # Will be calculated
                            description=f"Transfer from {account_id}",
                            counterparty_account=account_id,
                            reference_id=transaction.transaction_id,
                            created_at=datetime.utcnow()
                        )
                        
                        await self._process_counterparty_transfer(conn, counterparty_transaction)
                    
                    return transaction
                    
        except Exception as e:
            # Mark transaction as failed
            transaction.status = TransactionStatus.FAILED
            transaction.processed_at = datetime.utcnow()
            
            async with self.db_pool.acquire() as conn:
                await self._record_transaction(conn, transaction)
            
            raise e
    
    async def _validate_transaction(self, account: Account, transaction: Transaction) -> None:
        """Validate transaction against business rules"""
        
        # Check account status
        if account.status != "ACTIVE":
            raise ValueError(f"Account {account.account_id} is not active")
        
        # Check transaction limits
        limits = self.transaction_limits.get(account.account_type, {})
        
        # Check per-transaction limit
        max_transaction = limits.get('transaction_max', Decimal('999999'))
        if transaction.amount > max_transaction:
            raise ValueError(f"Transaction amount exceeds limit: ${max_transaction}")
        
        # Check daily limits
        if transaction.transaction_type in [TransactionType.WITHDRAWAL, TransactionType.PAYMENT]:
            daily_limit = limits.get('daily_withdrawal', Decimal('999999'))
            daily_total = await self._get_daily_withdrawal_total(account.account_id)
            
            if daily_total + transaction.amount > daily_limit:
                raise ValueError(f"Daily withdrawal limit exceeded: ${daily_limit}")
        
        # Check business hours for large transactions
        if transaction.amount > Decimal('10000'):
            current_hour = datetime.now().hour
            if current_hour < 9 or current_hour > 17:  # 9 AM to 5 PM
                raise ValueError("Large transactions only allowed during business hours")
    
    async def calculate_daily_interest(self, account_id: str) -> Optional[Transaction]:
        """Calculate and apply daily interest"""
        
        async with self.db_pool.acquire() as conn:
            account_data = await conn.fetchrow("""
                SELECT * FROM accounts 
                WHERE account_id = $1 AND account_type IN ('SAVINGS', 'CHECKING')
            """, account_id)
            
            if not account_data or account_data['interest_rate'] <= 0:
                return None
            
            account = Account(**dict(account_data))
            
            # Calculate daily interest (annual rate / 365)
            daily_rate = account.interest_rate / Decimal('365')
            interest_amount = (account.balance * daily_rate).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            if interest_amount > Decimal('0.01'):  # Minimum interest amount
                return await self.process_transaction(
                    account_id=account_id,
                    transaction_type=TransactionType.INTEREST,
                    amount=interest_amount,
                    description="Daily interest accrual"
                )
        
        return None
    
    async def generate_statement(
        self, 
        account_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict:
        """Generate account statement"""
        
        async with self.db_pool.acquire() as conn:
            # Get account info
            account_data = await conn.fetchrow("""
                SELECT * FROM accounts WHERE account_id = $1
            """, account_id)
            
            if not account_data:
                raise ValueError(f"Account {account_id} not found")
            
            # Get transactions for period
            transactions = await conn.fetch("""
                SELECT * FROM transactions 
                WHERE account_id = $1 
                AND created_at BETWEEN $2 AND $3
                ORDER BY created_at
            """, account_id, start_date, end_date)
            
            # Calculate summary statistics
            total_deposits = sum(
                t['amount'] for t in transactions 
                if t['transaction_type'] in ['DEPOSIT', 'INTEREST', 'TRANSFER']
                and t['counterparty_account'] is not None
            )
            
            total_withdrawals = sum(
                t['amount'] for t in transactions 
                if t['transaction_type'] in ['WITHDRAWAL', 'PAYMENT', 'FEE', 'TRANSFER']
                and t['counterparty_account'] is None
            )
            
            statement = {
                'account_id': account_id,
                'account_type': account_data['account_type'],
                'statement_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'opening_balance': account_data['balance'] - total_deposits + total_withdrawals,
                'closing_balance': account_data['balance'],
                'summary': {
                    'total_deposits': float(total_deposits),
                    'total_withdrawals': float(total_withdrawals),
                    'transaction_count': len(transactions),
                    'average_balance': float(account_data['balance'])  # Simplified
                },
                'transactions': [
                    {
                        'transaction_id': t['transaction_id'],
                        'date': t['created_at'].isoformat(),
                        'type': t['transaction_type'],
                        'amount': float(t['amount']),
                        'balance': float(t['balance_after']),
                        'description': t['description']
                    }
                    for t in transactions
                ]
            }
            
            return statement

    async def _record_transaction(self, conn: asyncpg.Connection, transaction: Transaction) -> None:
        """Record transaction in database"""
        await conn.execute("""
            INSERT INTO transactions (
                transaction_id, account_id, transaction_type, amount,
                balance_after, description, reference_id, counterparty_account,
                status, created_at, processed_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """,
        transaction.transaction_id, transaction.account_id,
        transaction.transaction_type.value, transaction.amount,
        transaction.balance_after, transaction.description,
        transaction.reference_id, transaction.counterparty_account,
        transaction.status.value, transaction.created_at, transaction.processed_at)
```

## Architecture Governance

Financial services architecture governance ensures compliance, security, and operational excellence across all systems and processes.

### Compliance Monitoring System

```python
import asyncio
from typing import Dict, List, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class ComplianceRule:
    rule_id: str
    name: str
    regulation: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    check_function: str
    parameters: Dict
    enabled: bool = True

class ComplianceMonitor:
    """Real-time compliance monitoring and alerting system"""
    
    def __init__(self, db_pool: Any):
        self.db_pool = db_pool
        self.compliance_rules = []
        self.violation_handlers = []
        
    async def run_compliance_checks(self) -> List[Dict]:
        """Run all enabled compliance checks"""
        violations = []
        
        for rule in self.compliance_rules:
            if not rule.enabled:
                continue
                
            try:
                result = await self._execute_compliance_check(rule)
                if result['violations']:
                    violations.extend(result['violations'])
                    
            except Exception as e:
                print(f"Error executing compliance rule {rule.rule_id}: {e}")
        
        # Process violations
        for violation in violations:
            await self._handle_compliance_violation(violation)
        
        return violations
    
    async def _execute_compliance_check(self, rule: ComplianceRule) -> Dict:
        """Execute a specific compliance check"""
        
        if rule.check_function == "check_transaction_limits":
            return await self._check_transaction_limits(rule.parameters)
        elif rule.check_function == "check_data_retention":
            return await self._check_data_retention(rule.parameters)
        elif rule.check_function == "check_access_controls":
            return await self._check_access_controls(rule.parameters)
        else:
            return {'violations': []}
```

This comprehensive Financial Services Architecture guide provides production-ready implementations for high-frequency trading, risk management, payment processing, regulatory compliance, and core banking systems. Each component is designed for scalability, security, and regulatory compliance in financial environments.