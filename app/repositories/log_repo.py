from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.models import AuditLog, UsageLog


class LogRepository:
    """จัดการการบันทึกและดึงข้อมูลจากตาราง usage_logs และ audit_logs"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_usage_log(
        self,
        request_id: str,
        provider_name: str,
        model_name: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
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
            latency_ms=latency_ms,
            status_code=status_code,
            error_message=error_message,
        )
        self.db.add(log_entry)
        await self.db.commit()
        await self.db.refresh(log_entry)
        return log_entry

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