
import os
from pathlib import Path
from dotenv import load_dotenv

from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

import json
from fastapi.concurrency import run_in_threadpool

from app.services.copilot_lookup_service import resolve_sprint_context

from app.database.connection import get_db
from app.services.metrics.delivery_service import get_delivery_summary
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

import logging

logger = logging.getLogger(__name__)

# Load environment variables from backend/.env
BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])

@router.get("/health")
def copilot_health():
    return {
        "status": "ok",
        "message": "AI Copilot API is running"
    }

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[dict[str, str]] = Field(default_factory=list)
    organization_id: UUID | None = None

class ChatResponse(BaseModel):
    answer: str


SYSTEM_PROMPT = """
You are an expert Scrum Master AI Copilot.

You help Scrum Masters analyze sprint delivery performance,
velocity, delivery risks, rework, and Agile practices.

You have access to an approved database tool called analyze_sprint.

Rules:
1. Use the analyze_sprint tool when the user requests actual
   sprint delivery metrics or performance analysis.

2. The tool requires a team name and sprint name.

3. If either name is missing, ask a concise clarification
   question unless it is clear from conversation history.

4. Never invent teams, sprints, work items, or metrics.

5. Never claim to have retrieved database information
   unless a tool has returned that information.

6. Base sprint analysis on the metrics returned by the tool.

7. Distinguish actual findings from recommendations.

8. Do not assume a sprint is behind schedule without
   knowing its dates or progress through the sprint.

9. Keep answers practical, professional, and concise.

10. For general Agile questions, answer directly without
    calling the database tool.
"""


COPILOT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_sprint",
            "description": (
                "Retrieve actual delivery metrics for a "
                "specific team and sprint."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "team_name": {
                        "type": "string",
                        "description": "Name of the Scrum team"
                    },
                    "sprint_name": {
                        "type": "string",
                        "description": "Name of the sprint"
                    }
                },
                "required": [
                    "team_name",
                    "sprint_name"
                ],
                "additionalProperties": False
            }
        }
    }
]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured"
        )

    client = AsyncOpenAI(api_key=api_key)

    # Validate and prepare conversation history
    history = [
        {
            "role": item["role"],
            "content": item["content"]
        }
        for item in request.history[-10:]
        if item.get("role") in ("user", "assistant")
        and isinstance(item.get("content"), str)
    ]

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        *history,
        {
            "role": "user",
            "content": request.message
        }
    ]

    try:
        # Step 1: Ask OpenAI whether a tool is needed
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=messages,
            tools=COPILOT_TOOLS,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message

        # Step 2: Handle tool calls
        if assistant_message.tool_calls:

            messages.append(
                assistant_message.model_dump(
                    exclude_none=True
                )
            )

            for tool_call in assistant_message.tool_calls:

                if tool_call.function.name != "analyze_sprint":
                    raise HTTPException(
                        status_code=400,
                        detail="Unsupported Copilot tool"
                    )

                try:
                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                    team_name = arguments["team_name"]
                    sprint_name = arguments["sprint_name"]

                    if (
                        not isinstance(team_name, str)
                        or not team_name.strip()
                        or not isinstance(sprint_name, str)
                        or not sprint_name.strip()
                    ):
                        raise ValueError("Invalid team or sprint name")

                except (ValueError, KeyError, TypeError):
                    tool_result = {
                        "status": "invalid_arguments",
                        "message": (
                            "A valid team name and sprint name "
                            "are required."
                        )
                    }

                else:
                    if request.organization_id is None:
                        tool_result = {
                            "status": "missing_organization",
                            "message": (
                                "Organization context is required "
                                "to retrieve sprint metrics."
                            )
                        }

                    else:
                        # Resolve names to PostgreSQL IDs
                        context = await run_in_threadpool(
                            resolve_sprint_context,
                            db,
                            request.organization_id,
                            team_name,
                            sprint_name
                        )

                        if context["status"] != "resolved":
                            tool_result = context

                        else:
                            sprint = context["sprint"]
                            team = context["team"]

                            # Retrieve actual delivery metrics
                            summary = await run_in_threadpool(
                                get_delivery_summary,
                                db=db,
                                organization_id=request.organization_id,
                                team_id=UUID(team["id"]),
                                sprint_id=UUID(sprint["id"])
                            )

                            tool_result = {
                                "status": "success",
                                "team": team,
                                "sprint": sprint,
                                "delivery_metrics": summary
                            }

                # Step 3: Return the tool result to OpenAI
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        tool_result,
                        default=str
                    )
                })

            # Step 4: Ask OpenAI to interpret the results
            final_response = await client.chat.completions.create(
                model=os.getenv(
                    "OPENAI_MODEL",
                    "gpt-4.1-mini"
                ),
                messages=messages,
            )

            answer = (
                final_response.choices[0].message.content
                or "No response was generated."
            )

        else:
            # General question: no database lookup needed
            answer = (
                assistant_message.content
                or "No response was generated."
            )

        return ChatResponse(answer=answer)

    except HTTPException:
        raise

    except HTTPException:
        raise

    except Exception as e:
        import traceback

        print("AI COPILOT ERROR:", repr(e))
        traceback.print_exc()

        raise HTTPException(
            status_code=502,
            detail="The AI Copilot could not complete the request."
        )

