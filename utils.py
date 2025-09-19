import hashlib
import re
from typing import List, Dict


def is_duplicate(argument: str, transcript: List[Dict[str,str]]) -> bool:
    # Consider duplicate if exact match or high overlap of tokens
    def normalize(s):
        return re.sub(r"\\W+", ' ', s.lower()).strip()
    norm = normalize(argument)
    for t in transcript:
        if normalize(t['argument']) == norm:
            return True
    return False


def generate_dag_dot() -> str:
    dot = '''digraph DebateDAG {
  rankdir=LR;
  UserInputNode [shape=box];
  AgentA [shape=ellipse,label="AgentA\n(Scientist)"];
  AgentB [shape=ellipse,label="AgentB\n(Philosopher)"];
  MemoryNode [shape=note];
  JudgeNode [shape=diamond];
  UserInputNode -> AgentA;
  UserInputNode -> AgentB;
  AgentA -> MemoryNode;
  AgentB -> MemoryNode;
  MemoryNode -> AgentA;
  MemoryNode -> AgentB;
  AgentA -> JudgeNode;
  AgentB -> JudgeNode;
  MemoryNode -> JudgeNode;
}
'''
    return dot
