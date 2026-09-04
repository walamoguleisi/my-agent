# backend/agent_cli.py
# 6th simple test of LLM API, agent event generator consumer

from app.agent import run_agent_events

def print_event(event: dict) -> None:
    event_type = event["type"]

    if event_type == "iteration_start":
        print(f"\n--- 第 {event['iteration']} 轮 ---")

    elif event_type == "token":
        print(event["content"], end="", flush=True)
    
    elif event_type == "tool_start":
        print()
        print(f"[tool_start] {event['name']}")
        print(f"args: {event['args']}")
    
    elif event_type == "tool_result":
        print(f"[tool_result] {event['name']}")
        print(event["output"])
    
    elif event_type == "done":
        print("\n[done]")

    elif event_type == "error":
        print(f"\n[error] {event['message']}")


def main() -> None:
    print("my-agent CLI, 输入 exit 退出")

    while True:
        user_input = input("\n你: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            break
        
        if not user_input:
            continue
        
        print("AI: ",end="", flush=True)

        for event in run_agent_events(user_input):   # 通过for循环来调用生成器
            print_event(event)

if __name__ == "__main__":
    main()
