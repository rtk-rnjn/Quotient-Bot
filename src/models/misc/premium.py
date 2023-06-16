from models import BaseDbModel
from datetime import timedelta
from tortoise import fields
import os

__all__ = ("PremiumTxn", "PremiumPlan")


class PremiumPlan(BaseDbModel):
    class Meta:
        table = "premium_plans"

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50)
    description = fields.CharField(max_length=250, null=True)
    price = fields.IntField()
    duration = fields.TimeDeltaField()

    @staticmethod
    async def insert_plans():
        await PremiumPlan.all().delete()
        await PremiumPlan.create(name="Trial (7d)", description="Duration: 7 days", price=29, duration=timedelta(days=7))
        await PremiumPlan.create(
            name="Basic (1m)", description="Duration: 28 days", price=79, duration=timedelta(days=28)
        )
        await PremiumPlan.create(
            name="Professional (3m)", description="Duration: 84 days", price=229, duration=timedelta(days=84)
        )
        await PremiumPlan.create(
            name="Enterprise (6m)", description="Duration: 168 days", price=469, duration=timedelta(days=168)
        )
        await PremiumPlan.create(
            name="GodLike (Lifetime)", description="Duration: 69 years", price=4999, duration=timedelta(days=25185)
        )


class PremiumTxn(BaseDbModel):
    class Meta:
        table = "premium_txns"

    id = fields.IntField(pk=True)
    txnid = fields.CharField(max_length=100)
    user_id = fields.BigIntField()
    guild_id = fields.BigIntField()
    plan_id = fields.IntField()

    created_at = fields.DatetimeField(auto_now=True)
    completed_at = fields.DatetimeField(null=True)
    raw_data = fields.JSONField(default=dict)

    @staticmethod
    async def gen_txnid() -> str:
        txnid = None

        while txnid is None:
            _id = f"QP_{os.urandom(16).hex()}"
            if not await PremiumTxn.filter(txnid=_id).exists():
                txnid = _id

        return txnid
