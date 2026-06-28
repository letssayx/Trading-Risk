import re

with open('backend/web/ai/routes.py', 'r') as f:
    content = f.read()

# Replace the WS endpoint body entirely to hook into our new 9-step flow
search = "        command = payload.get(\"command\")"
replace = """        command = payload.get("command")
            workspace = payload.get("workspace", "DERIVATIVES")
            symbols = payload.get("symbols", [])

            groq_key = keys.get("groq") or os.getenv("GROQ_API_KEY")
            openrouter_key = keys.get("openrouter") or os.getenv("OPENROUTER_API_KEY")

            orchestrator = TerminalOrchestrator(
                groq_key=groq_key,
                openrouter_key=openrouter_key,
                db=db,
                session_id=session_id
            )

            async def stream_callback(token: str):
                await websocket.send_text(json.dumps({"type": "stream", "chunk": token}))

            async def think_callback(token: str):
                await websocket.send_text(json.dumps({"type": "think", "chunk": token}))

            result = await orchestrator.run_pipeline(
                command=command,
                workspace=workspace,
                symbols=symbols,
                stream_callback=stream_callback,
                think_callback=think_callback
            )

            await websocket.send_text(json.dumps({
                "type": "final",
                "skill_used": result["skill_used"],
                "trade_id": result["trade_id"]
            }))
"""

# Very naive replacement, let's use a regex to replace the entire try/while loop body
pattern = r"command = payload\.get\(\"command\"\).*?(?=except WebSocketDisconnect:)"
new_body = replace

content = re.sub(pattern, new_body, content, flags=re.DOTALL)

with open('backend/web/ai/routes.py', 'w') as f:
    f.write(content)
