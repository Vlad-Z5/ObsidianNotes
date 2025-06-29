**Customer Expectation:** System is accessible when needed with minimal to no downtime
**Objective:** Achieve and maintain target uptime percentage aligned with business requirements

### Best Practices

- Establish Service Level Objectives (SLOs) based on business impact (99.9%+ for main services)
- Implement multi-zone and multi-region deployments for geographic redundancy
- Design circuit breakers and graceful degradation patterns
- Conduct regular disaster recovery testing and failover drills
- Implement automated health checks and load balancing
- Use error budgets (leftover from availability SLO, e.g. SLO = 99.9%, error budget is .01%) to balance reliability with feature velocity, spend error budget to innovate
- Design for partial failures rather than complete system failures

### Trade-offs and Risks

- Higher availability increases infrastructure costs and maintenance
- Complex redundancy systems can introduce new failures
- Overly conservative change management kills innovation
- Perfect availability is impossible, economically unfeasible, and unreasonable. Efforts to improve availability scale exponentially; even if higher availability point is achieved, there might be outside influences that negate the efforts (e.g. customer may not notice the difference due to their ISP)

### Common Bottlenecks and Resolution Steps

**Single Points of Failure:**
1. Identify critical components through dependency mapping
2. Implement redundancy at each layer (database, application, network)
3. Test failure scenarios regularly through chaos engineering
4. Document and automate recovery procedures, have clear and descriptive runbooks

**Inadequate Monitoring:**
1. Implement comprehensive health checks at all needed system levels
2. Set up synthetic monitoring to detect issues before users
3. Create alerting thresholds that trigger much faster than SLO breach
4. Establish escalation procedures for different severity levels