"""Norm rule pack HITL event and version listing routes."""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from aerobim.core.di.tokens import Tokens
from aerobim.domain.object_acl import AuthPrincipal, principal_may_edit_norm_pack
from aerobim.presentation.http.context import ApiContext
from aerobim.presentation.http.errors import public_bad_request_detail
from aerobim.presentation.http.schemas import NormRuleHitlEventRequest


def build_norm_packs_router(ctx: ApiContext) -> APIRouter:
    router = APIRouter()
    settings = ctx.settings

    @router.post("/v1/norm-packs/{pack_id}/rule-events")
    def post_norm_rule_hitl_event(
        pack_id: str,
        payload: NormRuleHitlEventRequest,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        if not pack_id.strip() or len(pack_id) > 128:
            raise HTTPException(status_code=400, detail="Invalid pack_id")
        if not principal_may_edit_norm_pack(
            enforce_rbac=settings.enforce_norm_pack_rbac,
            principal=principal,
        ):
            raise HTTPException(
                status_code=403,
                detail="Norm-pack edits require editor/reviewer OIDC role",
            )
        tenant_id = ctx.resolve_bound_tenant(principal)
        ctx.assert_norm_pack_access(principal, tenant_id=tenant_id)
        if payload.report_id:
            ctx.load_authorized_report(payload.report_id, principal)
        subject = (principal.subject or "").strip()
        proposed_by = subject or "lab:anonymous"
        if payload.target_approval_status == "customer_approved":
            if not subject or subject in {"anonymous-dev", "api-bearer"}:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "customer_approved requires an authenticated human subject "
                        "(OIDC sub); anonymous-dev/api-bearer are not allowed"
                    ),
                )
        use_case = ctx.container.resolve(Tokens.APPLY_NORM_RULE_HITL_EVENT_USE_CASE)
        base_path = ctx.resolve_safe_path(payload.base_pack_path, principal=principal)
        try:
            record, event = use_case.execute(
                pack_id=pack_id,
                base_pack_path=base_path,
                event_type=payload.event_type,
                rule_diff=payload.rule_diff,
                proposed_by=proposed_by,
                target_approval_status=payload.target_approval_status,
                approval_ref=payload.approval_ref,
                report_id=payload.report_id,
                tenant_id=tenant_id,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=public_bad_request_detail(),
            ) from exc
        return {"version": asdict(record), "event": asdict(event)}

    @router.get("/v1/norm-packs/{pack_id}/versions")
    def list_norm_pack_versions(
        pack_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        if not pack_id.strip() or len(pack_id) > 128:
            raise HTTPException(status_code=400, detail="Invalid pack_id")
        tenant_id = ctx.resolve_bound_tenant(principal)
        ctx.assert_norm_pack_access(principal, tenant_id=tenant_id)
        store = ctx.container.resolve(Tokens.NORM_RULE_PACK_VERSION_STORE)
        versions = store.list_versions(pack_id, tenant_id=tenant_id)
        return {"pack_id": pack_id, "versions": [asdict(item) for item in versions]}

    return router
