# ============================================================
# SUPERVISOR AGENT
# ============================================================

import asyncio
import re

from event_manager import event_manager
from planner import plan_trip
from research_agent import research_trip
from budget_agent import budget_trip
from itinerary_agent import itinerary_trip


class TripSupervisor:

    def __init__(self):
        self.status = []

    # ========================================================
    # ACTIVITY TRACKING
    # ========================================================

    def reset_status(self):

        self.status = [
            {
                "agent": "Supervisor Agent",
                "status": "completed",
                "message": "Travel request received."
            },
            {
                "agent": "Planner Agent",
                "status": "pending",
                "message": "Waiting to analyze travel requirements."
            },
            {
                "agent": "Research Agent",
                "status": "pending",
                "message": "Waiting for trip requirements."
            },
            {
                "agent": "Budget Agent",
                "status": "pending",
                "message": "Waiting for destination research."
            },
            {
                "agent": "Itinerary Agent",
                "status": "pending",
                "message": "Waiting for budget analysis."
            },
            {
                "agent": "Validation",
                "status": "pending",
                "message": "Waiting for itinerary."
            }
        ]

    def update_status(
        self,
        agent_name: str,
        status: str,
        message: str
    ):

        for item in self.status:

            if item["agent"] == agent_name:

                item["status"] = status
                item["message"] = message

                return

    async def publish_completion(
        self,
        request_id: str,
        agent: str,
        message: str,
    ):

        await event_manager.publish(
            request_id,
            {
                "type": "complete",
                "agent": agent,
                "message": message,
            },
        )

    # ========================================================
    # EXTRACT REQUESTED DAYS
    # ========================================================

    def extract_trip_days(self, trip_data: dict) -> int:

        duration = str(
            trip_data.get("duration", "")
        ).strip().lower()

        if not duration:
            return 0

        match = re.search(
            r"(\d+)\s*(?:-|\s)?\s*day",
            duration
        )

        if match:
            return int(match.group(1))

        match = re.search(
            r"\d+",
            duration
        )

        if match:
            return int(match.group())

        return 0

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_trip(
        self,
        trip_data: dict,
        budget_data: dict,
        itinerary_data: dict
    ) -> dict:

        issues = []

        # ----------------------------------------------------
        # Duration
        # ----------------------------------------------------

        requested_days = self.extract_trip_days(
            trip_data
        )

        if requested_days <= 0:

            issues.append(
                "Trip duration could not be determined."
            )

        # ----------------------------------------------------
        # Itinerary
        # ----------------------------------------------------

        days = itinerary_data.get(
            "days",
            []
        )

        if not isinstance(days, list):

            issues.append(
                "Itinerary days must be a list."
            )

        else:

            if len(days) == 0:

                issues.append(
                    "No day-by-day itinerary was generated."
                )

            elif requested_days > 0 and len(days) != requested_days:

                issues.append(
                    f"Requested {requested_days} days, "
                    f"but the itinerary contains {len(days)} days."
                )

            # -----------------------------------------------
            # Verify sequential day numbers
            # -----------------------------------------------

            if requested_days > 0 and len(days) == requested_days:

                expected_days = list(
                    range(
                        1,
                        requested_days + 1
                    )
                )

                actual_days = []

                for item in days:

                    try:

                        actual_days.append(
                            int(item.get("day"))
                        )

                    except (
                        TypeError,
                        ValueError
                    ):

                        issues.append(
                            "Itinerary contains an invalid day number."
                        )

                        break

                if actual_days != expected_days:

                    issues.append(
                        "Itinerary day numbers are not sequential."
                    )

        # ----------------------------------------------------
        # Budget
        # ----------------------------------------------------

        budget_status = budget_data.get(
            "status",
            "BUDGET_NOT_SPECIFIED"
        )

        if budget_status == "OVER_BUDGET":

            issues.append(
                "The estimated trip cost exceeds "
                "the stated budget."
            )

        # ----------------------------------------------------
        # Final validation
        # ----------------------------------------------------

        if issues:

            validation_status = "NEEDS_REVIEW"

            message = (
                "Trip plan was generated but requires review."
            )

        else:

            validation_status = "VALID"

            message = (
                "Trip plan passed validation."
            )

        return {
            "status": validation_status,
            "issues": issues,
            "message": message
        }

    # ========================================================
    # MAIN WORKFLOW
    # ========================================================

    async def run(
        self,
        user_request: str,
        request_id: str,
    ) -> dict:

        await event_manager.publish(
            request_id,
            {
                "type": "agent_started",
                "agent": "Supervisor Agent",
                "message": "Understanding your travel requirements",
            },
        )

        self.reset_status()

        if not user_request or not user_request.strip():

            await self.publish_completion(
                request_id,
                "Supervisor Agent",
                "Travel request cannot be empty.",
            )

            return {
                "success": False,
                "error": "Travel request cannot be empty.",
                "agent_activity": self.status
            }

        # ====================================================
        # PLANNER
        # ====================================================

        self.update_status(
            "Planner Agent",
            "running",
            "Understanding your travel requirements..."
        )

        await event_manager.publish(
            request_id,
            {
                "type": "agent_started",
                "agent": "Planner Agent",
                "message": "Creating your personalized travel strategy",
            },
        )

        try:

            trip_data = await asyncio.to_thread(
                plan_trip,
                user_request.strip()
            )

            self.update_status(
                "Planner Agent",
                "completed",
                "Travel requirements successfully understood."
            )

            await event_manager.publish(
                request_id,
                {
                    "type": "agent_completed",
                    "agent": "Planner Agent",
                    "message": "Travel requirements understood",
                },
            )

        except Exception as error:

            self.update_status(
                "Planner Agent",
                "failed",
                "Unable to understand the travel request."
            )

            await self.publish_completion(
                request_id,
                "Planner Agent",
                "Trip planning failed during the planner stage.",
            )

            return {
                "success": False,
                "error": str(error),
                "failed_stage": "Planner Agent",
                "agent_activity": self.status
            }

        # ====================================================
        # RESEARCH
        # ====================================================

        self.update_status(
            "Research Agent",
            "running",
            "Researching destinations, attractions and activities..."
        )

        await event_manager.publish(
            request_id,
            {
                "type": "agent_started",
                "agent": "Research Agent",
                "message": "Researching destinations, activities and food",
            },
        )

        try:

            research_data = await asyncio.to_thread(
                research_trip,
                trip_data
            )

            self.update_status(
                "Research Agent",
                "completed",
                "Destination research completed."
            )

            await event_manager.publish(
                request_id,
                {
                    "type": "agent_completed",
                    "agent": "Research Agent",
                    "message": "Destination research completed",
                },
            )

        except Exception as error:

            self.update_status(
                "Research Agent",
                "failed",
                "Destination research could not be completed."
            )

            await self.publish_completion(
                request_id,
                "Research Agent",
                "Trip planning failed during destination research.",
            )

            return {
                "success": False,
                "error": str(error),
                "failed_stage": "Research Agent",
                "trip": trip_data,
                "agent_activity": self.status
            }

        # ====================================================
        # BUDGET
        # ====================================================

        self.update_status(
            "Budget Agent",
            "running",
            "Calculating the estimated trip budget..."
        )

        await event_manager.publish(
            request_id,
            {
                "type": "agent_started",
                "agent": "Budget Agent",
                "message": "Analyzing your travel budget",
            },
        )

        try:

            budget_data = await asyncio.to_thread(
                budget_trip,
                trip_data,
                research_data
            )

            self.update_status(
                "Budget Agent",
                "completed",
                "Budget analysis completed."
            )

            await event_manager.publish(
                request_id,
                {
                    "type": "agent_completed",
                    "agent": "Budget Agent",
                    "message": "Budget analysis completed",
                },
            )

        except Exception as error:

            self.update_status(
                "Budget Agent",
                "failed",
                "Budget analysis could not be completed."
            )

            await self.publish_completion(
                request_id,
                "Budget Agent",
                "Trip planning failed during budget analysis.",
            )

            return {
                "success": False,
                "error": str(error),
                "failed_stage": "Budget Agent",
                "trip": trip_data,
                "research": research_data,
                "agent_activity": self.status
            }

        # ====================================================
        # ITINERARY
        # ====================================================

        self.update_status(
            "Itinerary Agent",
            "running",
            "Creating your complete day-by-day itinerary..."
        )

        await event_manager.publish(
            request_id,
            {
                "type": "agent_started",
                "agent": "Itinerary Agent",
                "message": "Building your day-by-day itinerary",
            },
        )

        try:

            itinerary_data = await asyncio.to_thread(
                itinerary_trip,
                trip_data,
                research_data,
                budget_data
            )

            self.update_status(
                "Itinerary Agent",
                "completed",
                "Complete itinerary created."
            )

            await event_manager.publish(
                request_id,
                {
                    "type": "agent_completed",
                    "agent": "Itinerary Agent",
                    "message": "Personalized itinerary created",
                },
            )

        except Exception as error:

            self.update_status(
                "Itinerary Agent",
                "failed",
                "Complete itinerary could not be generated."
            )

            await self.publish_completion(
                request_id,
                "Itinerary Agent",
                "Trip planning failed during itinerary generation.",
            )

            return {
                "success": False,
                "error": str(error),
                "failed_stage": "Itinerary Agent",
                "trip": trip_data,
                "research": research_data,
                "budget": budget_data,
                "agent_activity": self.status
            }

        # ====================================================
        # VALIDATION
        # ====================================================

        self.update_status(
            "Validation",
            "running",
            "Checking duration, itinerary and budget consistency..."
        )

        await event_manager.publish(
            request_id,
            {
                "type": "agent_started",
                "agent": "Validation",
                "message": "Checking your final travel plan",
            },
        )

        try:

            validation = await asyncio.to_thread(
                self.validate_trip,
                trip_data,
                budget_data,
                itinerary_data
            )

            if validation["status"] == "VALID":

                self.update_status(
                    "Validation",
                    "completed",
                    "Travel plan validation completed successfully."
                )

            else:

                self.update_status(
                    "Validation",
                    "completed",
                    "Travel plan requires review."
                )

            await event_manager.publish(
                request_id,
                {
                    "type": "agent_completed",
                    "agent": "Validation",
                    "message": "Travel plan validation completed",
                },
            )

        except Exception as error:

            self.update_status(
                "Validation",
                "failed",
                "Travel plan validation failed."
            )

            await self.publish_completion(
                request_id,
                "Validation",
                "Trip planning failed during final validation.",
            )

            return {
                "success": False,
                "error": str(error),
                "failed_stage": "Validation",
                "trip": trip_data,
                "research": research_data,
                "budget": budget_data,
                "itinerary": itinerary_data,
                "agent_activity": self.status
            }

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        await event_manager.publish(
            request_id,
            {
                "type": "agent_completed",
                "agent": "Supervisor Agent",
                "message": "Trip plan orchestration completed",
            },
        )

        await self.publish_completion(
            request_id,
            "Validation",
            "TripGenie AI completed your travel plan.",
        )

        return {
            "success": True,
            "message": "TripGenie AI completed your travel plan.",
            "trip": trip_data,
            "research": research_data,
            "budget": budget_data,
            "itinerary": itinerary_data,
            "validation": validation,
            "agent_activity": self.status
        }