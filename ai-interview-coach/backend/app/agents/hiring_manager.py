from __future__ import annotations

import json

from app.llm.json_utils import parse_json_or_repair
from app.llm.openai_compatible import OpenAICompatibleChatClient
from app.llm.prompts import load_prompt
from app.models import AgentQuestion, InterviewSession


class HiringManagerAgent:
    def __init__(self, client: OpenAICompatibleChatClient | None = None) -> None:
        self.client = client or OpenAICompatibleChatClient()
        self.system_prompt = load_prompt("hiring_manager_prompt.md")

    async def next_question(self, session: InterviewSession) -> AgentQuestion:
        user_context = {
            "job_announcement": session.job_announcement,
            "candidate_profile": session.candidate_profile,
            "hiring_manager_instructions": session.hiring_manager_instructions or session.agent_instructions,
            "language_mode": session.language_mode,
            "history": [turn.model_dump() for turn in session.turns],
        }
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": "Generate the next interview question from this context:\n"
                + json.dumps(user_context, ensure_ascii=False, indent=2),
            },
        ]
        raw = await self.client.complete(messages, json_mode=True)
        data = await parse_json_or_repair(raw, self._repair_json)
        return AgentQuestion.model_validate(data)

    async def _repair_json(self, bad_text: str) -> str:
        messages = [
            {"role": "system", "content": "Return only valid JSON matching the hiring-manager question schema."},
            {"role": "user", "content": bad_text},
        ]
        return await self.client.complete(messages, json_mode=True)
