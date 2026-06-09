"""
Supabase Database Service for AI Lead Generator.

Provides async CRUD operations for leads and outreach records.
Wraps the sync Supabase client with asyncio for non-blocking database access.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from supabase import create_client, Client
from postgrest.exceptions import APIError

from config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        logger.info("SupabaseService initialized successfully")

    def _get_client_for_user(self, access_token: Optional[str] = None) -> Client:
        if access_token:
            client = create_client(settings.supabase_url, settings.supabase_key)
            client.auth.set_session(access_token=access_token, refresh_token="")
            return client
        return self.client

    # ─── Lead Operations ───────────────────────────────────────────────────────

    async def create_lead(
        self,
        lead_data: Dict[str, Any],
        user_id: str,
        access_token: str
    ) -> Dict[str, Any]:
        try:
            business_name = lead_data.get('business_name') or "Unknown Business"
            logger.info(f"Creating lead for business: {business_name} (User: {user_id})")

            lead_data['user_id'] = user_id

            serialized_data = {
                k: v.isoformat() if isinstance(v, datetime) else v
                for k, v in lead_data.items()
            }

            client = self._get_client_for_user(access_token)
            result = await asyncio.to_thread(
                lambda: client.table("leads").insert(serialized_data).execute()
            )

            if not result.data:
                raise APIError({"message": "No data returned after creating lead", "code": "NO_DATA"})

            logger.info(f"Lead created successfully: {result.data[0]['id']}")
            return result.data[0]
        except APIError as e:
            logger.error(f"Failed to create lead: {e}")
            raise

    async def get_lead(
        self,
        lead_id: str,
        user_id: str,
        access_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Fetching lead: {lead_id} (User: {user_id})")
            client = self._get_client_for_user(access_token)
            result = await asyncio.to_thread(
                lambda: client.table("leads")
                .select("*")
                .eq("id", lead_id)
                .eq("user_id", user_id)
                .execute()
            )
            if result.data:
                logger.info(f"Lead found: {lead_id}")
                return result.data[0]
            logger.warning(f"Lead not found or access denied: {lead_id}")
            return None
        except APIError as e:
            logger.error(f"Failed to get lead {lead_id}: {e}")
            return None

    async def get_leads(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            logger.info(f"Fetching leads for user {user_id}: limit={limit}, offset={offset}, filters={filters}")

            client = self._get_client_for_user(access_token)
            query = client.table("leads").select("*").eq("user_id", user_id)

            if filters:
                if "city" in filters:
                    query = query.eq("city", filters["city"])
                if "min_score" in filters:
                    query = query.gte("opportunity_score", filters["min_score"])
                if "max_score" in filters:
                    query = query.lte("opportunity_score", filters["max_score"])

            query = query.range(offset, offset + limit - 1)
            result = await asyncio.to_thread(lambda: query.execute())
            logger.info(f"Retrieved {len(result.data)} leads")
            return result.data
        except APIError as e:
            logger.error(f"Failed to get leads: {e}")
            return []

    async def update_lead(
        self,
        lead_id: str,
        updates: Dict[str, Any],
        user_id: str,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Updating lead {lead_id} for user {user_id}: {updates}")
            client = self._get_client_for_user(access_token)
            result = await asyncio.to_thread(
                lambda: client.table("leads")
                .update(updates)
                .eq("id", lead_id)
                .eq("user_id", user_id)
                .execute()
            )
            if result.data:
                logger.info(f"Lead updated successfully: {lead_id}")
                return result.data[0]
            raise APIError({"message": f"Lead not found or access denied: {lead_id}", "code": "NOT_FOUND"})
        except APIError as e:
            logger.error(f"Failed to update lead {lead_id}: {e}")
            raise

    async def delete_lead(
        self,
        lead_id: str,
        user_id: str,
        access_token: Optional[str] = None
    ) -> bool:
        try:
            logger.info(f"Deleting lead: {lead_id} (User: {user_id})")
            client = self._get_client_for_user(access_token)
            result = await asyncio.to_thread(
                lambda: client.table("leads")
                .delete()
                .eq("id", lead_id)
                .eq("user_id", user_id)
                .execute()
            )
            if result.data:
                logger.info(f"Lead deleted successfully: {lead_id}")
                return True
            logger.warning(f"Lead not found or access denied for deletion: {lead_id}")
            return False
        except APIError as e:
            logger.error(f"Failed to delete lead {lead_id}: {e}")
            return False

    # ─── Outreach Operations ───────────────────────────────────────────────────

    async def create_outreach(
        self,
        outreach_data: Dict[str, Any],
        user_id: str,
        access_token: str
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Creating outreach for user {user_id}, lead: {outreach_data.get('lead_id', 'N/A')}")

            outreach_data['user_id'] = user_id

            serialized_data = {
                k: v.isoformat() if isinstance(v, datetime) else v
                for k, v in outreach_data.items()
            }

            client = self._get_client_for_user(access_token)
            result = await asyncio.to_thread(
                lambda: client.table("outreach").insert(serialized_data).execute()
            )

            if not result.data:
                raise APIError({"message": "No data returned after creating outreach", "code": "NO_DATA"})

            logger.info(f"Outreach created successfully: {result.data[0]['id']}")
            return result.data[0]
        except APIError as e:
            logger.error(f"Failed to create outreach: {e}")
            raise

    async def get_outreach_by_id(
        self,
        outreach_id: str,
        user_id: str,
        access_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Fetching outreach {outreach_id} for user {user_id}")
            client = self._get_client_for_user(access_token)
            result = await asyncio.to_thread(
                lambda: client.table("outreach")
                .select("*")
                .eq("id", outreach_id)
                .eq("user_id", user_id)
                .execute()
            )
            if result.data:
                return result.data[0]
            return None
        except APIError as e:
            logger.error(f"Failed to get outreach {outreach_id}: {e}")
            return None

    async def get_outreach_by_lead(
        self,
        lead_id: str,
        user_id: str,
        access_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Fetching outreach for lead {lead_id} (User: {user_id})")
            client = self._get_client_for_user(access_token)
            result = await asyncio.to_thread(
                lambda: client.table("outreach")
                .select("*")
                .eq("lead_id", lead_id)
                .eq("user_id", user_id)
                .execute()
            )
            if result.data:
                return result.data[0]
            return None
        except APIError as e:
            logger.error(f"Failed to get outreach for lead {lead_id}: {e}")
            return None

    async def update_outreach(
        self,
        outreach_id: str,
        updates: Dict[str, Any],
        user_id: str,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Updating outreach {outreach_id} for user {user_id}: {updates}")
            client = self._get_client_for_user(access_token)
            result = await asyncio.to_thread(
                lambda: client.table("outreach")
                .update(updates)
                .eq("id", outreach_id)
                .eq("user_id", user_id)
                .execute()
            )
            if result.data:
                logger.info(f"Outreach updated successfully: {outreach_id}")
                return result.data[0]
            raise APIError({"message": f"Outreach not found or access denied: {outreach_id}", "code": "NOT_FOUND"})
        except APIError as e:
            logger.error(f"Failed to update outreach {outreach_id}: {e}")
            raise

    async def mark_outreach_sent(
        self,
        outreach_id: str,
        user_id: str,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        updates = {
            "sent": True,
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
        return await self.update_outreach(outreach_id, updates, user_id=user_id, access_token=access_token)

    # ─── Query Operations ──────────────────────────────────────────────────────

    async def get_leads_by_score(
        self,
        min_score: int,
        max_score: int = 10
    ) -> List[Dict[str, Any]]:
        try:
            logger.info(f"Fetching leads with score {min_score}-{max_score}")
            result = await asyncio.to_thread(
                lambda: self.client.table("leads")
                .select("*")
                .gte("opportunity_score", min_score)
                .lte("opportunity_score", max_score)
                .execute()
            )
            logger.info(f"Found {len(result.data)} leads in score range")
            return result.data
        except APIError as e:
            logger.error(f"Failed to get leads by score: {e}")
            return []

    async def get_leads_by_city(self, city: str) -> List[Dict[str, Any]]:
        try:
            logger.info(f"Fetching leads in city: {city}")
            result = await asyncio.to_thread(
                lambda: self.client.table("leads").select("*").eq("city", city).execute()
            )
            logger.info(f"Found {len(result.data)} leads in {city}")
            return result.data
        except APIError as e:
            logger.error(f"Failed to get leads by city: {e}")
            return []

    async def count_leads(self) -> int:
        try:
            logger.info("Counting total leads")
            result = await asyncio.to_thread(
                lambda: self.client.table("leads").select("*", count="exact").execute()
            )
            count = result.count or 0
            logger.info(f"Total leads: {count}")
            return count
        except APIError as e:
            logger.error(f"Failed to count leads: {e}")
            return 0

    async def get_average_score(self) -> float:
        try:
            logger.info("Calculating average opportunity score")
            result = await asyncio.to_thread(
                lambda: self.client.table("leads").select("opportunity_score").execute()
            )
            if not result.data:
                return 0.0
            scores = [lead["opportunity_score"] for lead in result.data if lead.get("opportunity_score")]
            avg = sum(scores) / len(scores) if scores else 0.0
            logger.info(f"Average score: {avg:.2f}")
            return avg
        except APIError as e:
            logger.error(f"Failed to calculate average score: {e}")
            return 0.0