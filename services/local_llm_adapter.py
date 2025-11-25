"""
Local LLM Adapter

Provides interface for local LLM integration (Ollama, Llama.cpp, etc.)
for offline AI responses without API costs.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)

# Try to import Ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None  # type: ignore

# Try to import llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    Llama = None  # type: ignore

# Try to import transformers (Hugging Face)
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    AutoModelForCausalLM = None  # type: ignore
    AutoTokenizer = None  # type: ignore
    pipeline = None  # type: ignore
    torch = None  # type: ignore


class LocalLLMAdapter:
    """
    Adapter for local LLM inference.
    
    Supports multiple backends:
    - Ollama (easiest to use)
    - llama.cpp (lightweight, fast)
    - Transformers (Hugging Face models)
    """
    
    def __init__(
        self,
        backend: str = "ollama",
        model_name: Optional[str] = None,
        model_path: Optional[str] = None
    ):
        """
        Initialize local LLM adapter.
        
        Args:
            backend: Backend to use ("ollama", "llama_cpp", "transformers")
            model_name: Model name (for Ollama or Hugging Face)
            model_path: Path to model file (for llama.cpp)
        """
        self.backend = backend
        self.model_name = model_name
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.available = False
        
        self._initialize_backend()
    
    def _initialize_backend(self) -> None:
        """Initialize the selected backend."""
        if self.backend == "ollama" and OLLAMA_AVAILABLE:
            self._initialize_ollama()
        elif self.backend == "llama_cpp" and LLAMA_CPP_AVAILABLE:
            self._initialize_llama_cpp()
        elif self.backend == "transformers" and TRANSFORMERS_AVAILABLE:
            self._initialize_transformers()
        else:
            LOGGER.warning("Local LLM backend not available: %s", self.backend)
            self.available = False
    
    def _initialize_ollama(self) -> None:
        """Initialize Ollama backend."""
        try:
            # Check if Ollama is running
            models = ollama.list()
            if models:
                # Use first available model or specified model
                if self.model_name:
                    self.model_name = self.model_name
                else:
                    # Try common small models
                    for model in ["llama2", "mistral", "phi"]:
                        try:
                            ollama.show(model)
                            self.model_name = model
                            break
                        except:
                            continue
                
                if self.model_name:
                    self.available = True
                    LOGGER.info("Ollama initialized with model: %s", self.model_name)
                else:
                    LOGGER.warning("No suitable Ollama model found")
            else:
                LOGGER.warning("Ollama not running or no models installed")
        except Exception as e:
            LOGGER.warning("Failed to initialize Ollama: %s", e)
            self.available = False
    
    def _initialize_llama_cpp(self) -> None:
        """Initialize llama.cpp backend."""
        if not self.model_path:
            LOGGER.warning("llama.cpp requires model_path")
            return
        
        try:
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=2048,  # Context window
                n_threads=4,  # CPU threads
                verbose=False,
            )
            self.available = True
            LOGGER.info("llama.cpp initialized with model: %s", self.model_path)
        except Exception as e:
            LOGGER.error("Failed to initialize llama.cpp: %s", e)
            self.available = False
    
    def _initialize_transformers(self) -> None:
        """Initialize Transformers backend."""
        if not self.model_name:
            # Use a small, fast model
            self.model_name = "microsoft/DialoGPT-small"
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            )
            
            # Create pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=512,
            )
            
            self.available = True
            LOGGER.info("Transformers initialized with model: %s", self.model_name)
        except Exception as e:
            LOGGER.error("Failed to initialize Transformers: %s", e)
            self.available = False
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate response using local LLM.
        
        Args:
            prompt: User prompt/question
            system_prompt: System prompt/instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            context: Conversation context (list of {role, content} dicts)
        
        Returns:
            Generated response
        """
        if not self.available:
            raise RuntimeError(f"Local LLM backend not available: {self.backend}")
        
        if self.backend == "ollama":
            return self._generate_ollama(prompt, system_prompt, max_tokens, temperature, context)
        elif self.backend == "llama_cpp":
            return self._generate_llama_cpp(prompt, system_prompt, max_tokens, temperature)
        elif self.backend == "transformers":
            return self._generate_transformers(prompt, system_prompt, max_tokens, temperature)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
    
    def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        context: Optional[List[Dict[str, str]]]
    ) -> str:
        """Generate using Ollama."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if context:
            messages.extend(context)
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )
            return response["message"]["content"].strip()
        except Exception as e:
            LOGGER.error("Ollama generation failed: %s", e)
            raise
    
    def _generate_llama_cpp(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using llama.cpp."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            response = self.model(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["\n\n", "User:", "Assistant:"],
            )
            return response["choices"][0]["text"].strip()
        except Exception as e:
            LOGGER.error("llama.cpp generation failed: %s", e)
            raise
    
    def _generate_transformers(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using Transformers."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            outputs = self.pipeline(
                full_prompt,
                max_length=len(full_prompt.split()) + max_tokens,
                temperature=temperature,
                do_sample=True,
                num_return_sequences=1,
            )
            generated_text = outputs[0]["generated_text"]
            # Remove the prompt from the response
            response = generated_text[len(full_prompt):].strip()
            return response
        except Exception as e:
            LOGGER.error("Transformers generation failed: %s", e)
            raise
    
    def is_available(self) -> bool:
        """Check if local LLM is available."""
        return self.available


__all__ = ["LocalLLMAdapter"]









