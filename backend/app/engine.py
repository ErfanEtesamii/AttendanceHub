"""Boundary for the future attendance engine integration.

The onboarding service owns tenant and authorization checks; a concrete engine
must never receive a request without the resolved company id.
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class AttendanceEngineHealth:
    status: str
    provider: str


class AttendanceEngineClient(Protocol):
    def provision_company(self, company_id: UUID) -> AttendanceEngineHealth: ...
    def sync_policy(self, company_id: UUID) -> AttendanceEngineHealth: ...
    def sync_members(self, company_id: UUID) -> AttendanceEngineHealth: ...
    def health(self, company_id: UUID) -> AttendanceEngineHealth: ...


class MockEngineClient:
    def provision_company(self, company_id: UUID) -> AttendanceEngineHealth:
        return AttendanceEngineHealth(status="not_connected", provider="mock")

    def sync_policy(self, company_id: UUID) -> AttendanceEngineHealth:
        return AttendanceEngineHealth(status="not_connected", provider="mock")

    def sync_members(self, company_id: UUID) -> AttendanceEngineHealth:
        return AttendanceEngineHealth(status="not_connected", provider="mock")

    def health(self, company_id: UUID) -> AttendanceEngineHealth:
        return AttendanceEngineHealth(status="not_connected", provider="mock")
