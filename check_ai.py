"""Live check: connects to DNotifier and asks the AI one tiny question. Run: python check_ai.py"""
import asyncio, os
from dotenv import load_dotenv
from dnotifier import DNotifier
from agents.ai_utils import extract_ai_text, ai_kwargs

load_dotenv()

async def main():
    n = DNotifier(app_id=os.environ["DNOTIFIER_APP_ID"], secret=os.environ["DNOTIFIER_SECRET"],
                  transport="http", user_id=os.environ.get("DNOTIFIER_USER_ID", "founderslens-system"))
    await n.connect()
    print("1) Connected to DNotifier: OK")
    resp = await n.send_ai(sender_id=n.user_id,
                           message={"useKnowledgeBase": False, "messages": [{"role": "user", "content": "Reply with exactly: AI IS WORKING"}]},
                           save_history=False, **ai_kwargs())
    print("2) AI reply:", extract_ai_text(resp))
    await n.disconnect()

asyncio.run(main())
