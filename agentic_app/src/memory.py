import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class InMemoryStorage:
    """In-memory message storage."""
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(msg)
        return msg
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def clear(self) -> None:
        self.messages = []
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        return [m for m in self.messages if query_lower in m["content"].lower()]


class FileStorage:
    """File-based persistent storage with caching."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            home = os.path.expanduser("~")
            storage_dir = os.path.join(home, ".codex", "agent_memory")
        
        self.storage_dir = Path(storage_dir).expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.conversations_file = self.storage_dir / "conversations.json"
        self.facts_file = self.storage_dir / "facts.json"
        
        # In-memory cache to reduce file I/O
        self._conversations_cache: Optional[List[Dict]] = None
        self._facts_cache: Optional[Dict] = None
        self._cache_dirty = False
        
        self._init_storage()
    
    def _init_storage(self) -> None:
        """Initialize storage files if they don''t exist."""
        if not self.conversations_file.exists():
            self._write_json(self.conversations_file, [])
        if not self.facts_file.exists():
            self._write_json(self.facts_file, {})
    
    def _read_json(self, filepath: Path) -> Any:
        """Read JSON file with error handling."""
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted JSON in {filepath}: {e}")
            return [] if "conversation" in str(filepath) else {}
        except IOError as e:
            logger.error(f"Failed to read {filepath}: {e}")
            raise
    
    def _write_json(self, filepath: Path, data: Any) -> None:
        """Write JSON file with error handling."""
        try:
            # Write to temp file first, then rename (atomic write)
            temp_file = filepath.with_suffix('.tmp')
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(filepath)
        except IOError as e:
            logger.error(f"Failed to write {filepath}: {e}")
            raise
    
    def _get_conversations(self, use_cache: bool = True) -> List[Dict]:
        """Get conversations, optionally from cache."""
        if use_cache and self._conversations_cache is not None:
            return self._conversations_cache
        
        convs = self._read_json(self.conversations_file)
        self._conversations_cache = convs
        return convs
    
    def _save_conversations(self, conversations: List[Dict], update_cache: bool = True) -> None:
        """Save conversations to file and update cache."""
        self._write_json(self.conversations_file, conversations)
        if update_cache:
            self._conversations_cache = conversations
    
    def _get_facts(self, use_cache: bool = True) -> Dict:
        """Get facts, optionally from cache."""
        if use_cache and self._facts_cache is not None:
            return self._facts_cache
        
        facts = self._read_json(self.facts_file)
        self._facts_cache = facts
        return facts
    
    def _save_facts(self, facts: Dict, update_cache: bool = True) -> None:
        """Save facts to file and update cache."""
        self._write_json(self.facts_file, facts)
        if update_cache:
            self._facts_cache = facts
    
    def invalidate_cache(self) -> None:
        """Invalidate all caches."""
        self._conversations_cache = None
        self._facts_cache = None
    
    def create_conversation(self, name: Optional[str] = None) -> int:
        """Create a new conversation."""
        conversations = self._get_conversations()
        
        conv_id = max([c["id"] for c in conversations], default=0) + 1
        now = datetime.now().isoformat()
        
        conv = {
            "id": conv_id,
            "name": name or "Default",
            "created_at": now,
            "updated_at": now,
            "messages": []
        }
        
        conversations.append(conv)
        self._save_conversations(conversations)
        
        logger.info(f"Created conversation: {conv_id} - {name or 'Default'}")
        return conv_id
    
    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Add a message to a conversation."""
        conversations = self._get_conversations(use_cache=False)
        now = datetime.now().isoformat()
        
        for conv in conversations:
            if conv["id"] == conversation_id:
                conv["messages"].append({
                    "role": role,
                    "content": content,
                    "timestamp": now,
                    "metadata": metadata or {}
                })
                conv["updated_at"] = now
                break
        else:
            logger.warning(f"Conversation {conversation_id} not found")
            return
        
        self._save_conversations(conversations, update_cache=False)
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations."""
        conversations = self._get_conversations()
        return [
            {
                "id": c["id"],
                "name": c["name"],
                "created_at": c["created_at"],
                "updated_at": c["updated_at"]
            }
            for c in conversations
        ]
    
    def store_fact(self, key: str, value: str) -> None:
        """Store a fact in long-term memory."""
        facts = self._get_facts(use_cache=False)
        now = datetime.now().isoformat()
        
        facts[key] = {
            "value": value,
            "created_at": now,
            "updated_at": now
        }
        
        self._save_facts(facts, update_cache=False)
        logger.info(f"Stored fact: {key}")
    
    def get_fact(self, key: str) -> Optional[str]:
        """Retrieve a fact from long-term memory."""
        facts = self._get_facts()
        return facts.get(key, {}).get("value")
    
    def search_facts(self, query: str) -> List[Dict[str, str]]:
        """Search facts by key or value."""
        facts = self._get_facts()
        results = []
        
        query_lower = query.lower()
        for k, v in facts.items():
            if query_lower in k.lower() or query_lower in v.get("value", "").lower():
                results.append({"key": k, "value": v.get("value")})
        
        return results


class Memory:
    """Main memory class combining in-memory and persistent storage."""
    
    def __init__(self, use_persistent: bool = True, storage_dir: Optional[str] = None):
        self.in_memory = InMemoryStorage()
        self.persistent = FileStorage(storage_dir) if use_persistent else None
        self.current_conversation_id: Optional[int] = None
        
        if use_persistent:
            self.current_conversation_id = self.persistent.create_conversation("Default")
            logger.info("Memory initialized with persistent storage")
        else:
            logger.info("Memory initialized with in-memory storage only")
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Add a message to both in-memory and persistent storage."""
        msg = self.in_memory.add_message(role, content, metadata)
        
        if self.persistent and self.current_conversation_id:
            self.persistent.add_message(
                self.current_conversation_id,
                role,
                content,
                metadata
            )
        
        return msg
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get messages from in-memory storage."""
        messages = self.in_memory.get_messages(limit)
        return [{ "role": m["role"], "content": m["content"] } for m in messages]
    
    def get_context(self, max_tokens: int = 4000) -> List[Dict[str, str]]:
        """Get messages that fit within token limit."""
        messages = self.in_memory.get_messages()
        
        # Rough estimate: 4 characters per token
        max_chars = max_tokens * 4
        total_chars = sum(len(m["content"]) for m in messages)
        
        if total_chars > max_chars:
            selected = []
            chars = 0
            for msg in reversed(messages):
                if chars + len(msg["content"]) > max_chars:
                    break
                selected.insert(0, msg)
                chars += len(msg["content"])
            messages = selected
        
        return [{ "role": m["role"], "content": m["content"] } for m in messages]
    
    def remember(self, key: str, value: str) -> str:
        """Store a fact in long-term memory."""
        if self.persistent:
            self.persistent.store_fact(key, value)
            return f"Remembered: {key}"
        return "Persistent memory not enabled"
    
    def recall(self, key: Optional[str] = None, query: Optional[str] = None) -> str:
        """Recall a fact or search memories."""
        if not self.persistent:
            return "Persistent memory not enabled"
        
        if key:
            value = self.persistent.get_fact(key)
            return value if value else f"No memory found for: {key}"
        
        if query:
            results = self.persistent.search_facts(query)
            if results:
                return_string = "\n".join([r["key"] + ": " + r["value"] for r in results])
                return return_string
            return f"No memories found for: {query}"
        
        return "Please provide a key or query"
    
    def new_conversation(self, name: Optional[str] = None) -> str:
        """Start a new conversation."""
        if self.persistent:
            self.current_conversation_id = self.persistent.create_conversation(name)
        
        self.in_memory.clear()
        conv_name = name or "Default"
        logger.info(f"Started new conversation: {conv_name}")
        return f"Started new conversation: {conv_name}"
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations."""
        if self.persistent:
            return self.persistent.list_conversations()
        return []
    
    def clear(self) -> None:
        """Clear in-memory storage."""
        self.in_memory.clear()
