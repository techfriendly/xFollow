from __future__ import annotations

from typing import Any

from . import db
from .config import load_runtime_config


def _available(table: str) -> bool:
    config = load_runtime_config()
    if not config.integrations_enabled or not db.db_available():
        return False
    try:
        row = db.fetch_one("SELECT to_regclass(%s) AS relation", (f"public.{table}",))
    except Exception:
        return False
    return bool(row and row.get("relation"))


def status() -> dict[str, Any]:
    return {
        "enabled": load_runtime_config().integrations_enabled,
        "xtender": {"available": _available("procurement_workspaces"), "relation": "public.procurement_workspaces"},
        "pcsp": {"available": _available("kb_tenders"), "relation": "public.kb_tenders"},
        "pcsp_evidence": {"available": _available("kb_chunks"), "relation": "public.kb_chunks"},
        "xreview": {"available": _relation_available("xreview.award_handoffs"), "relation": "xreview.award_handoffs"},
    }


def _relation_available(relation: str) -> bool:
    config = load_runtime_config()
    if not config.integrations_enabled or not db.db_available():
        return False
    try:
        row = db.fetch_one("SELECT to_regclass(%s) AS relation", (relation,))
    except Exception:
        return False
    return bool(row and row.get("relation"))


def xtender_candidates(tenant_id: str, query: str | None = None) -> list[dict[str, Any]]:
    if not _available("procurement_workspaces"):
        return []
    clauses = ["tenant_id = %s"]
    params: list[Any] = [tenant_id]
    if query:
        clauses.append("(title ILIKE %s OR coalesce(data->>'file_number', '') ILIKE %s)")
        params.extend([f"%{query}%", f"%{query}%"])
    try:
        return db.fetch_all(
            f"""
            SELECT id, tenant_id, title, unit, status, active_document_type, data, updated_at
            FROM public.procurement_workspaces
            WHERE {' AND '.join(clauses)}
            ORDER BY updated_at DESC
            LIMIT 40
            """,
            tuple(params),
        )
    except Exception:
        return []


def get_xtender(tenant_id: str, workspace_id: str) -> dict[str, Any] | None:
    if not _available("procurement_workspaces"):
        return None
    try:
        return db.fetch_one(
            "SELECT * FROM public.procurement_workspaces WHERE tenant_id = %s AND id = %s",
            (tenant_id, workspace_id),
        )
    except Exception:
        return None


def pcsp_candidates(query: str | None = None) -> list[dict[str, Any]]:
    if not _available("kb_tenders"):
        return []
    clauses = ["status IN ('ADJ', 'RES')"]
    params: list[Any] = []
    if query:
        clauses.append("(title ILIKE %s OR coalesce(expediente, '') ILIKE %s OR coalesce(contracting_body, '') ILIKE %s)")
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    try:
        return db.fetch_all(
            f"""
            SELECT id, expediente, title, status, cpv, contracting_body, budget_without_tax,
                   budget_with_tax, estimated_value, currency, updated_at
            FROM public.kb_tenders
            WHERE {' AND '.join(clauses)}
            ORDER BY updated_at DESC NULLS LAST
            LIMIT 40
            """,
            tuple(params),
        )
    except Exception:
        return []


def get_pcsp(tender_id: str) -> dict[str, Any] | None:
    if not _available("kb_tenders"):
        return None
    try:
        return db.fetch_one(
            "SELECT * FROM public.kb_tenders WHERE id = %s OR expediente = %s OR atom_id = %s LIMIT 1",
            (tender_id, tender_id, tender_id),
        )
    except Exception:
        return None


def pcsp_execution_fragments(tender_id: str) -> list[dict[str, Any]]:
    if not _available("kb_chunks"):
        return []
    try:
        return db.fetch_all(
            """
            SELECT c.id, c.document_id, c.document_type, c.title, c.chunk_text, c.source_url, c.heading_path, c.page_start
            FROM public.kb_chunks c
            WHERE c.tender_id = %s
              AND (
                c.chunk_text ILIKE '%ejecuci%%' OR c.chunk_text ILIKE '%plazo%%'
                OR c.chunk_text ILIKE '%pr%%rroga%%' OR c.chunk_text ILIKE '%garant%%'
                OR c.chunk_text ILIKE '%penal%%' OR c.chunk_text ILIKE '%recepci%%'
                OR c.chunk_text ILIKE '%liquidaci%%' OR c.chunk_text ILIKE '%entreg%%'
                OR c.chunk_text ILIKE '%factur%%' OR c.chunk_text ILIKE '%nivel de servicio%%'
              )
            ORDER BY c.publication_date DESC NULLS LAST, c.id
            LIMIT 80
            """,
            (tender_id,),
        )
    except Exception:
        return []


def xreview_candidates(tenant_id: str, query: str | None = None) -> list[dict[str, Any]]:
    """List only immutable, published award packages belonging to the caller tenant."""
    if not _relation_available("xreview.award_handoffs"):
        return []
    clauses = ["tenant_id = %s", "status = 'published'", "coalesce((data->>'immutable')::boolean, false) = true"]
    params: list[Any] = [tenant_id]
    if query:
        clauses.append("(coalesce(data#>>'{procedure,title}', '') ILIKE %s OR coalesce(data#>>'{procedure,file_number}', '') ILIKE %s OR coalesce(data#>>'{lot,title}', '') ILIKE %s)")
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    try:
        return db.fetch_all(
            f"""
            SELECT id, procedure_id, parent_id AS lot_id, status, data, created_at
            FROM xreview.award_handoffs
            WHERE {' AND '.join(clauses)}
            ORDER BY created_at DESC
            LIMIT 80
            """,
            tuple(params),
        )
    except Exception:
        return []


def get_xreview_handoff(tenant_id: str, handoff_id: str) -> dict[str, Any] | None:
    if not _relation_available("xreview.award_handoffs"):
        return None
    try:
        return db.fetch_one(
            """
            SELECT id, procedure_id, parent_id AS lot_id, status, data, created_at
            FROM xreview.award_handoffs
            WHERE tenant_id = %s AND id = %s AND status = 'published'
              AND coalesce((data->>'immutable')::boolean, false) = true
            """,
            (tenant_id, handoff_id),
        )
    except Exception:
        return None
