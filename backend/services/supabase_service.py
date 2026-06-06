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

from ..config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SupabaseService:
    """
    Async wrapper for Supabase database operations.

    Manages leads and outreach records with full CRUD functionality,
    filtering, and aggregation queries.
    """

    def __init__(self):
        """Initialize Supabase client with credentials from config."""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        logger.info("SupabaseService initialized successfully")

    # Lead Operations

    async def create_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a new lead into the database.

        Args:
            lead_data: Dictionary containing lead fields (name, email, company, etc.)

        Returns:
            Created lead record with generated ID and timestamps

        Raises:
            APIError: If database insertion fails
        """
        try:
            logger.info(f"Creating lead: {lead_data.get('email', 'N/A')}")
            
            # Convert datetime objects to ISO strings for JSON serialization
            serialized_data = {
                k: v.isoformat() if isinstance(v, datetime) else v
                for k, v in lead_data.items()
            }
            
            result = await asyncio.to_thread(
                lambda: self.client.table("leads").insert(serialized_data).execute()
            )
            
            if not result.data:
                raise APIError({"message": "No data returned after creating lead", "code": "NO_DATA"})
                
            logger.info(f"Lead created successfully: {result.data[0]['id']}")
            return result.data[0]
        except APIError as e:
            logger.error(f"Failed to create lead: {e}")
            raise

    async def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single lead by ID.

        Args:
            lead_id: UUID of the lead

        Returns:
            Lead record or None if not found
        """
        try:
            logger.info(f"Fetching lead: {lead_id}")
            result = await asyncio.to_thread(
                lambda: self.client.table("leads").select("*").eq("id", lead_id).execute()
            )
            if result.data:
                logger.info(f"Lead found: {lead_id}")
                return result.data[0]
            logger.warning(f"Lead not found: {lead_id}")
            return None
        except APIError as e:
            logger.error(f"Failed to get lead {lead_id}: {e}")
            return None

    async def get_leads(
        self,
        limit: int = 50,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get paginated list of leads with optional filters.

        Args:
            limit: Maximum number of records to return (default 50)
            offset: Number of records to skip (default 0)
            filters: Optional filters (city, min_score, max_score)

        Returns:
            List of lead records
        """
        try:
            logger.info(f"Fetching leads: limit={limit}, offset={offset}, filters={filters}")

            query = self.client.table("leads").select("*")

            # Apply filters if provided
            if filters:
                if "city" in filters:
                    query = query.eq("city", filters["city"])
                if "min_score" in filters:
                    query = query.gte("opportunity_score", filters["min_score"])
                if "max_score" in filters:
                    query = query.lte("opportunity_score", filters["max_score"])

            # Apply pagination
            query = query.range(offset, offset + limit - 1)

            result = await asyncio.to_thread(lambda: query.execute())
            logger.info(f"Retrieved {len(result.data)} leads")
            return result.data
        except APIError as e:
            logger.error(f"Failed to get leads: {e}")
            return []

    async def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update lead fields.

        Args:
            lead_id: UUID of the lead
            updates: Dictionary of fields to update

        Returns:
            Updated lead record

        Raises:
            APIError: If update fails or lead not found
        """
        try:
            logger.info(f"Updating lead {lead_id}: {updates}")
            result = await asyncio.to_thread(
                lambda: self.client.table("leads").update(updates).eq("id", lead_id).execute()
            )
            if result.data:
                logger.info(f"Lead updated successfully: {lead_id}")
                return result.data[0]
            raise APIError(f"Lead not found: {lead_id}")
        except APIError as e:
            logger.error(f"Failed to update lead {lead_id}: {e}")
            raise

    async def delete_lead(self, lead_id: str) -> bool:
        """
        Delete a lead (cascades to outreach records).

        Args:
            lead_id: UUID of the lead

        Returns:
            True if deleted, False if not found
        """
        try:
            logger.info(f"Deleting lead: {lead_id}")
            result = await asyncio.to_thread(
                lambda: self.client.table("leads").delete().eq("id", lead_id).execute()
            )
            if result.data:
                logger.info(f"Lead deleted successfully: {lead_id}")
                return True
            logger.warning(f"Lead not found for deletion: {lead_id}")
            return False
        except APIError as e:
            logger.error(f"Failed to delete lead {lead_id}: {e}")
            return False

    # Outreach Operations

    async def create_outreach(self, outreach_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a new outreach record.

        Args:
            outreach_data: Dictionary with lead_id, template, and message fields

        Returns:
            Created outreach record

        Raises:
            APIError: If insertion fails
        """
        try:
            logger.info(f"Creating outreach for lead: {outreach_data.get('lead_id', 'N/A')}")
            logger.debug(f"Outreach payload: {outreach_data}")
            
            # Convert datetime objects to ISO strings for JSON serialization
            serialized_data = {
                k: v.isoformat() if isinstance(v, datetime) else v
                for k, v in outreach_data.items()
            }
            
            result = await asyncio.to_thread(
                lambda: self.client.table("outreach").insert(serialized_data).execute()
            )
            
            logger.debug(f"Supabase response for create_outreach: {result}")
            if not result.data:
                # If result.data is empty, it might mean the insert failed without raising an APIError
                logger.error(f"Insert outreach returned no data. Result: {result}")
                raise APIError({"message": "No data returned after creating outreach", "code": "NO_DATA"})
            
            logger.info(f"Outreach created successfully: {result.data[0]['id']}")
            return result.data[0]
        except APIError as e:
            logger.error(f"Failed to create outreach: {e}")
            raise

    async def get_outreach_by_id(self, outreach_id: str) -> Optional[Dict[str, Any]]:
        """
        Get outreach record by outreach ID.

        Args:
            outreach_id: UUID of the outreach record

        Returns:
            Outreach record or None if not found
        """
        try:
            logger.info(f"Fetching outreach by ID: {outreach_id}")
            result = await asyncio.to_thread(
                lambda: self.client.table("outreach").select("*").eq("id", outreach_id).execute()
            )
            if result.data:
                logger.info(f"Outreach found: {outreach_id}")
                return result.data[0]
            logger.warning(f"Outreach not found: {outreach_id}")
            return None
        except APIError as e:
            logger.error(f"Failed to get outreach {outreach_id}: {e}")
            return None

    async def get_outreach_by_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Get outreach record for a specific lead.

        Args:
            lead_id: UUID of the lead

        Returns:
            Outreach record or None if not found
        """
        try:
            logger.info(f"Fetching outreach for lead: {lead_id}")
            result = await asyncio.to_thread(
                lambda: self.client.table("outreach").select("*").eq("lead_id", lead_id).execute()
            )
            logger.debug(f"Supabase response for outreach lead {lead_id}: {result.data}")
            if result.data:
                logger.info(f"Outreach found for lead: {lead_id}")
                return result.data[0]
            logger.warning(f"No outreach found for lead: {lead_id}")
            return None
        except APIError as e:
            logger.error(f"Failed to get outreach for lead {lead_id}: {e}")
            return None

    async def update_outreach(self, outreach_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update outreach record fields.

        Args:
            outreach_id: UUID of the outreach record
            updates: Dictionary of fields to update

        Returns:
            Updated outreach record

        Raises:
            APIError: If update fails
        """
        try:
            logger.info(f"Updating outreach {outreach_id}: {updates}")
            result = await asyncio.to_thread(
                lambda: self.client.table("outreach").update(updates).eq("id", outreach_id).execute()
            )
            if result.data:
                logger.info(f"Outreach updated successfully: {outreach_id}")
                return result.data[0]
            raise APIError(f"Outreach not found: {outreach_id}")
        except APIError as e:
            logger.error(f"Failed to update outreach {outreach_id}: {e}")
            raise

    async def mark_outreach_sent(self, outreach_id: str) -> Dict[str, Any]:
        """
        Mark outreach as sent with current timestamp.

        Args:
            outreach_id: UUID of the outreach record

        Returns:
            Updated outreach record with sent=True and sent_at timestamp
        """
        updates = {
            "sent": True,
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
        return await self.update_outreach(outreach_id, updates)

    # Query Operations

    async def get_leads_by_score(
        self,
        min_score: int,
        max_score: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Filter leads by opportunity score range.

        Args:
            min_score: Minimum score (inclusive)
            max_score: Maximum score (inclusive, default 10)

        Returns:
            List of leads within score range
        """
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
        """
        Filter leads by city.

        Args:
            city: City name (exact match)

        Returns:
            List of leads in the specified city
        """
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
        """
        Get total count of leads in database.

        Returns:
            Total number of leads
        """
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
        """
        Calculate average opportunity score across all leads.

        Returns:
            Average score (0.0 if no leads)
        """
        try:
            logger.info("Calculating average opportunity score")
            result = await asyncio.to_thread(
                lambda: self.client.table("leads").select("opportunity_score").execute()
            )
            if not result.data:
                logger.info("No leads found for average calculation")
                return 0.0

            scores = [lead["opportunity_score"] for lead in result.data if lead.get("opportunity_score")]
            avg = sum(scores) / len(scores) if scores else 0.0
            logger.info(f"Average score: {avg:.2f}")
            return avg
        except APIError as e:
            logger.error(f"Failed to calculate average score: {e}")
            return 0.0
