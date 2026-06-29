# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software...
#
"""
Module: ai_manager.py (v3.5 - Local Model Support)
Project: TALOS v4.8.1
"""

# --- Αντέγραψε από εδώ ---

import os, json, re, requests
from dotenv import load_dotenv
import google.generativeai as genai
import openai
from typing import Union, List, Dict, Any
# Note: core.hardware used by _verify_local_models / external callers

class AIManager:
    def __init__(self, config: Dict[str, Any]):
        load_dotenv()
        self.config = config
        self.providers = {}
        self.provider_priority = config.get("ai_provider_priority", ["gemini", "deepseek"])
        
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.providers['gemini'] = {
                'flash_model': genai.GenerativeModel(config.get("pre_screening_model", "gemini-2.5-flash-lite")),
                'pro_model': genai.GenerativeModel(config.get("model_for_daily_search", "gemini-2.5-pro")),
                'embedding_model': "models/text-embedding-004",
                'consecutive_failures': 0, 'circuit_open': False
            }
            print("INFO: Gemini provider initialized.")

        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_api_key:
            self.providers['deepseek'] = {
                'client': openai.OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1"),
                'model_name': config.get("deepseek_model_chat", "deepseek-chat"),
                'consecutive_failures': 0, 'circuit_open': False
            }
            print("INFO: DeepSeek provider initialized.")

        # --- HUGGING FACE PROVIDER (Free cloud inference) ---
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            self.providers['huggingface'] = {
                'client': openai.OpenAI(api_key=hf_token, base_url="https://router.huggingface.co/v1"),
                'model_name': os.getenv("HF_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct"),
                'consecutive_failures': 0, 'circuit_open': False
            }
            print("INFO: Hugging Face provider initialized.")
            if 'huggingface' not in self.provider_priority:
                self.provider_priority.insert(0, 'huggingface')  # Free first
        

        # --- LOCAL MODEL PROVIDER (Ollama) ---
        local_url = os.getenv("LOCAL_MODEL_BASE_URL", "http://localhost:11434/v1")
        self.local_enabled = os.getenv("TALOS_USE_LOCAL", "").lower() in ("1", "true", "yes")
        if self.local_enabled:
            self.providers['local'] = {
                'client': openai.OpenAI(api_key=os.getenv("LOCAL_MODEL_API_KEY", "ollama"), base_url=local_url),
                'model_name': os.getenv("LOCAL_MODEL_NAME", "gemma3:12b"),      
                'embedding_model': os.getenv("LOCAL_EMBEDDING_MODEL", "nomic-embed-text"),
                'ollama_url': local_url.replace("/v1", ""),
                'consecutive_failures': 0, 'circuit_open': False
            }
            if not os.getenv("TALOS_MODELS_VERIFIED"):
                self._ensure_local_model()
            print(f"INFO: Local provider initialized ({self.providers['local']['model_name']}).")
            self.provider_priority.insert(0, 'local')  # local first when enabled
            
            
        self.FAILURE_THRESHOLD = config.get("failure_threshold", 5)
        print(f"INFO: AIManager v3.5 (Local Model Support) initialized.")

    def _clean_json_string(self, text: str) -> str:
        match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL)
        if match: text = match.group(1)
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1: return text[start:end+1]
        return text.strip()

    def evaluate_paper_json(self, paper_content: str, model_type: str = 'pro', system_prompt_override: str = None) -> Union[Dict[str, Any], None]:
        if system_prompt_override:
             full_prompt = f"{system_prompt_override}\n\n---\n\n{paper_content}"
        else:
             prompt_key = 'phd_focus_system_prompt' if model_type == 'pro' else 'pre_screening_prompt'
             system_prompt = self.config.get(prompt_key, "")
             full_prompt = f"{system_prompt}\n\n---\n\n**// PAPER TO ANALYZE //**\n\n{paper_content}"
        return self._execute_request(full_prompt, model_type, response_format='json')

    def analyze_generic_text(self, full_prompt: str) -> str:
        result = self._execute_request(full_prompt, 'pro', response_format='text')
        return result if result is not None else "All AI providers failed to generate a response."

    def generate_embeddings(self, texts, task_type=None):
        # Try local first
        if 'local' in self.providers:
            try:
                p = self.providers['local']
                resp = requests.post(f"{p['ollama_url']}/api/embed",
                    json={"model": p['embedding_model'], "input": texts}, timeout=60)
                if resp.status_code == 200:
                    return resp.json().get('embeddings')
                print(f"  >!> Local embedding status: {resp.status_code}")
            except Exception as e:
                print(f"  >!> Local embedding error: {e}")
        # Fallback to Gemini
        if 'gemini' in self.providers:
            try:
                result = genai.embed_content(
                    model=self.providers['gemini']['embedding_model'],
                    content=texts, task_type="RETRIEVAL_DOCUMENT")
                return result['embedding']
            except Exception as e:
                print(f"  >!> Gemini embedding failed: {e}")
        print("ERROR: No embedding provider available.")
        return None           

    def _execute_request(self, prompt: str, model_type: str, response_format: str = 'text') -> Union[Dict[str, Any], str, None]:
        for provider_name in self.provider_priority:
            if provider_name in self.providers and not self.providers[provider_name]['circuit_open']:
                print(f"  > Attempting request with provider: {provider_name.upper()}")
                result = None
                if provider_name == 'gemini':
                    result = self._execute_gemini_request(prompt, model_type, response_format)
                elif provider_name == 'deepseek':
                    result = self._execute_deepseek_request(prompt, response_format)                    
                elif provider_name == 'huggingface':
                    result = self._execute_openai_compatible(prompt, response_format, 'huggingface')
                elif provider_name == 'local':
                    result = self._execute_openai_compatible(prompt, response_format, 'local')
                if result is not None:
                    self.providers[provider_name]['consecutive_failures'] = 0
                    return result                   
                    
                else:
                    print(f"  >!> Provider {provider_name.upper()} failed. Trying next provider...")
                    continue
        print("FATAL: All AI providers failed.")
        return None

    def _execute_gemini_request(self, prompt: str, model_type: str, response_format: str) -> Union[Dict[str, Any], str, None]:
        provider = self.providers['gemini']
        model = provider['pro_model'] if model_type == 'pro' else provider['flash_model']
        try:
            if response_format == 'json':
                config = genai.types.GenerationConfig(response_mime_type="application/json")
                response = model.generate_content(prompt, generation_config=config)
                return json.loads(response.text)
            else:
                response = model.generate_content(prompt)
                return response.text
        except Exception as e:
            print(f"  >!> Gemini execution error: {e}")
            if "429" in str(e) or "resource exhausted" in str(e).lower():
                self._handle_failure('gemini')
            return None

    def _execute_deepseek_request(self, prompt: str, response_format: str) -> Union[Dict[str, Any], str, None]:
        provider = self.providers['deepseek']
        final_prompt = prompt
        if response_format == 'json':
            final_prompt += "\n\nIMPORTANT: Your response MUST be a single, valid JSON object. Do not include any text explanation before or after the JSON."
        try:
            chat_completion = provider['client'].chat.completions.create(
                model=provider['model_name'],
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.5)
            response_text = chat_completion.choices[0].message.content
            if response_format == 'json':
                try:
                    return json.loads(self._clean_json_string(response_text))
                except json.JSONDecodeError:
                    print(f"  >!> DeepSeek JSON decode failed.")
                    return None
            return response_text
        except Exception as e:
            print(f"  >!> DeepSeek execution error: {e}")
            if "insufficient_quota" in str(e):
                 self._handle_failure('deepseek')
            return None

    def _execute_openai_compatible(self, prompt: str, response_format: str, provider_name='local') -> Union[Dict[str, Any], str, None]:
        provider = self.providers[provider_name]
        final_prompt = prompt
        if response_format == 'json':
            final_prompt += "\n\nIMPORTANT: Return ONLY a valid JSON object. No markdown, no explanation."
        try:
            response = provider['client'].chat.completions.create(
                model=provider['model_name'],
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.3)
            text = response.choices[0].message.content
            if response_format == 'json':
                try:
                    return json.loads(self._clean_json_string(text))
                except json.JSONDecodeError:
                    print(f"  >!> Local model JSON decode failed.")
                    return None
            return text
        except Exception as e:
            print(f"  >!> {provider_name.upper()} execution error: {e}")
            self._handle_failure(provider_name)
            return None   

    def _handle_failure(self, provider_name: str):
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            provider['consecutive_failures'] += 1
            print(f"  >!> {provider_name.upper()} failure count: {provider['consecutive_failures']}/{self.FAILURE_THRESHOLD}")
            if provider['consecutive_failures'] >= self.FAILURE_THRESHOLD:
                provider['circuit_open'] = True
                print(f"  >!!!> CIRCUIT BREAKER OPEN for {provider_name.upper()}!")
