from __future__ import annotations
import abc
import time
import json
from typing import Any, Dict, List, Optional
import os

LOG_PATH = os.path.join(os.getcwd(), 'debate.log')

# Lightweight logger
def append_log(line: str):
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f'[{ts}] {line}\n')


class Node(abc.ABC):
    def __init__(self, name: str):
        self.name = name

    @abc.abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass


class UserInputNode(Node):
    def __init__(self):
        super().__init__('UserInputNode')

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state.get('topic')
        append_log(f'Node[{self.name}] received topic: {topic}')
        return {'topic': topic}


class MemoryNode(Node):
    """Stores per-agent memory summaries and full transcripts.
    state keys it maintains: memory (dict per agent), transcript (list)
    """
    def __init__(self):
        super().__init__('MemoryNode')
        # initialize file-level log of memory
        append_log(f'Node[{self.name}] initialized')

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # memory updates are done externally; just return current memory snapshot
        mem = state.get('memory', {})
        append_log(f'Node[{self.name}] snapshot: {json.dumps(mem, ensure_ascii=False)}')
        return {'memory': mem, 'transcript': state.get('transcript', [])}


class AgentNode(Node):
    def __init__(self, name: str, persona: str):
        super().__init__(name)
        self.persona = persona

    def generate_argument(self, topic: str, round_no: int, visible_memory: Dict[str, Any], transcript: List[Dict[str,str]]) -> str:
        """A placeholder generator: uses heuristics to construct a short argument string.
        In a real LangGraph + LLM environment, you'd call the model here with a persona prompt.
        """
        # Build a simple, deterministic argument using persona, topic and round number with reference to memory.
        prior_points = []
        for t in transcript[-6:]:
            if t['agent'] != self.persona:
                prior_points.append(t['argument'])
        # make a compact argument that references prior points if any
        base = f"As a {self.persona}, I argue that {topic}"
        if prior_points:
            base += f" — building on earlier points like '{prior_points[-1][:60]}...'"
        base += f" (round {round_no})."
        return base

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state['topic']
        round_no = state['round_no']
        visible_memory = state.get('visible_memory', {})
        transcript = state.get('transcript', [])
        arg = self.generate_argument(topic, round_no, visible_memory, transcript)
        append_log(f'Node[{self.name}] produced argument: "{arg}"')
        return {'argument': arg, 'agent': self.persona}


class JudgeNode(Node):
    def __init__(self):
        super().__init__('JudgeNode')

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Accept memory + transcript and produce summary + winner
        transcript = state.get('transcript', [])
        memory = state.get('memory', {})
        append_log(f'Node[{self.name}] received transcript of {len(transcript)} entries')

        # Produce a simple summary: top 3 concise lines and a scoring heuristic
        summary_lines = []
        if not transcript:
            summary_lines.append('No arguments were presented.')
        else:
            for i, t in enumerate(transcript[-8:]):
                summary_lines.append(f"[{i+1}] {t['agent']}: {t['argument'][:160]}")

        # rudimentary scoring: count presence of risk/public-safety words for Scientist
        scientist_score = 0
        philosopher_score = 0
        s_words = ['risk', 'safety', 'regulated', 'harm', 'medical', 'clinical', 'testing']
        p_words = ['autonomy', 'freedom', 'ethics', 'progress', 'philosophy', 'meaning']
        for t in transcript:
            a = t['agent']
            text = t['argument'].lower()
            s_ct = sum(text.count(w) for w in s_words)
            p_ct = sum(text.count(w) for w in p_words)
            if a.lower().startswith('scient'):
                scientist_score += 1 + s_ct
            else:
                philosopher_score += 1 + p_ct
        # tie-breaker: who used more unique points
        unique_scientist = len({t['argument'] for t in transcript if t['agent'].lower().startswith('scient')})
        unique_philosopher = len({t['argument'] for t in transcript if t['agent'].lower().startswith('philos')})
        scientist_score += unique_scientist * 0.5
        philosopher_score += unique_philosopher * 0.5

        if scientist_score > philosopher_score:
            winner = 'Scientist'
            reason = f'Scientist scored {scientist_score:.1f} vs Philosopher {philosopher_score:.1f} — stronger risk/safety grounding.'
        elif philosopher_score > scientist_score:
            winner = 'Philosopher'
            reason = f'Philosopher scored {philosopher_score:.1f} vs Scientist {scientist_score:.1f} — stronger autonomy/ethics framing.'
        else:
            winner = 'Tie'
            reason = f'Scores equal ({scientist_score:.1f}). Logical strengths balanced.'

        summary_text = '\n'.join(summary_lines)
        result = {
            'summary': summary_text,
            'winner': winner,
            'reason': reason,
            'scores': {'Scientist': scientist_score, 'Philosopher': philosopher_score}
        }
        append_log(f'Node[{self.name}] judgment: Winner={winner}; Reason={reason}')
        append_log(f'Node[{self.name}] summary: {summary_text}')
        return result
