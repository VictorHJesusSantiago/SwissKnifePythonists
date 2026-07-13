from datetime import UTC, datetime, timedelta

from swissknife.features.cost_whatif import PricedResource, compare_scenarios, estimate
from swissknife.features.iam_least_privilege import GrantedPermission, UsageEvent, find_excess_permissions, recommend_policy
from swissknife.features.orphan_resources import CloudResourceRecord, find_orphans


def test_cost_whatif() -> None:
    resources = [PricedResource("ec2", 0.05, 2)]
    result = estimate(resources, hours=100)
    assert result["total_estimated_cost"] == 10.0
    comparison = compare_scenarios({"pequeno": resources, "grande": [PricedResource("ec2", 0.05, 10)]}, hours=100)
    assert comparison["cheapest"] == "pequeno"


def test_iam_least_privilege() -> None:
    events = [UsageEvent("user1", "s3:GetObject", "bucket1")]
    policy = recommend_policy(events)
    assert policy["user1"]["recommended_actions"] == ["s3:GetObject"]
    excess = find_excess_permissions(events, [GrantedPermission("user1", "s3:DeleteObject")])
    assert excess["user1"] == ["s3:DeleteObject"]


def test_orphan_resources() -> None:
    now = datetime.now(UTC)
    resources = [
        CloudResourceRecord("vol-1", "ebs", attached_to=None, last_used_at=now - timedelta(days=60), monthly_cost=10.0),
        CloudResourceRecord("vol-2", "ebs", attached_to="instance-1", last_used_at=now, monthly_cost=5.0),
    ]
    result = find_orphans(resources, idle_days=30, now=now)
    assert result["orphan_count"] == 1
    assert result["potential_savings"] == 10.0
