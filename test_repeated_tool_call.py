a/cache/scratch/test_repeated_tool_calls_v2.py → b/cache/scratch/test_repeated_tool_calls_v2.py
@@ -0,0 +1,498 @@
+import json
+import urllib.request
+import urllib.error
+import concurrent.futures
+import threading
+
+BASE = "http://host.docker.internal:11434/api/chat"
+
+MODELS = [
+    "gemma4:12b-65k",
+    "hermes3:8b-65k",
+    "qwen3.5:4b-65k",
+    "mistral-nemo:12b-65k",
+    "llama3.1:8b-65k",
+    "deepseek-r1:8b-65k",
+]
+
+SETTINGS = {"num_ctx": 65536, "temperature": 0.0, "num_predict": 512}
+REPS = 5
+MAX_TURNS = 8
+
+# ---------------------------------------------------------------- tools -----
+
+TOOLS_CHAIN = [
+    {
+        "type": "function",
+        "function": {
+            "name": "resolve_user",
+            "description": "Resolve a user's internal ID from their email address.",
+            "parameters": {
+                "type": "object",
+                "properties": {"email": {"type": "string"}},
+                "required": ["email"],
+            },
+        },
+    },
+    {
+        "type": "function",
+        "function": {
+            "name": "fetch_user_orders",
+            "description": "Fetch a user's orders given their internal user ID.",
+            "parameters": {
+                "type": "object",
+                "properties": {"user_id": {"type": "string"}},
+                "required": ["user_id"],
+            },
+        },
+    },
+    {
+        "type": "function",
+        "function": {
+            "name": "fetch_order_details",
+            "description": "Fetch details of an order including item IDs.",
+            "parameters": {
+                "type": "object",
+                "properties": {"order_id": {"type": "string"}},
+                "required": ["order_id"],
+            },
+        },
+    },
+    {
+        "type": "function",
+        "function": {
+            "name": "fetch_item_inventory",
+            "description": "Check inventory status for an item.",
+            "parameters": {
+                "type": "object",
+                "properties": {"item_id": {"type": "string"}},
+                "required": ["item_id"],
+            },
+        },
+    },
+]
+
+TOOLS_CURRENCY = [
+    {
+        "type": "function",
+        "function": {
… omitted 420 diff line(s) across 1 additional file(s)/section(s)