@router.get("/delivery-summary")
def copilot_delivery_summary(
    organization_id: UUID,
    team_id: UUID,
    sprint_id: UUID,
    db: Session = Depends(get_db)
):
    summary = get_delivery_summary(
        db=db,
        organization_id=organization_id,
        team_id=team_id,
        sprint_id=sprint_id
    )

    return summary

import json


class SprintAnalysisRequest(BaseModel):
    organization_id: UUID
    team_id: UUID
    sprint_id: UUID
    message: str = Field(min_length=1)


@router.post(
    "/analyze-sprint",
    response_model=ChatResponse
)
async def analyze_sprint(
    request: SprintAnalysisRequest,
    db: Session = Depends(get_db)
):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured"
        )

    # Step 1: Retrieve actual sprint metrics
    summary = get_delivery_summary(
        db=db,
        organization_id=request.organization_id,
        team_id=request.team_id,
        sprint_id=request.sprint_id
    )

    if not summary:
        raise HTTPException(
            status_code=404,
            detail="Sprint metrics not found"
        )

    # Step 2: Convert metrics to JSON
    metrics_json = json.dumps(
        summary,
        indent=2,
        default=str
    )

    # Step 3: Create the AI prompt
    system_prompt = """
    You are an expert Scrum Master AI Copilot.

    Analyze sprint delivery performance using
    the PostgreSQL metrics supplied.

    Explain:
    - Sprint commitment performance
    - Current scope completion
    - Delivery risks
    - Blocked and reopened work items
    - Recommended Scrum Master actions

    Rules:
    - Use only the supplied metrics.
    - Never invent data.
    - Distinguish findings from recommendations.
    - Do not assume the sprint is behind schedule
      without knowing sprint progress or dates.
    - Keep responses practical and concise.
    """

    client = AsyncOpenAI(api_key=api_key)

    try:
        response = await client.chat.completions.create(
            model=os.getenv(
                "OPENAI_MODEL",
                "gpt-4.1-mini"
            ),
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": (
                        f"Sprint metrics:\n{metrics_json}\n\n"
                        f"User question: {request.message}"
                    )
                }
            ]
        )

        return ChatResponse(
            answer=(
                response.choices[0].message.content
                or "No response was generated."
            )
        )

    except Exception:
        logger.exception("AI Copilot chat failed")

        raise HTTPException(
            status_code=502,
            detail="The AI Copilot could not complete the request."
        )

@router.get("/resolve-sprint")
def resolve_sprint(
    organization_id: UUID,
    team_name: str,
    sprint_name: str,
    db: Session = Depends(get_db)
):
    return resolve_sprint_context(
        db=db,
        organization_id=organization_id,
        team_name=team_name,
        sprint_name=sprint_name
    )