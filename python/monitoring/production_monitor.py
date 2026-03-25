"""
Production Performance Monitor for calculo_tração_light.
This module provides real-time monitoring, alerting, and performance optimization for production environments.
"""

import asyncio
import logging
import time
import json
import psutil
import statistics
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class PerformanceMetric:
    """Performance metric data."""
    timestamp: float
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str]


@dataclass
class Alert:
    """Alert data."""
    timestamp: float
    level: AlertLevel
    title: str
    message: str
    metric_name: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None


class ProductionMonitor:
    """Production performance monitoring system."""
    
    def __init__(self, config_file: str = "production_monitor_config.json"):
        self.config = self._load_config(config_file)
        self.metrics_history: List[PerformanceMetric] = []
        self.alerts: List[Alert] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.monitoring_active = False
        self.lock = asyncio.Lock()
        
        # Performance thresholds
        self.thresholds = self.config.get('thresholds', {})
        
        # Alerting configuration
        self.alerting_config = self.config.get('alerting', {})
        
        logger.info("Production monitor initialized")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load monitoring configuration."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._generate_default_config()
    
    def _generate_default_config(self) -> Dict[str, Any]:
        """Generate default monitoring configuration."""
        config = {
            "monitoring": {
                "enabled": True,
                "interval": 30,
                "retention_hours": 24
            },
            "thresholds": {
                "cpu_usage": 80.0,
                "memory_usage": 85.0,
                "disk_usage": 90.0,
                "response_time": 2.0,
                "error_rate": 5.0,
                "database_connections": 80,
                "cache_hit_rate": 70.0
            },
            "alerting": {
                "enabled": True,
                "email": {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "sender_email": "",
                    "sender_password": "",
                    "recipients": []
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {}
                },
                "cooldown_minutes": 15
            }
        }
        
        # Save default config
        with open("production_monitor_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info("Generated default monitoring config")
        return config
    
    async def start_monitoring(self):
        """Start production monitoring."""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        logger.info("Starting production monitoring...")
        
        while self.monitoring_active:
            try:
                await self._collect_metrics()
                await self._check_thresholds()
                await self._cleanup_old_data()
                await asyncio.sleep(self.config['monitoring']['interval'])
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def stop_monitoring(self):
        """Stop production monitoring."""
        self.monitoring_active = False
        logger.info("Stopping production monitoring...")
    
    async def _collect_metrics(self):
        """Collect performance metrics."""
        timestamp = time.time()
        
        # System metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application metrics (would integrate with existing metrics system)
        app_metrics = await self._get_application_metrics()
        
        # Database metrics
        db_metrics = await self._get_database_metrics()
        
        # Cache metrics
        cache_metrics = await self._get_cache_metrics()
        
        # Network metrics
        network = psutil.net_io_counters()
        
        # Create metrics
        metrics = [
            PerformanceMetric(timestamp, "cpu_usage", cpu_usage, "%", {}),
            PerformanceMetric(timestamp, "memory_usage", memory.percent, "%", {}),
            PerformanceMetric(timestamp, "memory_used_gb", memory.used / (1024**3), "GB", {}),
            PerformanceMetric(timestamp, "disk_usage", disk.percent, "%", {}),
            PerformanceMetric(timestamp, "disk_free_gb", disk.free / (1024**3), "GB", {}),
            PerformanceMetric(timestamp, "network_bytes_sent", network.bytes_sent, "bytes", {}),
            PerformanceMetric(timestamp, "network_bytes_recv", network.bytes_recv, "bytes", {}),
        ]
        
        # Add application metrics
        for key, value in app_metrics.items():
            metrics.append(PerformanceMetric(timestamp, key, value, "", {}))
        
        # Add database metrics
        for key, value in db_metrics.items():
            metrics.append(PerformanceMetric(timestamp, f"db_{key}", value, "", {}))
        
        # Add cache metrics
        for key, value in cache_metrics.items():
            metrics.append(PerformanceMetric(timestamp, f"cache_{key}", value, "", {}))
        
        # Store metrics
        async with self.lock:
            self.metrics_history.extend(metrics)
        
        logger.debug(f"Collected {len(metrics)} metrics")
    
    async def _get_application_metrics(self) -> Dict[str, float]:
        """Get application-specific metrics."""
        # This would integrate with the existing metrics system
        try:
            from ..monitoring.metrics import metrics_collector
            
            latest_metrics = metrics_collector.get_latest_metrics()
            
            if latest_metrics['system']:
                return {
                    'app_request_count': latest_metrics['application']['request_count'] if latest_metrics['application'] else 0,
                    'app_error_count': latest_metrics['application']['error_count'] if latest_metrics['application'] else 0,
                    'app_response_time_avg': latest_metrics['application']['request_duration_avg'] if latest_metrics['application'] else 0,
                    'app_active_connections': latest_metrics['application']['active_connections'] if latest_metrics['application'] else 0
                }
            else:
                return {}
        except ImportError:
            return {}
    
    async def _get_database_metrics(self) -> Dict[str, float]:
        """Get database-specific metrics."""
        try:
            from ..db.integration_manager import db_manager
            
            # Get database health and stats
            health = await db_manager.health_check('default')
            stats = await db_manager.get_connection_stats('default')
            
            return {
                'db_health': 1 if health['status'] == 'healthy' else 0,
                'db_connection_pool_size': stats.get('pool_size', 0),
                'db_checked_out_connections': stats.get('checked_out', 0),
                'db_response_time': health.get('duration', 0)
            }
        except ImportError:
            return {}
    
    async def _get_cache_metrics(self) -> Dict[str, float]:
        """Get cache-specific metrics."""
        try:
            from ..cache.strategic_cache import strategic_cache
            
            stats = strategic_cache.get_stats()
            
            return {
                'cache_hit_rate': stats['total_hit_rate'],
                'cache_l1_hit_rate': stats['l1_hit_rate'],
                'cache_l2_hit_rate': stats['l2_hit_rate'],
                'cache_size': stats['memory_cache_size']
            }
        except ImportError:
            return {}
    
    async def _check_thresholds(self):
        """Check metrics against thresholds and generate alerts."""
        if not self.config['monitoring']['enabled']:
            return
        
        current_time = time.time()
        time_window = 300  # 5 minutes
        
        async with self.lock:
            # Get recent metrics
            recent_metrics = [
                m for m in self.metrics_history
                if current_time - m.timestamp <= time_window
            ]
        
        # Group metrics by name
        metrics_by_name = {}
        for metric in recent_metrics:
            if metric.metric_name not in metrics_by_name:
                metrics_by_name[metric.metric_name] = []
            metrics_by_name[metric.metric_name].append(metric.value)
        
        # Check thresholds
        for metric_name, values in metrics_by_name.items():
            if metric_name in self.thresholds:
                threshold = self.thresholds[metric_name]
                current_value = statistics.mean(values) if values else 0
                
                await self._evaluate_threshold(metric_name, current_value, threshold)
    
    async def _evaluate_threshold(self, metric_name: str, current_value: float, threshold: float):
        """Evaluate a single metric against its threshold."""
        alert_key = f"{metric_name}_threshold"
        
        # Determine if we should alert
        should_alert = False
        alert_level = AlertLevel.INFO
        
        if metric_name in ['cache_hit_rate']:
            # Lower is worse for hit rate
            if current_value < threshold:
                should_alert = True
                alert_level = AlertLevel.WARNING if current_value > threshold * 0.8 else AlertLevel.CRITICAL
        else:
            # Higher is worse for most metrics
            if current_value > threshold:
                should_alert = True
                alert_level = AlertLevel.WARNING if current_value < threshold * 1.2 else AlertLevel.CRITICAL
        
        # Check if we should create a new alert
        if should_alert:
            if alert_key not in self.active_alerts:
                await self._create_alert(alert_level, metric_name, current_value, threshold)
        else:
            # Clear existing alert
            if alert_key in self.active_alerts:
                await self._clear_alert(alert_key)
    
    async def _create_alert(self, level: AlertLevel, metric_name: str, value: float, threshold: float):
        """Create a new alert."""
        alert = Alert(
            timestamp=time.time(),
            level=level,
            title=f"{metric_name.replace('_', ' ').title()} Threshold Exceeded",
            message=f"{metric_name} is {value:.2f}, threshold is {threshold:.2f}",
            metric_name=metric_name,
            value=value,
            threshold=threshold
        )
        
        async with self.lock:
            self.alerts.append(alert)
            self.active_alerts[f"{metric_name}_threshold"] = alert
        
        logger.warning(f"Alert created: {alert.title}")
        await self._send_alert(alert)
    
    async def _clear_alert(self, alert_key: str):
        """Clear an active alert."""
        async with self.lock:
            if alert_key in self.active_alerts:
                alert = self.active_alerts.pop(alert_key)
                alert.message = f"Resolved: {alert.message}"
                self.alerts.append(alert)
        
        logger.info(f"Alert cleared: {alert_key}")
    
    async def _send_alert(self, alert: Alert):
        """Send alert via configured channels."""
        if not self.alerting_config.get('enabled', False):
            return
        
        # Email alerting
        if 'email' in self.alerting_config:
            await self._send_email_alert(alert)
        
        # Webhook alerting
        if 'webhook' in self.alerting_config and self.alerting_config['webhook'].get('enabled', False):
            await self._send_webhook_alert(alert)
    
    async def _send_email_alert(self, alert: Alert):
        """Send email alert."""
        email_config = self.alerting_config['email']
        
        if not email_config.get('sender_email') or not email_config.get('recipients'):
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = ', '.join(email_config['recipients'])
            msg['Subject'] = f"[{alert.level.value.upper()}] {alert.title}"
            
            body = f"""
Alert Details:
- Level: {alert.level.value.upper()}
- Time: {datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
- Metric: {alert.metric_name}
- Current Value: {alert.value}
- Threshold: {alert.threshold}
- Message: {alert.message}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, alert: Alert):
        """Send webhook alert."""
        webhook_config = self.alerting_config['webhook']
        
        try:
            payload = {
                'timestamp': alert.timestamp,
                'level': alert.level.value,
                'title': alert.title,
                'message': alert.message,
                'metric_name': alert.metric_name,
                'value': alert.value,
                'threshold': alert.threshold
            }
            
            response = requests.post(
                webhook_config['url'],
                json=payload,
                headers=webhook_config.get('headers', {}),
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook alert sent for {alert.title}")
            else:
                logger.error(f"Webhook alert failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old metrics and alerts."""
        retention_hours = self.config['monitoring']['retention_hours']
        cutoff_time = time.time() - (retention_hours * 3600)
        
        async with self.lock:
            # Clean up old metrics
            self.metrics_history = [
                m for m in self.metrics_history
                if m.timestamp > cutoff_time
            ]
            
            # Clean up old alerts (keep for longer)
            alert_cutoff_time = time.time() - (retention_hours * 3600 * 24)  # 24x retention for alerts
            self.alerts = [
                a for a in self.alerts
                if a.timestamp > alert_cutoff_time
            ]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        current_time = time.time()
        time_window = 3600  # 1 hour
        
        async def get_data():
            async with self.lock:
                recent_metrics = [
                    m for m in self.metrics_history
                    if current_time - m.timestamp <= time_window
                ]
            
            # Group metrics by name and calculate statistics
            metrics_stats = {}
            for metric_name in set(m.metric_name for m in recent_metrics):
                values = [m.value for m in recent_metrics if m.metric_name == metric_name]
                if values:
                    metrics_stats[metric_name] = {
                        'current': values[-1],
                        'average': statistics.mean(values),
                        'min': min(values),
                        'max': max(values),
                        'count': len(values)
                    }
            
            return {
                'metrics': metrics_stats,
                'alerts': [asdict(alert) for alert in self.alerts[-50:]],  # Last 50 alerts
                'active_alerts': len(self.active_alerts),
                'monitoring_status': 'active' if self.monitoring_active else 'inactive',
                'timestamp': current_time
            }
        
        return asyncio.run(get_data())
    
    async def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        dashboard_data = self.get_dashboard_data()
        
        # Calculate system health score
        health_score = 100
        issues = []
        
        for metric_name, stats in dashboard_data['metrics'].items():
            if metric_name in self.thresholds:
                threshold = self.thresholds[metric_name]
                current = stats['current']
                
                if metric_name in ['cache_hit_rate']:
                    if current < threshold:
                        health_score -= 20
                        issues.append(f"{metric_name}: {current:.2f} < {threshold:.2f}")
                else:
                    if current > threshold:
                        health_score -= 20
                        issues.append(f"{metric_name}: {current:.2f} > {threshold:.2f}")
        
        return {
            'health_score': max(0, health_score),
            'status': 'healthy' if health_score >= 80 else 'warning' if health_score >= 60 else 'critical',
            'issues': issues,
            'dashboard_data': dashboard_data,
            'timestamp': time.time()
        }


# Global monitor instance
production_monitor = ProductionMonitor()


def setup_production_monitoring():
    """Setup production monitoring."""
    # Start monitoring in background
    asyncio.create_task(production_monitor.start_monitoring())
    logger.info("Production monitoring setup completed")


async def get_monitoring_status() -> Dict[str, Any]:
    """Get current monitoring status."""
    return production_monitor.get_dashboard_data()


async def get_health_status() -> Dict[str, Any]:
    """Get current health status."""
    return await production_monitor.get_health_report()