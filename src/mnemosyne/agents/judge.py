import logging
import uuid
from typing import Dict, Any, List

from .base import BaseAgent, AgentMessage
from .bus import bus
from mnemosyne.models.llm_router import router

logger = logging.getLogger(__name__)

JUDGE_PROMPT = """You are an impartial Judge in a Digital Forensics Debate.
Analyze the following debate regarding an entity/relationship.
Provide a clear decision on which argument is correct, and explain your reasoning.
Output MUST be valid JSON:
{{
  "decision": "Argument A is correct",
  "reasoning_chain": ["Step 1...", "Step 2..."],
  "confidence": 0.9
}}

Debate Context:
{context}

Argument A: {arg_a}
Argument B: {arg_b}
"""

class JudgeAgent(BaseAgent):
    """
    Conflict resolution and debate mediation.
    """
    def __init__(self):
        super().__init__(name="JudgeAgent")
        self.decisions_log: List[Dict[str, Any]] = []

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Support manual override
        if input_data.get("human_override"):
            logger.info("Human override received! Bypassing Judge LLM.")
            override_decision = {
                "decision": input_data["human_override"],
                "reasoning_chain": ["Human explicitly overrode the decision."],
                "confidence": 1.0,
                "is_override": True
            }
            self.decisions_log.append(override_decision)
            return override_decision

        context = input_data.get("context", "")
        arg_a = input_data.get("arg_a", "")
        arg_b = input_data.get("arg_b", "")
        
        prompt = JUDGE_PROMPT.format(context=context, arg_a=arg_a, arg_b=arg_b)
        
        logger.info("[JudgeAgent] Mediating debate...")
        
        try:
            # Use reasoning task type
            response = await router.generate(prompt=prompt, task_type="reasoning")
            
            import json
            try:
                parsed = json.loads(response)
            except json.JSONDecodeError:
                logger.error("[JudgeAgent] Failed to parse LLM response as JSON.")
                parsed = {
                    "decision": "Inconclusive due to parsing error",
                    "reasoning_chain": [response],
                    "confidence": 0.0
                }
                
            parsed["is_override"] = False
            self.decisions_log.append(parsed)
            return parsed
            
        except Exception as e:
            logger.error(f"[JudgeAgent] LLM Generation failed: {e}")
            raise e
