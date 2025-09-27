"""
Dispute Resolution Tool for sofIA Agent

Provides automated and human-mediated dispute resolution capabilities
for payment transactions with comprehensive audit trails.
"""

from google.adk.tools import Tool
from typing import Dict, Any, List, Optional

from ...disputes import DisputeManager, DisputeType


def create_dispute(
    transaction_id: str,
    dispute_type: str,
    complainant_id: str,
    respondent_id: str,
    description: str,
    evidence: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new dispute case.

    Args:
        transaction_id: Associated transaction identifier
        dispute_type: Type of dispute (chargeback, fraud, quality, etc.)
        complainant_id: Party filing the dispute
        respondent_id: Party being disputed against
        description: Dispute description
        evidence: Supporting evidence documents

    Returns:
        Created dispute case information
    """
    try:
        manager = DisputeManager()

        dispute_case = manager.create_dispute(
            transaction_id=transaction_id,
            dispute_type=DisputeType(dispute_type),
            complainant_id=complainant_id,
            respondent_id=respondent_id,
            description=description,
            evidence=evidence or []
        )

        return {
            "success": True,
            "dispute_id": dispute_case.dispute_id,
            "status": dispute_case.status.value,
            "created_at": dispute_case.created_at.isoformat(),
            "estimated_resolution": dispute_case.estimated_resolution_date.isoformat() if dispute_case.estimated_resolution_date else None,
            "priority": dispute_case.priority.value
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Dispute creation failed: {str(e)}"
        }


def submit_evidence(
    dispute_id: str,
    party_id: str,
    evidence_type: str,
    evidence_data: Dict[str, Any],
    description: str
) -> Dict[str, Any]:
    """
    Submit evidence for a dispute case.

    Args:
        dispute_id: Dispute case identifier
        party_id: ID of party submitting evidence
        evidence_type: Type of evidence (document, transaction_log, witness, etc.)
        evidence_data: Evidence data and metadata
        description: Evidence description

    Returns:
        Evidence submission status
    """
    try:
        manager = DisputeManager()

        evidence_id = manager.submit_evidence(
            dispute_id=dispute_id,
            party_id=party_id,
            evidence_type=evidence_type,
            evidence_data=evidence_data,
            description=description
        )

        return {
            "success": True,
            "evidence_id": evidence_id,
            "dispute_id": dispute_id,
            "submitted_by": party_id,
            "evidence_type": evidence_type
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Evidence submission failed: {str(e)}"
        }


def get_dispute_status(
    dispute_id: str
) -> Dict[str, Any]:
    """
    Get current status of a dispute case.

    Args:
        dispute_id: Dispute case identifier

    Returns:
        Current dispute status and details
    """
    try:
        manager = DisputeManager()
        dispute_case = manager.get_dispute(dispute_id)

        if not dispute_case:
            return {
                "success": False,
                "error": f"Dispute {dispute_id} not found"
            }

        return {
            "success": True,
            "dispute_id": dispute_case.dispute_id,
            "status": dispute_case.status.value,
            "transaction_id": dispute_case.transaction_id,
            "dispute_type": dispute_case.dispute_type.value,
            "priority": dispute_case.priority.value,
            "created_at": dispute_case.created_at.isoformat(),
            "updated_at": dispute_case.updated_at.isoformat(),
            "resolution_summary": dispute_case.resolution_summary,
            "awarded_amount": dispute_case.awarded_amount,
            "evidence_count": len(dispute_case.evidence)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get dispute status: {str(e)}"
        }


def resolve_dispute(
    dispute_id: str,
    resolution_type: str,
    awarded_to: str,
    awarded_amount: float = 0.0,
    resolution_summary: str = ""
) -> Dict[str, Any]:
    """
    Resolve a dispute case.

    Args:
        dispute_id: Dispute case identifier
        resolution_type: Type of resolution (favor_complainant, favor_respondent, compromise)
        awarded_to: Party receiving the award
        awarded_amount: Amount awarded (if applicable)
        resolution_summary: Summary of resolution reasoning

    Returns:
        Dispute resolution result
    """
    try:
        manager = DisputeManager()

        success = manager.resolve_dispute(
            dispute_id=dispute_id,
            resolution_type=resolution_type,
            awarded_to=awarded_to,
            awarded_amount=awarded_amount,
            resolution_summary=resolution_summary
        )

        if success:
            return {
                "success": True,
                "dispute_id": dispute_id,
                "resolution_type": resolution_type,
                "awarded_to": awarded_to,
                "awarded_amount": awarded_amount,
                "status": "resolved"
            }
        else:
            return {
                "success": False,
                "error": "Failed to resolve dispute"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Dispute resolution failed: {str(e)}"
        }


def escalate_to_arbitration(
    dispute_id: str,
    arbitrator_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Escalate dispute to human arbitration.

    Args:
        dispute_id: Dispute case identifier
        arbitrator_id: Preferred arbitrator (optional, will auto-assign if not provided)

    Returns:
        Arbitration escalation status
    """
    try:
        manager = DisputeManager()

        arbitration_case = manager.escalate_to_arbitration(
            dispute_id=dispute_id,
            arbitrator_id=arbitrator_id
        )

        return {
            "success": True,
            "dispute_id": dispute_id,
            "arbitration_case_id": arbitration_case.case_id,
            "arbitrator_id": arbitration_case.arbitrator_id,
            "status": "in_arbitration",
            "estimated_resolution": arbitration_case.estimated_resolution.isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Arbitration escalation failed: {str(e)}"
        }


def get_dispute_analytics(
    date_range: Dict[str, str] = None,
    dispute_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get dispute analytics and metrics.

    Args:
        date_range: Date range for analytics (start_date, end_date)
        dispute_type: Filter by dispute type

    Returns:
        Dispute analytics and statistics
    """
    try:
        manager = DisputeManager()

        analytics = manager.get_analytics(
            date_range=date_range,
            dispute_type=DisputeType(dispute_type) if dispute_type else None
        )

        return {
            "success": True,
            "analytics": analytics
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get dispute analytics: {str(e)}"
        }


disputes_tool = Tool(
    name="dispute_resolution",
    description="Comprehensive dispute resolution system for payment transactions",
    function_declarations=[
        {
            "name": "create_dispute",
            "description": "Create a new dispute case for a payment transaction",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "Associated transaction identifier"
                    },
                    "dispute_type": {
                        "type": "string",
                        "description": "Type of dispute (chargeback, fraud, quality, etc.)"
                    },
                    "complainant_id": {
                        "type": "string",
                        "description": "Party filing the dispute"
                    },
                    "respondent_id": {
                        "type": "string",
                        "description": "Party being disputed against"
                    },
                    "description": {
                        "type": "string",
                        "description": "Dispute description"
                    },
                    "evidence": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Supporting evidence documents"
                    }
                },
                "required": ["transaction_id", "dispute_type", "complainant_id", "respondent_id", "description"]
            }
        },
        {
            "name": "submit_evidence",
            "description": "Submit evidence for a dispute case",
            "parameters": {
                "type": "object",
                "properties": {
                    "dispute_id": {
                        "type": "string",
                        "description": "Dispute case identifier"
                    },
                    "party_id": {
                        "type": "string",
                        "description": "ID of party submitting evidence"
                    },
                    "evidence_type": {
                        "type": "string",
                        "description": "Type of evidence (document, transaction_log, witness, etc.)"
                    },
                    "evidence_data": {
                        "type": "object",
                        "description": "Evidence data and metadata"
                    },
                    "description": {
                        "type": "string",
                        "description": "Evidence description"
                    }
                },
                "required": ["dispute_id", "party_id", "evidence_type", "evidence_data", "description"]
            }
        },
        {
            "name": "get_dispute_status",
            "description": "Get current status of a dispute case",
            "parameters": {
                "type": "object",
                "properties": {
                    "dispute_id": {
                        "type": "string",
                        "description": "Dispute case identifier"
                    }
                },
                "required": ["dispute_id"]
            }
        },
        {
            "name": "resolve_dispute",
            "description": "Resolve a dispute case with final decision",
            "parameters": {
                "type": "object",
                "properties": {
                    "dispute_id": {
                        "type": "string",
                        "description": "Dispute case identifier"
                    },
                    "resolution_type": {
                        "type": "string",
                        "description": "Type of resolution (favor_complainant, favor_respondent, compromise)"
                    },
                    "awarded_to": {
                        "type": "string",
                        "description": "Party receiving the award"
                    },
                    "awarded_amount": {
                        "type": "number",
                        "description": "Amount awarded (if applicable)",
                        "default": 0.0
                    },
                    "resolution_summary": {
                        "type": "string",
                        "description": "Summary of resolution reasoning"
                    }
                },
                "required": ["dispute_id", "resolution_type", "awarded_to"]
            }
        },
        {
            "name": "escalate_to_arbitration",
            "description": "Escalate dispute to human arbitration",
            "parameters": {
                "type": "object",
                "properties": {
                    "dispute_id": {
                        "type": "string",
                        "description": "Dispute case identifier"
                    },
                    "arbitrator_id": {
                        "type": "string",
                        "description": "Preferred arbitrator (optional, will auto-assign if not provided)"
                    }
                },
                "required": ["dispute_id"]
            }
        },
        {
            "name": "get_dispute_analytics",
            "description": "Get dispute analytics and metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_range": {
                        "type": "object",
                        "description": "Date range for analytics (start_date, end_date)"
                    },
                    "dispute_type": {
                        "type": "string",
                        "description": "Filter by dispute type"
                    }
                }
            }
        }
    ],
    functions={
        "create_dispute": create_dispute,
        "submit_evidence": submit_evidence,
        "get_dispute_status": get_dispute_status,
        "resolve_dispute": resolve_dispute,
        "escalate_to_arbitration": escalate_to_arbitration,
        "get_dispute_analytics": get_dispute_analytics
    }
)