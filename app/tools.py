def check_service_status(service_name: str) -> str:
    """Checks operational health status of an IT service or infrastructure component.

    Args:
        service_name: The name of the service to check (e.g., 'database', 'network', 'auth', 'infrastructure').

    Returns:
        A string containing the current status and health information of the queried service.
    """
    mock_services = {
        "database": "CRITICAL: High CPU utilization (98%) and connection pool exhausted. 500 internal server errors reported.",
        "db": "CRITICAL: High CPU utilization (98%) and connection pool exhausted. 500 internal server errors reported.",
        "network": "DEGRADED: Increased latency (250ms) and packet drop rate on regional gateway.",
        "auth": "HEALTHY: Authentication service operational. SSO and token validation normal.",
        "authentication": "HEALTHY: Authentication service operational. SSO and token validation normal.",
        "infrastructure": "DEGRADED: Node worker-03 in NotReady state. Container reschedule in progress.",
        "software": "HEALTHY: Microservices operating within normal latency SLAs.",
        "payment": "HEALTHY: Payment gateway processing transactions normally.",
    }
    key = service_name.lower().strip()
    for service_key, status in mock_services.items():
        if service_key in key or key in service_key:
            return f"Status for '{service_name}': {status}"

    return f"Status for '{service_name}': HEALTHY: No known active incidents reported for this service."


def escalate_to_human(urgency_level: str) -> dict[str, str | bool]:
    """Escalates an urgent or high-severity IT ticket for immediate human operator review.

    Args:
        urgency_level: The urgency level of the ticket triggering escalation (e.g., 'HIGH', 'CRITICAL').

    Returns:
        A dictionary containing escalation status, urgency level, and assigned response team.
    """
    return {
        "escalated": True,
        "urgency_level": urgency_level,
        "assigned_team": "On-Call Tier-3 Engineering Team",
        "message": f"Ticket successfully escalated with urgency level '{urgency_level}'. On-call engineer notified.",
    }
