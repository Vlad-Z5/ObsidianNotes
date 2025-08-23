# Networking CDN & Caching

## Overview

Content Delivery Networks (CDNs) and caching strategies provide essential performance optimization by distributing content closer to users and reducing server load through intelligent caching. This guide covers CDN architectures, caching policies, edge computing, performance optimization, and enterprise CDN implementations crucial for DevOps engineers managing global applications and content delivery.

## CDN Fundamentals and Architecture

### CDN Types and Distribution Models

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
import time
import hashlib
import json
from datetime import datetime, timedelta
import requests

class CDNType(Enum):
    PULL = "pull"
    PUSH = "push"
    HYBRID = "hybrid"

class CachePolicy(Enum):
    NO_CACHE = "no-cache"
    CACHE = "cache"
    CACHE_AND_REVALIDATE = "cache-revalidate"
    AGGRESSIVE_CACHE = "aggressive-cache"

class ContentType(Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    STREAMING = "streaming"
    API = "api"

@dataclass
class CDNEndpoint:
    location: str
    region: str
    pop_name: str
    capacity_gbps: int
    latency_ms: float
    active: bool
    supported_protocols: List[str]

@dataclass
class CacheRule:
    path_pattern: str
    content_type: ContentType
    cache_policy: CachePolicy
    ttl_seconds: int
    compression_enabled: bool
    edge_side_includes: bool
    custom_headers: Dict[str, str]

@dataclass
class CDNDistribution:
    name: str
    origin_domain: str
    cdn_domain: str
    endpoints: List[CDNEndpoint]
    cache_rules: List[CacheRule]
    ssl_certificate: str
    monitoring_enabled: bool

class EnterpriseCDNManager:
    def __init__(self):
        self.distributions = {}
        self.cache_statistics = {}
        self.performance_metrics = {}
        
    def create_distribution(self, name: str, origin_domain: str, cdn_domain: str) -> CDNDistribution:
        """Create a new CDN distribution"""
        distribution = CDNDistribution(
            name=name,
            origin_domain=origin_domain,
            cdn_domain=cdn_domain,
            endpoints=[],
            cache_rules=[],
            ssl_certificate="",
            monitoring_enabled=True
        )
        
        self.distributions[name] = distribution
        return distribution
    
    def add_global_endpoints(self, distribution_name: str):
        """Add global CDN endpoints for worldwide distribution"""
        if distribution_name not in self.distributions:
            return "Distribution not found"
        
        global_endpoints = [
            CDNEndpoint("North America - East", "us-east-1", "IAD", 100, 25.0, True, ["HTTP/2", "HTTP/3"]),
            CDNEndpoint("North America - West", "us-west-1", "SFO", 100, 30.0, True, ["HTTP/2", "HTTP/3"]),
            CDNEndpoint("Europe - West", "eu-west-1", "LHR", 80, 15.0, True, ["HTTP/2", "HTTP/3"]),
            CDNEndpoint("Europe - Central", "eu-central-1", "FRA", 80, 20.0, True, ["HTTP/2", "HTTP/3"]),
            CDNEndpoint("Asia Pacific - Northeast", "ap-northeast-1", "NRT", 60, 40.0, True, ["HTTP/2"]),
            CDNEndpoint("Asia Pacific - Southeast", "ap-southeast-1", "SIN", 60, 45.0, True, ["HTTP/2"]),
            CDNEndpoint("South America", "sa-east-1", "GRU", 40, 60.0, True, ["HTTP/2"]),
            CDNEndpoint("Australia", "ap-southeast-2", "SYD", 40, 55.0, True, ["HTTP/2"]),
            CDNEndpoint("India", "ap-south-1", "BOM", 40, 50.0, True, ["HTTP/2"]),
            CDNEndpoint("Africa", "af-south-1", "CPT", 20, 80.0, True, ["HTTP/2"])
        ]
        
        self.distributions[distribution_name].endpoints = global_endpoints
        return f"Added {len(global_endpoints)} global endpoints to {distribution_name}"
    
    def configure_caching_policies(self, distribution_name: str):
        """Configure comprehensive caching policies"""
        if distribution_name not in self.distributions:
            return "Distribution not found"
        
        cache_rules = [
            # Static assets - aggressive caching
            CacheRule(
                path_pattern="/static/*",
                content_type=ContentType.STATIC,
                cache_policy=CachePolicy.AGGRESSIVE_CACHE,
                ttl_seconds=31536000,  # 1 year
                compression_enabled=True,
                edge_side_includes=False,
                custom_headers={"Cache-Control": "public, max-age=31536000, immutable"}
            ),
            
            # Images - long cache with compression
            CacheRule(
                path_pattern="*.{jpg,jpeg,png,gif,webp,svg}",
                content_type=ContentType.STATIC,
                cache_policy=CachePolicy.AGGRESSIVE_CACHE,
                ttl_seconds=2592000,  # 30 days
                compression_enabled=True,
                edge_side_includes=False,
                custom_headers={"Cache-Control": "public, max-age=2592000"}
            ),
            
            # CSS and JavaScript - versioned caching
            CacheRule(
                path_pattern="*.{css,js}",
                content_type=ContentType.STATIC,
                cache_policy=CachePolicy.AGGRESSIVE_CACHE,
                ttl_seconds=2592000,  # 30 days
                compression_enabled=True,
                edge_side_includes=False,
                custom_headers={"Cache-Control": "public, max-age=2592000"}
            ),
            
            # HTML pages - short cache with revalidation
            CacheRule(
                path_pattern="*.html",
                content_type=ContentType.DYNAMIC,
                cache_policy=CachePolicy.CACHE_AND_REVALIDATE,
                ttl_seconds=3600,  # 1 hour
                compression_enabled=True,
                edge_side_includes=True,
                custom_headers={"Cache-Control": "public, max-age=3600, must-revalidate"}
            ),
            
            # API endpoints - minimal caching
            CacheRule(
                path_pattern="/api/*",
                content_type=ContentType.API,
                cache_policy=CachePolicy.CACHE,
                ttl_seconds=300,  # 5 minutes
                compression_enabled=True,
                edge_side_includes=False,
                custom_headers={"Cache-Control": "public, max-age=300"}
            ),
            
            # Dynamic content - no cache
            CacheRule(
                path_pattern="/admin/*",
                content_type=ContentType.DYNAMIC,
                cache_policy=CachePolicy.NO_CACHE,
                ttl_seconds=0,
                compression_enabled=True,
                edge_side_includes=False,
                custom_headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
            ),
            
            # Video streaming - streaming optimized
            CacheRule(
                path_pattern="*.{mp4,webm,m3u8,ts}",
                content_type=ContentType.STREAMING,
                cache_policy=CachePolicy.AGGRESSIVE_CACHE,
                ttl_seconds=86400,  # 1 day
                compression_enabled=False,  # Don't compress video
                edge_side_includes=False,
                custom_headers={"Cache-Control": "public, max-age=86400"}
            ),
            
            # Fonts - long cache
            CacheRule(
                path_pattern="*.{woff,woff2,ttf,eot}",
                content_type=ContentType.STATIC,
                cache_policy=CachePolicy.AGGRESSIVE_CACHE,
                ttl_seconds=31536000,  # 1 year
                compression_enabled=True,
                edge_side_includes=False,
                custom_headers={"Cache-Control": "public, max-age=31536000, immutable"}
            )
        ]
        
        self.distributions[distribution_name].cache_rules = cache_rules
        return f"Configured {len(cache_rules)} caching policies for {distribution_name}"
    
    def calculate_cache_hit_ratio(self, distribution_name: str, requests_data: List[Dict]) -> Dict:
        """Calculate cache hit ratio and performance metrics"""
        if distribution_name not in self.distributions:
            return {"error": "Distribution not found"}
        
        total_requests = len(requests_data)
        cache_hits = 0
        cache_misses = 0
        total_response_time = 0
        bandwidth_saved = 0
        
        for request in requests_data:
            total_response_time += request.get('response_time_ms', 0)
            
            if request.get('cache_status') == 'HIT':
                cache_hits += 1
                bandwidth_saved += request.get('size_bytes', 0)
            elif request.get('cache_status') == 'MISS':
                cache_misses += 1
        
        hit_ratio = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        avg_response_time = total_response_time / total_requests if total_requests > 0 else 0
        
        metrics = {
            'distribution_name': distribution_name,
            'total_requests': total_requests,
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'hit_ratio_percent': round(hit_ratio, 2),
            'avg_response_time_ms': round(avg_response_time, 2),
            'bandwidth_saved_mb': round(bandwidth_saved / (1024 * 1024), 2),
            'performance_improvement': round((100 - avg_response_time) / 100, 2) if avg_response_time < 100 else 0
        }
        
        self.performance_metrics[distribution_name] = metrics
        return metrics
    
    def optimize_cache_settings(self, distribution_name: str, usage_patterns: Dict):
        """Optimize cache settings based on usage patterns"""
        if distribution_name not in self.distributions:
            return "Distribution not found"
        
        optimizations = []
        distribution = self.distributions[distribution_name]
        
        # Analyze content types and adjust TTL
        for content_type, stats in usage_patterns.items():
            hit_ratio = stats.get('hit_ratio', 0)
            avg_size = stats.get('avg_size_kb', 0)
            frequency = stats.get('requests_per_hour', 0)
            
            # Find matching cache rule
            for rule in distribution.cache_rules:
                if content_type in rule.path_pattern:
                    old_ttl = rule.ttl_seconds
                    
                    # Increase TTL for high hit ratio content
                    if hit_ratio > 80 and frequency > 100:
                        rule.ttl_seconds = min(rule.ttl_seconds * 2, 31536000)
                        optimizations.append(f"Increased TTL for {content_type}: {old_ttl} -> {rule.ttl_seconds}")
                    
                    # Decrease TTL for low hit ratio content
                    elif hit_ratio < 30 and frequency > 50:
                        rule.ttl_seconds = max(rule.ttl_seconds // 2, 300)
                        optimizations.append(f"Decreased TTL for {content_type}: {old_ttl} -> {rule.ttl_seconds}")
                    
                    # Enable compression for large files with low compression
                    if avg_size > 100 and not rule.compression_enabled:
                        rule.compression_enabled = True
                        optimizations.append(f"Enabled compression for {content_type}")
        
        return {
            'distribution': distribution_name,
            'optimizations_applied': optimizations,
            'total_optimizations': len(optimizations)
        }

# Example enterprise CDN setup
cdn_manager = EnterpriseCDNManager()

# Create distribution for e-commerce site
distribution = cdn_manager.create_distribution(
    "ecommerce-cdn",
    "origin.example-company.com",
    "cdn.example-company.com"
)

# Add global endpoints
endpoint_result = cdn_manager.add_global_endpoints("ecommerce-cdn")
print(f"✅ {endpoint_result}")

# Configure caching policies
cache_result = cdn_manager.configure_caching_policies("ecommerce-cdn")
print(f"✅ {cache_result}")

# Simulate request data for analysis
sample_requests = [
    {"url": "/static/css/main.css", "cache_status": "HIT", "response_time_ms": 12, "size_bytes": 45000},
    {"url": "/api/products", "cache_status": "MISS", "response_time_ms": 250, "size_bytes": 12000},
    {"url": "/images/product1.jpg", "cache_status": "HIT", "response_time_ms": 15, "size_bytes": 156000},
    {"url": "/admin/dashboard", "cache_status": "MISS", "response_time_ms": 180, "size_bytes": 8000},
    {"url": "/static/js/app.js", "cache_status": "HIT", "response_time_ms": 10, "size_bytes": 89000}
] * 1000  # Simulate 5000 requests

# Calculate performance metrics
metrics = cdn_manager.calculate_cache_hit_ratio("ecommerce-cdn", sample_requests)
print(f"\nCDN Performance Metrics:")
print(f"Cache Hit Ratio: {metrics['hit_ratio_percent']}%")
print(f"Average Response Time: {metrics['avg_response_time_ms']}ms")
print(f"Bandwidth Saved: {metrics['bandwidth_saved_mb']}MB")

# Optimize based on usage patterns
usage_patterns = {
    "css": {"hit_ratio": 95, "avg_size_kb": 44, "requests_per_hour": 500},
    "api": {"hit_ratio": 25, "avg_size_kb": 12, "requests_per_hour": 200},
    "images": {"hit_ratio": 88, "avg_size_kb": 152, "requests_per_hour": 800}
}

optimization_result = cdn_manager.optimize_cache_settings("ecommerce-cdn", usage_patterns)
print(f"\nOptimization Results:")
for opt in optimization_result['optimizations_applied']:
    print(f"  • {opt}")
```

## CloudFront CDN Configuration with Terraform

### Enterprise CloudFront Distribution

```hcl
# cloudfront-cdn.tf - Comprehensive CloudFront CDN setup

variable "domain_name" {
  description = "Primary domain name"
  type        = string
  default     = "example-company.com"
}

variable "origin_domain_name" {
  description = "Origin server domain"
  type        = string
  default     = "origin.example-company.com"
}

variable "ssl_certificate_arn" {
  description = "ACM certificate ARN for SSL"
  type        = string
}

variable "enable_logging" {
  description = "Enable CloudFront access logging"
  type        = bool
  default     = true
}

# S3 bucket for access logs
resource "aws_s3_bucket" "cdn_logs" {
  bucket = "${var.domain_name}-cdn-logs"

  tags = {
    Name        = "CDN Access Logs"
    Environment = "production"
  }
}

resource "aws_s3_bucket_versioning" "cdn_logs" {
  bucket = aws_s3_bucket.cdn_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "cdn_logs" {
  bucket = aws_s3_bucket.cdn_logs.id

  rule {
    id     = "log_lifecycle"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

# Origin Request Policy
resource "aws_cloudfront_origin_request_policy" "enterprise_policy" {
  name    = "enterprise-origin-request-policy"
  comment = "Enterprise origin request policy"

  cookies_config {
    cookie_behavior = "whitelist"
    cookies {
      items = ["sessionid", "csrftoken", "user_pref"]
    }
  }

  headers_config {
    header_behavior = "whitelist"
    headers {
      items = [
        "Accept",
        "Accept-Encoding",
        "Accept-Language",
        "Authorization",
        "CloudFront-Viewer-Country",
        "Host",
        "Origin",
        "Referer",
        "User-Agent"
      ]
    }
  }

  query_strings_config {
    query_string_behavior = "whitelist"
    query_strings {
      items = ["page", "sort", "filter", "version"]
    }
  }
}

# Cache Policy for static assets
resource "aws_cloudfront_cache_policy" "static_assets" {
  name        = "static-assets-cache-policy"
  comment     = "Cache policy for static assets"
  default_ttl = 86400
  max_ttl     = 31536000
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true

    cookies_config {
      cookie_behavior = "none"
    }

    headers_config {
      header_behavior = "whitelist"
      headers {
        items = ["Accept-Encoding"]
      }
    }

    query_strings_config {
      query_string_behavior = "whitelist"
      query_strings {
        items = ["version", "v"]
      }
    }
  }
}

# Cache Policy for dynamic content
resource "aws_cloudfront_cache_policy" "dynamic_content" {
  name        = "dynamic-content-cache-policy"
  comment     = "Cache policy for dynamic content"
  default_ttl = 300
  max_ttl     = 3600
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true

    cookies_config {
      cookie_behavior = "whitelist"
      cookies {
        items = ["sessionid", "user_pref"]
      }
    }

    headers_config {
      header_behavior = "whitelist"
      headers {
        items = ["Accept", "Accept-Encoding", "Authorization"]
      }
    }

    query_strings_config {
      query_string_behavior = "all"
    }
  }
}

# Response Headers Policy
resource "aws_cloudfront_response_headers_policy" "security_headers" {
  name    = "security-headers-policy"
  comment = "Security headers for enterprise applications"

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      override                   = false
    }

    content_type_options {
      override = false
    }

    frame_options {
      frame_option = "DENY"
      override     = false
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = false
    }
  }

  custom_headers_config {
    items {
      header   = "X-Custom-Header"
      value    = "Enterprise-CDN"
      override = false
    }

    items {
      header   = "X-Content-Security-Policy"
      value    = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
      override = false
    }
  }

  cors_config {
    access_control_allow_credentials = false

    access_control_allow_headers {
      items = ["*"]
    }

    access_control_allow_methods {
      items = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
    }

    access_control_allow_origins {
      items = ["https://${var.domain_name}"]
    }

    access_control_expose_headers {
      items = ["X-Custom-Header"]
    }

    access_control_max_age_sec = 3600
    origin_override            = true
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "enterprise_cdn" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Enterprise CDN Distribution"
  default_root_object = "index.html"
  price_class         = "PriceClass_All"
  http_version        = "http2and3"

  aliases = [
    var.domain_name,
    "www.${var.domain_name}",
    "cdn.${var.domain_name}"
  ]

  # Primary origin
  origin {
    domain_name = var.origin_domain_name
    origin_id   = "primary-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    custom_header {
      name  = "X-Forwarded-Host"
      value = var.domain_name
    }
  }

  # S3 origin for static assets
  origin {
    domain_name = "static-assets.s3.amazonaws.com"
    origin_id   = "s3-static-assets"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.static_assets.cloudfront_access_identity_path
    }
  }

  # Default cache behavior (dynamic content)
  default_cache_behavior {
    target_origin_id         = "primary-origin"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods           = ["GET", "HEAD", "OPTIONS"]
    compress                 = true
    cache_policy_id          = aws_cloudfront_cache_policy.dynamic_content.id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.enterprise_policy.id
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id

    # Lambda@Edge function for request processing
    lambda_function_association {
      event_type   = "viewer-request"
      lambda_arn   = aws_lambda_function.edge_request_processor.qualified_arn
      include_body = false
    }
  }

  # Static assets behavior
  ordered_cache_behavior {
    path_pattern             = "/static/*"
    target_origin_id         = "s3-static-assets"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["GET", "HEAD", "OPTIONS"]
    cached_methods           = ["GET", "HEAD"]
    compress                 = true
    cache_policy_id          = aws_cloudfront_cache_policy.static_assets.id
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # Images behavior
  ordered_cache_behavior {
    path_pattern           = "*.jpg"
    target_origin_id       = "primary-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = aws_cloudfront_cache_policy.static_assets.id

    # Image optimization Lambda@Edge
    lambda_function_association {
      event_type = "origin-response"
      lambda_arn = aws_lambda_function.image_optimizer.qualified_arn
    }
  }

  # API behavior with shorter cache
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = "primary-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = aws_cloudfront_cache_policy.dynamic_content.id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.enterprise_policy.id

    # API rate limiting
    lambda_function_association {
      event_type   = "viewer-request"
      lambda_arn   = aws_lambda_function.api_rate_limiter.qualified_arn
      include_body = false
    }
  }

  # Admin panel - no cache
  ordered_cache_behavior {
    path_pattern           = "/admin/*"
    target_origin_id       = "primary-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    compress               = false

    forwarded_values {
      query_string = true
      headers      = ["*"]

      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # Geographic restrictions
  restrictions {
    geo_restriction {
      restriction_type = "blacklist"
      locations        = ["CN", "RU", "KP"]  # Example restricted countries
    }
  }

  # SSL certificate
  viewer_certificate {
    acm_certificate_arn      = var.ssl_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  # Access logging
  dynamic "logging_config" {
    for_each = var.enable_logging ? [1] : []
    content {
      bucket          = aws_s3_bucket.cdn_logs.bucket_domain_name
      prefix          = "access-logs/"
      include_cookies = false
    }
  }

  tags = {
    Name        = "Enterprise CDN"
    Environment = "production"
  }
}

# Origin Access Identity for S3
resource "aws_cloudfront_origin_access_identity" "static_assets" {
  comment = "OAI for static assets bucket"
}

# Lambda@Edge functions
resource "aws_lambda_function" "edge_request_processor" {
  provider      = aws.us_east_1  # Lambda@Edge must be in us-east-1
  filename      = "edge-request-processor.zip"
  function_name = "edge-request-processor"
  role          = aws_iam_role.lambda_edge_execution.arn
  handler       = "index.handler"
  runtime       = "nodejs18.x"
  timeout       = 5
  publish       = true

  tags = {
    Name = "Edge Request Processor"
  }
}

resource "aws_lambda_function" "image_optimizer" {
  provider      = aws.us_east_1
  filename      = "image-optimizer.zip"
  function_name = "image-optimizer"
  role          = aws_iam_role.lambda_edge_execution.arn
  handler       = "index.handler"
  runtime       = "nodejs18.x"
  timeout       = 30
  memory_size   = 512
  publish       = true

  tags = {
    Name = "Image Optimizer"
  }
}

resource "aws_lambda_function" "api_rate_limiter" {
  provider      = aws.us_east_1
  filename      = "api-rate-limiter.zip"
  function_name = "api-rate-limiter"
  role          = aws_iam_role.lambda_edge_execution.arn
  handler       = "index.handler"
  runtime       = "nodejs18.x"
  timeout       = 5
  publish       = true

  tags = {
    Name = "API Rate Limiter"
  }
}

# IAM role for Lambda@Edge
resource "aws_iam_role" "lambda_edge_execution" {
  name = "lambda-edge-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "edgelambda.amazonaws.com"
          ]
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_edge_execution" {
  role       = aws_iam_role.lambda_edge_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CloudWatch alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "high_4xx_errors" {
  alarm_name          = "cloudfront-high-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4xxErrorRate"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "5"
  alarm_description   = "This metric monitors CloudFront 4xx error rate"

  dimensions = {
    DistributionId = aws_cloudfront_distribution.enterprise_cdn.id
  }

  alarm_actions = [aws_sns_topic.cdn_alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "high_5xx_errors" {
  alarm_name          = "cloudfront-high-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5xxErrorRate"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "This metric monitors CloudFront 5xx error rate"

  dimensions = {
    DistributionId = aws_cloudfront_distribution.enterprise_cdn.id
  }

  alarm_actions = [aws_sns_topic.cdn_alerts.arn]
}

# SNS topic for alerts
resource "aws_sns_topic" "cdn_alerts" {
  name = "cdn-alerts"
}

# Provider for us-east-1 (required for Lambda@Edge)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# Outputs
output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.enterprise_cdn.id
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.enterprise_cdn.domain_name
}

output "cache_policies" {
  value = {
    static_assets    = aws_cloudfront_cache_policy.static_assets.id
    dynamic_content  = aws_cloudfront_cache_policy.dynamic_content.id
  }
}
```

## Advanced Caching Strategies

### Redis Cluster for Application Caching

```python
import redis
import json
import hashlib
import time
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import pickle
import zlib

class EnterpriseRedisCache:
    def __init__(self, host='localhost', port=6379, password=None, cluster_nodes=None):
        if cluster_nodes:
            # Redis Cluster setup
            self.redis_client = redis.RedisCluster(
                startup_nodes=cluster_nodes,
                decode_responses=False,
                password=password,
                max_connections_per_node=20,
                retry_on_timeout=True,
                health_check_interval=30
            )
        else:
            # Single Redis instance
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                password=password,
                decode_responses=False,
                max_connections=100,
                retry_on_timeout=True,
                health_check_interval=30
            )
        
        self.default_ttl = 3600  # 1 hour
        self.compression_threshold = 1024  # Compress objects larger than 1KB
        
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize and optionally compress the value"""
        # Serialize the value
        serialized = pickle.dumps(value)
        
        # Compress if above threshold
        if len(serialized) > self.compression_threshold:
            compressed = zlib.compress(serialized)
            # Add compression marker
            return b'COMPRESSED:' + compressed
        
        return serialized
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize and optionally decompress the value"""
        if data.startswith(b'COMPRESSED:'):
            # Remove compression marker and decompress
            compressed_data = data[11:]  # Remove 'COMPRESSED:' prefix
            decompressed = zlib.decompress(compressed_data)
            return pickle.loads(decompressed)
        
        return pickle.loads(data)
    
    def _generate_cache_key(self, key: str, namespace: str = None) -> str:
        """Generate namespaced cache key"""
        if namespace:
            return f"{namespace}:{key}"
        return key
    
    def set(self, key: str, value: Any, ttl: int = None, namespace: str = None) -> bool:
        """Set a cache value with optional TTL and namespace"""
        try:
            cache_key = self._generate_cache_key(key, namespace)
            serialized_value = self._serialize_value(value)
            ttl = ttl or self.default_ttl
            
            result = self.redis_client.setex(cache_key, ttl, serialized_value)
            return bool(result)
        except Exception as e:
            print(f"Cache SET error: {e}")
            return False
    
    def get(self, key: str, namespace: str = None) -> Optional[Any]:
        """Get a cache value by key"""
        try:
            cache_key = self._generate_cache_key(key, namespace)
            data = self.redis_client.get(cache_key)
            
            if data is None:
                return None
            
            return self._deserialize_value(data)
        except Exception as e:
            print(f"Cache GET error: {e}")
            return None
    
    def delete(self, key: str, namespace: str = None) -> bool:
        """Delete a cache entry"""
        try:
            cache_key = self._generate_cache_key(key, namespace)
            result = self.redis_client.delete(cache_key)
            return result > 0
        except Exception as e:
            print(f"Cache DELETE error: {e}")
            return False
    
    def exists(self, key: str, namespace: str = None) -> bool:
        """Check if a cache key exists"""
        try:
            cache_key = self._generate_cache_key(key, namespace)
            return bool(self.redis_client.exists(cache_key))
        except Exception as e:
            print(f"Cache EXISTS error: {e}")
            return False
    
    def ttl(self, key: str, namespace: str = None) -> int:
        """Get TTL for a cache key"""
        try:
            cache_key = self._generate_cache_key(key, namespace)
            return self.redis_client.ttl(cache_key)
        except Exception as e:
            print(f"Cache TTL error: {e}")
            return -1
    
    def flush_namespace(self, namespace: str) -> int:
        """Flush all keys in a namespace"""
        try:
            pattern = f"{namespace}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache FLUSH_NAMESPACE error: {e}")
            return 0
    
    def mget(self, keys: List[str], namespace: str = None) -> Dict[str, Any]:
        """Get multiple cache values"""
        try:
            cache_keys = [self._generate_cache_key(key, namespace) for key in keys]
            values = self.redis_client.mget(cache_keys)
            
            result = {}
            for i, value in enumerate(values):
                if value is not None:
                    result[keys[i]] = self._deserialize_value(value)
                else:
                    result[keys[i]] = None
            
            return result
        except Exception as e:
            print(f"Cache MGET error: {e}")
            return {key: None for key in keys}
    
    def mset(self, mapping: Dict[str, Any], ttl: int = None, namespace: str = None) -> bool:
        """Set multiple cache values"""
        try:
            ttl = ttl or self.default_ttl
            pipe = self.redis_client.pipeline()
            
            for key, value in mapping.items():
                cache_key = self._generate_cache_key(key, namespace)
                serialized_value = self._serialize_value(value)
                pipe.setex(cache_key, ttl, serialized_value)
            
            results = pipe.execute()
            return all(results)
        except Exception as e:
            print(f"Cache MSET error: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1, namespace: str = None, ttl: int = None) -> int:
        """Increment a numeric value"""
        try:
            cache_key = self._generate_cache_key(key, namespace)
            result = self.redis_client.incrby(cache_key, amount)
            
            # Set TTL if this is a new key
            if ttl and self.redis_client.ttl(cache_key) == -1:
                self.redis_client.expire(cache_key, ttl)
            
            return result
        except Exception as e:
            print(f"Cache INCREMENT error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = self.redis_client.info()
            
            stats = {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'expired_keys': info.get('expired_keys', 0),
                'evicted_keys': info.get('evicted_keys', 0)
            }
            
            # Calculate hit ratio
            hits = stats['keyspace_hits']
            misses = stats['keyspace_misses']
            total = hits + misses
            stats['hit_ratio'] = (hits / total * 100) if total > 0 else 0
            
            return stats
        except Exception as e:
            print(f"Cache STATS error: {e}")
            return {}

class CacheDecorator:
    """Decorator for caching function results"""
    
    def __init__(self, cache: EnterpriseRedisCache, ttl: int = 3600, namespace: str = None):
        self.cache = cache
        self.ttl = ttl
        self.namespace = namespace
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            cache_key = hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = self.cache.get(cache_key, self.namespace)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            self.cache.set(cache_key, result, self.ttl, self.namespace)
            
            return result
        
        return wrapper

# Example usage and cache warming
def setup_enterprise_cache():
    """Setup enterprise Redis cache with cluster configuration"""
    
    # Redis cluster nodes
    cluster_nodes = [
        {"host": "redis-node-1.company.com", "port": 6379},
        {"host": "redis-node-2.company.com", "port": 6379},
        {"host": "redis-node-3.company.com", "port": 6379},
        {"host": "redis-node-4.company.com", "port": 6379},
        {"host": "redis-node-5.company.com", "port": 6379},
        {"host": "redis-node-6.company.com", "port": 6379}
    ]
    
    # Initialize cache
    cache = EnterpriseRedisCache(
        cluster_nodes=cluster_nodes,
        password="secure-redis-password"
    )
    
    return cache

# Initialize cache
enterprise_cache = setup_enterprise_cache()

# Example: Cache expensive database queries
@CacheDecorator(enterprise_cache, ttl=1800, namespace="products")
def get_product_details(product_id: int):
    """Expensive database query - cached for 30 minutes"""
    # Simulate expensive database operation
    import time
    time.sleep(0.5)  # Simulate DB query time
    
    return {
        'id': product_id,
        'name': f'Product {product_id}',
        'price': product_id * 10.99,
        'description': f'Description for product {product_id}',
        'timestamp': datetime.now().isoformat()
    }

@CacheDecorator(enterprise_cache, ttl=300, namespace="analytics")
def get_analytics_data(date_range: str, metric: str):
    """Analytics query - cached for 5 minutes"""
    # Simulate analytics calculation
    import random
    time.sleep(1.0)  # Simulate processing time
    
    return {
        'date_range': date_range,
        'metric': metric,
        'value': random.randint(1000, 10000),
        'trend': random.choice(['up', 'down', 'stable']),
        'generated_at': datetime.now().isoformat()
    }

# Cache warming strategy
def warm_cache():
    """Warm up cache with frequently accessed data"""
    print("Starting cache warm-up...")
    
    # Warm up product cache
    popular_products = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    for product_id in popular_products:
        get_product_details(product_id)
        print(f"Warmed up product {product_id}")
    
    # Warm up analytics cache
    analytics_queries = [
        ("last_7_days", "page_views"),
        ("last_30_days", "unique_visitors"),
        ("last_24_hours", "conversion_rate")
    ]
    
    for date_range, metric in analytics_queries:
        get_analytics_data(date_range, metric)
        print(f"Warmed up analytics: {metric} for {date_range}")
    
    print("Cache warm-up completed!")

# Performance testing
def test_cache_performance():
    """Test cache performance and hit ratios"""
    print("\nTesting cache performance...")
    
    # Test cache hits vs misses
    start_time = time.time()
    
    # First calls (cache misses)
    for i in range(10):
        get_product_details(i)
    
    first_run_time = time.time() - start_time
    
    # Second calls (cache hits)
    start_time = time.time()
    
    for i in range(10):
        get_product_details(i)
    
    second_run_time = time.time() - start_time
    
    print(f"First run (cache misses): {first_run_time:.2f}s")
    print(f"Second run (cache hits): {second_run_time:.2f}s")
    print(f"Performance improvement: {((first_run_time - second_run_time) / first_run_time * 100):.1f}%")
    
    # Display cache statistics
    stats = enterprise_cache.get_stats()
    print(f"\nCache Statistics:")
    print(f"Hit Ratio: {stats.get('hit_ratio', 0):.1f}%")
    print(f"Memory Used: {stats.get('used_memory_human', 'N/A')}")
    print(f"Connected Clients: {stats.get('connected_clients', 0)}")

if __name__ == "__main__":
    # Warm up the cache
    warm_cache()
    
    # Test performance
    test_cache_performance()
```

## Best Practices for Enterprise CDN and Caching

### Content Optimization Strategy
- **Asset bundling and minification** to reduce request count
- **Image optimization** with format selection and compression
- **Progressive loading** for large content and images
- **HTTP/2 and HTTP/3** adoption for improved performance

### Cache Invalidation Patterns
- **Version-based invalidation** using query parameters or file names
- **Tag-based purging** for related content invalidation
- **Geographic purging** for region-specific content updates
- **Automated invalidation** integrated with CI/CD pipelines

### Performance Monitoring
- **Real User Monitoring (RUM)** for actual user experience metrics
- **Synthetic monitoring** for proactive performance testing
- **Cache hit ratio analysis** and optimization
- **Edge location performance** monitoring and optimization

### Security Considerations
- **DDoS protection** at the edge level
- **WAF integration** for application security
- **Rate limiting** and bot protection
- **SSL/TLS termination** with modern protocols

This comprehensive CDN and caching guide provides enterprise-grade content delivery and performance optimization solutions essential for modern DevOps applications serving global audiences.