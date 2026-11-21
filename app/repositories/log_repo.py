from typing import Optional
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.models import AuditLog, UsageLog, ApiKey


class LogRepository:
    """จัดการการบันทึกและดึงข้อมูลจากตาราง usage_logs และ audit_logs"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_usage_logs(self, limit: int = 100) -> list[UsageLog]:
        result = await self.db.execute(
            select(UsageLog)
            .order_by(UsageLog.created_at.desc(), UsageLog.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_usage_summary(self) -> dict:
        result = await self.db.execute(
            select(
                func.count(UsageLog.id),
                func.count(UsageLog.id).filter(UsageLog.status_code.between(200, 399)),
                func.count(UsageLog.id).filter(UsageLog.status_code >= 400),
                func.coalesce(func.sum(UsageLog.total_tokens), 0),
                func.coalesce(func.sum(UsageLog.cost_usd), 0.0),
                func.coalesce(func.avg(UsageLog.latency_ms), 0.0),
            )
        )
        row = result.one()
        return {
            "total_requests": int(row[0] or 0),
            "successful_requests": int(row[1] or 0),
            "failed_requests": int(row[2] or 0),
            "total_tokens": int(row[3] or 0),
            "total_cost_usd": float(row[4] or 0.0),
            "average_latency_ms": float(row[5] or 0.0),
        }

    async def list_audit_logs(self, limit: int = 100) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_usage_log(
        self,
        request_id: str,
        provider_name: str,
        model_name: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
        cost_usd: float = 0.0,
        status_code: int = 200,
        error_message: Optional[str] = None,
        api_key_id: Optional[int] = None,
    ) -> UsageLog:
        """บันทึกประวัติการเรียกใช้งาน AI ลงตาราง usage_logs"""
        log_entry = UsageLog(
            request_id=request_id,
            api_key_id=api_key_id,
            provider_name=provider_name,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            status_code=status_code,
            error_message=error_message,
        )
        self.db.add(log_entry)
        await self.db.commit()
        await self.db.refresh(log_entry)
        return log_entry

    async def increment_api_key_spend(self, api_key_id: int, cost_usd: float) -> None:
        """บวกยอดค่าใช้จ่ายสะสมเข้า api_keys แบบ Atomic ป้องกันตัวเลขเพี้ยนเวลายิงพร้อมกัน"""
        if cost_usd <= 0:
            return
        stmt = (
            update(ApiKey)
            .where(ApiKey.id == api_key_id)
            .values(current_spend_usd=ApiKey.current_spend_usd + cost_usd)
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def create_audit_log(
        self,
        action: str,
        target_resource: str,
        admin_user_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """บันทึกประวัติการกระทำของแอดมินลงตาราง audit_logs"""
        audit_entry = AuditLog(
            admin_user_id=admin_user_id,
            action=action,
            target_resource=target_resource,
            details=details,
            ip_address=ip_address,
        )
        self.db.add(audit_entry)
        await self.db.commit()
        await self.db.refresh(audit_entry)
        return audit_entry