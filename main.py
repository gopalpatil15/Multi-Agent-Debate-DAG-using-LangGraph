import os
import sys
import json
from nodes import UserInputNode, MemoryNode, AgentNode, JudgeNode, append_log
from utils import is_duplicate, generate_dag_dot

LOG_PATH = os.path.join(os.getcwd(), 'debate.log')


def safe_init_log():
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    append_log('--- debate log started ---')


def run_debate():
    safe_init_log()
    # Build nodes
    user_node = UserInputNode()
    memory_node = MemoryNode()
    agentA = AgentNode('AgentA', 'Scientist')
    agentB = AgentNode('AgentB', 'Philosopher')
    judge = JudgeNode()

    # CLI input
    try:
        topic = input('Enter topic for debate: ').strip()
    except KeyboardInterrupt:
        print('\nAborted by user')
        return
    append_log(f'CLI topic input: {topic}')

    state = {
        'topic': topic,
        'memory': {'Scientist': [], 'Philosopher': []},
        'transcript': []
    }

    # Write DAG dot
    with open('dag.dot', 'w', encoding='utf-8') as f:
        f.write(generate_dag_dot())
    append_log('Wrote dag.dot')

    print(f"Starting debate between Scientist and Philosopher...\n")
    append_log('Debate started')

    # Exactly 8 rounds, alternate starting with Scientist (AgentA)
    rounds = 8
    current_agent = agentA
    for r in range(1, rounds + 1):
        state['round_no'] = r
        # prepare visible_memory: each agent gets only the other agent's prior points and shared summary
        other = 'Philosopher' if current_agent.persona == 'Scientist' else 'Scientist'
        visible_memory = {other: state['memory'][other]}
        state['visible_memory'] = visible_memory
        # Run agent
        out = current_agent.run(state)
        arg = out['argument']
        agent_name = out['agent']

        # state validation: turn control (agent identity) — we expect alternation
        expected_persona = 'Scientist' if (r % 2 == 1) else 'Philosopher'
        if agent_name != expected_persona:
            append_log(f'ERROR: Agent spoke out of turn: got {agent_name}, expected {expected_persona}')
            print(f'Protocol error: {agent_name} spoke on round {r} (expected {expected_persona}). Aborting.')
            return

        # No repeated argument
        if is_duplicate(arg, state['transcript']):
            append_log(f'ERROR: Duplicate argument detected on round {r} by {agent_name}')
            print(f'Protocol error: duplicate argument on round {r}. Aborting.')
            return

        # Coherence heuristic (simple): ensure not completely empty and some length
        if len(arg.strip()) < 10:
            append_log(f'ERROR: Incoherent/empty argument on round {r} by {agent_name}')
            print(f'Protocol error: incoherent argument on round {r}. Aborting.')
            return

        # Update transcript and memory
        entry = {'round': r, 'agent': agent_name, 'argument': arg}
        state['transcript'].append(entry)
        state['memory'][agent_name].append({'round': r, 'argument': arg})

        # Summarize memory entry for the other agent (simple summary: first 120 chars)
        summary_snip = arg[:120]
        # each agent receives only "relevant memory" — we simulate by adding summary to opposite memory
        # (the spec said: each agent only receives relevant memory; no full sharing)
        # For traceability, store visible_memory as well
        append_log(f'[Round {r}] {agent_name}: {arg}')
        append_log(f'[Round {r}] Memory update for {agent_name}: {summary_snip}')

        print(f'[Round {r}] {agent_name}: {arg}')

        # Alternate agent
        current_agent = agentB if current_agent is agentA else agentA

    # After rounds, call MemoryNode snapshot and JudgeNode
    memory_snapshot = memory_node.run(state)
    judge_result = judge.run(state)

    # Final print
    print('\n[Judge] Summary of debate:')
    print(judge_result['summary'])
    print(f"\n[Judge] Winner: {judge_result['winner']}")
    print(f"Reason: {judge_result['reason']}\n")

    # Append final outputs to log
    append_log('Final Judge summary written to log')
    with open('final_verdict.json', 'w', encoding='utf-8') as f:
        json.dump(judge_result, f, ensure_ascii=False, indent=2)
    append_log('Wrote final_verdict.json')

    print('Debate complete. Logs written to debate.log and final_verdict.json. DAG saved to dag.dot')


if __name__ == '__main__':
    run_debate()
