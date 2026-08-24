"""Default-deny authorization for registered tools."""

from __future__ import annotations

from ..errors import ToolPermissionDeniedError
from ..models import Agent
from .models import ToolDefinition


class DefaultDenyToolPolicy:
    """Requires both an exact tool grant and every declared permission."""

    def authorize(self, agent: Agent, definition: ToolDefinition) -> None:
        capability = next(
            (
                item
                for item in agent.tool_capabilities
                if item.name == definition.name
            ),
            None,
        )
        if capability is None:
            raise ToolPermissionDeniedError(
                "agent has no grant for the requested tool",
                details={
                    "agent_id": agent.agent_id,
                    "tool_name": definition.name,
                    "decision": "deny",
                    "reason": "missing_tool_grant",
                },
            )
        missing = definition.permission.permissions - capability.permissions
        if missing:
            raise ToolPermissionDeniedError(
                "agent grant does not include every required permission",
                details={
                    "agent_id": agent.agent_id,
                    "tool_name": definition.name,
                    "decision": "deny",
                    "missing_permissions": sorted(missing),
                },
            )
