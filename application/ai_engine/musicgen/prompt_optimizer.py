import logging
import asyncio
import re
from typing import Optional

from transcriptionist_v3.core.config import AppConfig
from transcriptionist_v3.application.ai_engine.base import AIServiceConfig

logger = logging.getLogger(__name__)

class MusicGenPromptOptimizer:
    """
    MusicGen 提示词优化器
    Core Mission: 将用户输入的中文/口语化描述转化为 MusicGen 友好的英文专业提示词
    """
    
    SYSTEM_PROMPT = (
        "You are an expert music and sound effects prompt engineer for MusicGen AI.\n"
        "Your task is to convert the user's description (in any language) into "
        "a precise English prompt that MusicGen can understand.\n"
        "Rules:\n"
        "1. Output ONLY the English prompt, no explanations.\n"
        "2. Use concrete music/audio terminology (e.g., 'whoosh transition sound', 'deep sub boom').\n"
        "3. Always include: genre/style, main instruments, mood, and tempo (or words like 'slow', 'medium', 'fast').\n"
        "4. Avoid long stories or scene descriptions. Describe the SOUND itself, not a movie plot.\n"
        "5. Keep it concise (ideally 15‑30 words).\n"
        "6. Remove filler words like 'I want', 'please generate', etc.\n"
        "Examples:\n"
        "- '欢快的钢琴曲' -> 'cheerful piano melody with bright chords, upbeat tempo, soft reverb, 120 bpm'\n"
        "- '紧张的电影配乐' -> 'tense cinematic soundtrack with low strings, heavy percussion hits, dark atmosphere, slow tempo 70 bpm'\n"
        "- '呼呼的转场声' -> 'short whoosh swish transition sound effect with airy high frequencies'\n"
        "- '城市街道环境氛围' -> 'urban city street ambience with distant traffic, car passes, light crowd noise, steady background hum'"
    )
    
    def __init__(self):
        self._loop = None
        
    def _get_ai_config(self) -> Optional[AIServiceConfig]:
        """获取当前激活的 AI 配置"""
        try:
            from transcriptionist_v3.application.ai_engine.provider_config import build_ai_service_config_from_app

            config, err, _ = build_ai_service_config_from_app(
                temperature=0.3,
                max_tokens=60,
                timeout=30,
            )
            if err:
                logger.warning(f"No AI config for prompt optimization: {err}")
                return None
            return config
        except Exception as e:
            logger.error(f"Failed to get AI config: {e}")
            return None

    async def _optimize_async(self, user_input: str) -> str:
        """异步执行优化"""
        import aiohttp
        
        config = self._get_ai_config()
        if not config:
            return user_input
            
        try:
            from transcriptionist_v3.application.ai_engine.provider_config import apply_chat_completion_params

            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": config.model_name,
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_input}
                    ],
                }
                apply_chat_completion_params(
                    payload,
                    config.provider_id,
                    config.model_name,
                    max_tokens=config.max_tokens,
                    temperature=0.3,
                )
                headers = {
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{config.base_url}/chat/completions",
                    json=payload, 
                    headers=headers,
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data['choices'][0]['message']['content'].strip()
                        # 清理可能存在的引号
                        return content.replace('"', '').replace("'", "")
                    else:
                        logger.warning(f"Optimization API error: {resp.status}")
                        return user_input
                        
        except Exception as e:
            logger.error(f"Prompt optimization failed: {e}")
            return user_input

    def optimize(self, user_input: str) -> str:
        """
        优化提示词 (同步调用封装)
        
        Args:
            user_input: 用户输入的原始文本 (中文/英文)
            
        Returns:
            str: MusicGen 友好的英文提示词
        """
        # 1. 简单规则过滤：如果是简短英文，直接返回
        if re.match(r'^[a-zA-Z0-9\s,\.]+$', user_input) and len(user_input.split()) < 5:
            return user_input
            
        # 2. 调用 AI 优化
        try:
            # 在现有的事件循环中运行，或者创建新的
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已经在循环中，这里比较麻烦，通常 UI 线程不是 Loop
                    # 在 Qt 环境中，通常可以在后台线程运行
                    import threading
                    if threading.current_thread() is threading.main_thread():
                        # 在主线程，虽然不推荐阻塞，但为了简化集成...
                        pass
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            return loop.run_until_complete(self._optimize_async(user_input))
            
        except Exception as e:
            logger.error(f"Sync optimization wrapper failed: {e}")
            return user_input
