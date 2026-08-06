import os
import time
import asyncio
import logging
from typing import AsyncGenerator, Dict, Optional, Literal, Any

try:
    from llama_cpp import Llama
except ImportError:
    logging.warning("llama_cpp not installed. Inference will fail.")
    Llama = None  # type: ignore

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")

# Define mapping from task_type to model filename
TASK_MODEL_MAP = {
    "fast_ner": "Phi-3-mini-4k-instruct-q4.gguf",
    "reasoning": "Mistral-7B-Instruct-v0.3.Q4_K_M.gguf",
    "summarization": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    "embedding": "bge-m3-q4_k_m.gguf",
}

TaskType = Literal["fast_ner", "reasoning", "summarization", "embedding"]


class LLMRouter:
    """Dynamic model loading and task routing system."""

    def __init__(self, idle_timeout: int = 300):
        self.idle_timeout = idle_timeout
        self._current_model: Optional[Llama] = None
        self._current_model_name: Optional[str] = None
        self._last_used: float = 0.0
        self._lock = asyncio.Lock()
        self._unload_task: Optional[asyncio.Task[None]] = None

    async def _start_monitor(self) -> None:
        """Starts the background monitor if not already running."""
        if self._unload_task is None:
            self._unload_task = asyncio.create_task(self._monitor_idle())

    async def _monitor_idle(self) -> None:
        """Background task to unload idle models from VRAM."""
        while True:
            await asyncio.sleep(60)  # Check every minute
            async with self._lock:
                if self._current_model and (time.time() - self._last_used) > self.idle_timeout:
                    logger.info(f"Unloading model {self._current_model_name} due to inactivity.")
                    self._unload_model()

    def _unload_model(self) -> None:
        """Internal method to unload current model."""
        if self._current_model:
            del self._current_model
            self._current_model = None
            self._current_model_name = None

    async def _get_model(self, model_filename: str, is_embedding: bool = False) -> Llama:
        """Loads and returns the requested model."""
        await self._start_monitor()
        async with self._lock:
            if self._current_model_name != model_filename:
                logger.info(f"Loading new model: {model_filename} (Unloading old if necessary)")
                self._unload_model()
                
                model_path = os.path.join(MODELS_DIR, model_filename)
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"Model file {model_path} not found. Please run download_models.py.")
                
                # Load via llama_cpp using mmap. 
                # n_gpu_layers=-1 attempts to offload entirely to GPU if available.
                self._current_model = Llama(
                    model_path=model_path,
                    n_gpu_layers=-1,
                    use_mmap=True,
                    embedding=is_embedding,
                    n_ctx=4096, # 4K context
                    verbose=False
                )
                self._current_model_name = model_filename

            self._last_used = time.time()
            return self._current_model  # type: ignore

    async def generate(self, prompt: str, task_type: TaskType) -> str:
        """Generate a response synchronously (but awaited) for the given task."""
        if task_type not in TASK_MODEL_MAP:
            raise ValueError(f"Unknown task type: {task_type}")

        model_filename = TASK_MODEL_MAP[task_type]
        model = await self._get_model(model_filename, is_embedding=False)

        self._last_used = time.time()
        
        # Run inference in a thread pool since llama_cpp is synchronous
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.create_completion(
                prompt=prompt,
                max_tokens=1024,
                stream=False
            )
        )
        return response["choices"][0]["text"] # type: ignore

    async def generate_stream(self, prompt: str, task_type: TaskType) -> AsyncGenerator[str, None]:
        """Stream generation response."""
        if task_type not in TASK_MODEL_MAP:
            raise ValueError(f"Unknown task type: {task_type}")

        model_filename = TASK_MODEL_MAP[task_type]
        model = await self._get_model(model_filename, is_embedding=False)
        self._last_used = time.time()
        
        # Since llama_cpp streaming is a blocking generator, we use a trick to make it async.
        # Alternatively, we iterate through it in an executor.
        loop = asyncio.get_event_loop()
        
        def run_stream():  # type: ignore
            return model.create_completion(prompt=prompt, max_tokens=1024, stream=True)
            
        stream = await loop.run_in_executor(None, run_stream)
        
        for chunk in stream:
            # We don't want to block the event loop for too long in the generator
            self._last_used = time.time()
            text = chunk["choices"][0]["text"]
            yield text
            await asyncio.sleep(0) # yield control

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text."""
        model_filename = TASK_MODEL_MAP["embedding"]
        model = await self._get_model(model_filename, is_embedding=True)
        self._last_used = time.time()

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.create_embedding(text)
        )
        return response["data"][0]["embedding"] # type: ignore

    async def close(self) -> None:
        """Close router and unload model."""
        if self._unload_task:
            self._unload_task.cancel()
        async with self._lock:
            self._unload_model()

# Global router instance for the application
router = LLMRouter()
