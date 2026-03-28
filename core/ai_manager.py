# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  For commercial licensing, please contact the author.
"""
Module: ai_manager.py (v3.4 - System Prompt Override)
Project: TALOS v4.2

Description:
Προσθέτει τη δυνατότητα παράκαμψης του προεπιλεγμένου System Prompt.
Απαραίτητο για την Πυθία, ώστε να μπορεί να δώσει το δικό της prompt
χωρίς να μπερδεύεται το AI με το prompt του PhD Advisor.
"""
import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai
import openai
from typing import Union, List, Dict, Any

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
                'consecutive_failures': 0,
                'circuit_open': False
            }
            print("INFO: Gemini provider initialized.")

        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_api_key:
            self.providers['deepseek'] = {
                'client': openai.OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1"),
                'model_name': config.get("deepseek_model_chat", "deepseek-chat"),
                'consecutive_failures': 0,
                'circuit_open': False
            }
            print("INFO: DeepSeek provider initialized.")
            
        self.FAILURE_THRESHOLD = config.get("failure_threshold", 5)
        print(f"INFO: AIManager v3.4 (System Prompt Override) initialized.")

    def _clean_json_string(self, text: str) -> str:
        match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL)
        if match: text = match.group(1)
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1: return text[start:end+1]
        return text.strip()

    # --- Η ΑΛΛΑΓΗ ΕΙΝΑΙ ΕΔΩ ---
    def evaluate_paper_json(self, paper_content: str, model_type: str = 'pro', system_prompt_override: str = None) -> Union[Dict[str, Any], None]:
        """
        Εκτελεί αξιολόγηση και επιστρέφει JSON.
        Αν δοθεί 'system_prompt_override', χρησιμοποιείται αυτό αντί του default από το config.
        """
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

    def generate_embeddings(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> Union[List[Any], None]:
        if 'gemini' in self.providers and not self.providers['gemini']['circuit_open']:
            try:
                model_name = self.providers['gemini']['embedding_model']
                result = genai.embed_content(model=model_name, content=texts, task_type=task_type)
                return result.get('embedding')
            except Exception as e:
                print(f"  >!> Gemini embedding failed: {e}")
                self._handle_failure('gemini')
        print("ERROR: No available provider for embeddings.")
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
            json_instruction = "\n\nIMPORTANT: Your response MUST be a single, valid JSON object. Do not include any text explanation before or after the JSON."
            final_prompt += json_instruction
            
        try:
            chat_completion = provider['client'].chat.completions.create(
                model=provider['model_name'],
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.5
            )
            response_text = chat_completion.choices[0].message.content
            
            if response_format == 'json':
                try:
                    clean_text = self._clean_json_string(response_text)
                    return json.loads(clean_text)
                except json.JSONDecodeError:
                    print(f"  >!> DeepSeek JSON decode failed. Raw response start: {response_text[:50]}...")
                    return None
            else:
                return response_text
        except Exception as e:
            print(f"  >!> DeepSeek execution error: {e}")
            if "insufficient_quota" in str(e):
                 self._handle_failure('deepseek')
            return None

    def _handle_failure(self, provider_name: str):
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            provider['consecutive_failures'] += 1
            print(f"  >!> {provider_name.upper()} failure count: {provider['consecutive_failures']}/{self.FAILURE_THRESHOLD}")
            if provider['consecutive_failures'] >= self.FAILURE_THRESHOLD:
                provider['circuit_open'] = True
                print(f"  >!!!> CIRCUIT BREAKER OPEN for {provider_name.upper()}!")