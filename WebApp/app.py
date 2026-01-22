import sys
import traceback
import os
import json
import asyncio
import logging
from datetime import datetime
from aiohttp import web, ClientSession, ClientTimeout, TCPConnector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from botbuilder.core import (
    TurnContext,
    ActivityHandler,
    ConversationState,
    MemoryStorage,
    UserState
)
from botbuilder.schema import Activity, ActivityTypes
from botbuilder.integration.aiohttp import (
    CloudAdapter,
    ConfigurationBotFrameworkAuthentication
)


class DefaultConfig:
    """Bot Configuration"""
    PORT = 8000
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
    APP_TYPE = os.environ.get("MicrosoftAppType", "MultiTenant")
    APP_TENANTID = os.environ.get("MicrosoftAppTenantId", "")
    AI_TIMEOUT = int(os.environ.get("AI_TIMEOUT_SECONDS", "30"))
    MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "2"))


CONFIG = DefaultConfig()
HTTP_SESSION = None

MEMORY = MemoryStorage()
CONVERSATION_STATE = ConversationState(MEMORY)
USER_STATE = UserState(MEMORY)

BOT_AUTH = ConfigurationBotFrameworkAuthentication(CONFIG)
ADAPTER = CloudAdapter(BOT_AUTH)

PF_ENDPOINT = os.environ.get("PROMPT_FLOW_ENDPOINT")
PF_KEY = os.environ.get("PROMPT_FLOW_API_KEY")


async def on_error(context: TurnContext, error: Exception):
    logger.error(f"Unhandled error: {error}", exc_info=True)
    await context.send_activity("The bot encountered an error or bug.")


ADAPTER.on_turn_error = on_error

class MyBot(ActivityHandler):
    def __init__(self, conversation_state: ConversationState, user_state: UserState):
        self.conversation_state = conversation_state
        self.user_state = user_state
        self.history_accessor = self.conversation_state.create_property("history")
        self.user_info_accessor = self.user_state.create_property("user_info")

    async def on_message_activity(self, turn_context: TurnContext):
        user_input = turn_context.activity.text

        if not PF_ENDPOINT:
            await turn_context.send_activity(
                "⚠️ Bot Ready. Brain (Prompt Flow) not connected."
            )
            return

        await turn_context.send_activity(Activity(type=ActivityTypes.typing))

        user_info = await self.user_info_accessor.get(turn_context, {})
        if not user_info:
            user_info = {
                "name": turn_context.activity.from_property.name or "User",
                "locale": turn_context.activity.locale or "en-US"
            }
            await self.user_info_accessor.set(turn_context, user_info)

        history = await self.history_accessor.get(turn_context, []) or []
        history.append({"role": "user", "content": user_input})
        if len(history) > 20:
            history = history[-20:]

        local_timestamp = turn_context.activity.local_timestamp

        if local_timestamp:
            user_time_str = local_timestamp.strftime(
                "%A, %Y-%m-%d %I:%M %p (Offset: %z)"
            )
        else:
            user_time_str = datetime.utcnow().strftime(
                "%A, %Y-%m-%d %I:%M %p UTC"
            )

        data = {
            "chat_input": user_input,
            "chat_history": history[-10:],
            "current_time": user_time_str,
            "user_name": user_info.get("name"),
            "user_locale": user_info.get("locale")
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {PF_KEY}"
        }

        timeout = ClientTimeout(total=CONFIG.AI_TIMEOUT)

        try:
            for attempt in range(CONFIG.MAX_RETRIES):
                try:
                    async with HTTP_SESSION.post(
                        PF_ENDPOINT,
                        json=data,
                        headers=headers,
                        timeout=timeout
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            ai_reply = result.get("chat_output", "")

                            if not ai_reply:
                                ai_reply = (
                                    result.get("output") or
                                    result.get("answer") or
                                    "I couldn't generate a response."
                                )

                            history.append({"role": "assistant", "content": ai_reply})
                            await self.history_accessor.set(turn_context, history)

                            await turn_context.send_activity(ai_reply)
                            break
                        elif attempt < CONFIG.MAX_RETRIES - 1:
                            await asyncio.sleep(1)
                        else:
                            await turn_context.send_activity(
                                f"⚠️ AI service returned status {response.status}"
                            )
                            break

                except asyncio.TimeoutError:
                    if attempt < CONFIG.MAX_RETRIES - 1:
                        logger.warning(f"AI timeout on attempt {attempt + 1}, retrying...")
                        await asyncio.sleep(1)
                    else:
                        logger.error(f"AI timeout after {CONFIG.MAX_RETRIES} attempts")
                        await turn_context.send_activity(
                            "⚠️ AI response timeout. Please try again."
                        )
                        break
                except Exception as e:
                    if attempt < CONFIG.MAX_RETRIES - 1:
                        logger.warning(f"AI error on attempt {attempt + 1}: {str(e)[:100]}, retrying...")
                        await asyncio.sleep(1)
                    else:
                        logger.error(f"AI error after {CONFIG.MAX_RETRIES} attempts: {str(e)}")
                        await turn_context.send_activity(
                            f"⚠️ Error calling AI: {str(e)[:100]}"
                        )
                        break
        finally:
            await self.conversation_state.save_changes(turn_context)
            await self.user_state.save_changes(turn_context)

BOT = MyBot(CONVERSATION_STATE, USER_STATE)


async def messages(req: web.Request) -> web.Response:
    return await ADAPTER.process(req, BOT)


async def index(req: web.Request) -> web.Response:
    return web.Response(
        text="Bot Service is Running (Robust Parser V2)!",
        status=200
    )


async def health(req: web.Request) -> web.Response:
    health_status = {
        "status": "healthy",
        "ai_configured": bool(PF_ENDPOINT and PF_KEY),
        "session_active": HTTP_SESSION is not None and not HTTP_SESSION.closed
    }
    return web.json_response(health_status)


if __name__ == "__main__":
    async def init_app():
        global HTTP_SESSION
        
        # Validate required environment variables
        if not PF_ENDPOINT:
            logger.warning("PROMPT_FLOW_ENDPOINT not configured")
        if not PF_KEY:
            logger.warning("PROMPT_FLOW_API_KEY not configured")
        if not CONFIG.APP_ID or not CONFIG.APP_PASSWORD:
            raise ValueError("MicrosoftAppId and MicrosoftAppPassword are required")
        
        HTTP_SESSION = ClientSession(
            connector=TCPConnector(limit=100, limit_per_host=30, ttl_dns_cache=300),
            timeout=ClientTimeout(total=60)
        )

        app = web.Application()
        app.router.add_post("/api/messages", messages)
        app.router.add_get("/", index)
        app.router.add_get("/health", health)

        async def on_shutdown(app):
            global HTTP_SESSION
            if HTTP_SESSION and not HTTP_SESSION.closed:
                await HTTP_SESSION.close()

        app.on_shutdown.append(on_shutdown)
        return app

    try:
        logger.info(f"--- STARTING CLOUD ADAPTER BOT on port {CONFIG.PORT} ---")
        web.run_app(init_app(), host="0.0.0.0", port=CONFIG.PORT)
    except Exception as error:
        logger.error(f"Startup failed: {error}", exc_info=True)
        raise