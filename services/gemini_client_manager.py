import os
import random
from google import genai

class GeminiClientManager:
    def __init__(self):
        # Retrieve keys from environment variable GEMINI_API_KEYS (comma-separated list)
        # Fall back to GEMINI_API_KEY if not defined
        keys_str = os.environ.get('GEMINI_API_KEYS') or os.environ.get('GEMINI_API_KEY') or ""
        
        # Split, strip whitespace, and filter empty strings
        self.keys = [k.strip() for k in keys_str.split(',') if k.strip()]
        
        # Choose a random starting key to distribute rate-limit load
        self.current_index = random.randint(0, len(self.keys) - 1) if self.keys else 0
        self._clients = {}
        
        print(f"--- GeminiClientManager Initialized with {len(self.keys)} keys ---")

    def get_client_and_key(self):
        if not self.keys:
            return None, None
            
        # Guarantee index is within list bounds
        idx = self.current_index % len(self.keys)
        key = self.keys[idx]
        
        if key not in self._clients:
            try:
                # Instantiate genai Client with this specific key
                self._clients[key] = genai.Client(api_key=key)
            except Exception as e:
                print(f"Error instantiating Gemini client with key {key[:8]}...: {e}")
                return None, None
                
        return self._clients[key], key

    def rotate_key(self):
        if not self.keys:
            return
        old_idx = self.current_index % len(self.keys)
        self.current_index = (self.current_index + 1) % len(self.keys)
        new_idx = self.current_index % len(self.keys)
        print(f"--- Gemini API Key Rotated: switched from key index {old_idx} to {new_idx} ({self.keys[new_idx][:8]}...) ---")

    def execute_with_retry(self, operation_func, *args, **kwargs):
        """
        Executes a function that uses a client, retrying with rotated keys if it fails.
        The operation_func should accept (client, model_name, *args, **kwargs).
        """
        if not self.keys:
            raise RuntimeError("No Gemini API keys configured.")
            
        attempts = len(self.keys)
        last_error = None
        
        # Pop model_name from kwargs, default to gemini-2.5-flash
        model_name = kwargs.pop('model_name', 'gemini-2.5-flash')
        
        for attempt in range(attempts):
            client, key = self.get_client_and_key()
            if not client:
                self.rotate_key()
                continue
                
            try:
                return operation_func(client, model_name, *args, **kwargs)
            except Exception as e:
                error_str = str(e)
                print(f"Gemini call failed with key {key[:8]}...: {error_str}")
                last_error = e
                # Rotate key and try again
                self.rotate_key()
                
        raise last_error or RuntimeError("All Gemini API keys failed.")

# Global singleton manager instance
gemini_manager = GeminiClientManager()
