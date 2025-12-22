from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.models import TestCase


router = APIRouter()


class TestCaseCreate(BaseModel):
    name: str
    task_type: str  # adherence, refactoring, extension
    description: Optional[str] = None
    prompt: str
    input_code: Optional[str] = None
    rules: List[Dict[str, Any]] = []
    golden_output: Optional[str] = None
    scoring_config: Dict[str, Any] = {}
    mode: str = "code"


class TestCaseUpdate(BaseModel):
    description: Optional[str] = None
    prompt: Optional[str] = None
    input_code: Optional[str] = None
    rules: Optional[List[Dict[str, Any]]] = None
    golden_output: Optional[str] = None
    scoring_config: Optional[Dict[str, Any]] = None
    mode: Optional[str] = None


class TestCaseResponse(BaseModel):
    id: int
    name: str
    task_type: str
    description: Optional[str]
    prompt: str
    input_code: Optional[str]
    rules: List[Dict[str, Any]]
    golden_output: Optional[str]
    scoring_config: Dict[str, Any]
    mode: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[TestCaseResponse])
async def list_test_cases(db: AsyncSession = Depends(get_db)):
    """List all test cases."""
    result = await db.execute(select(TestCase))
    return result.scalars().all()


@router.post("/", response_model=TestCaseResponse)
async def create_test_case(data: TestCaseCreate, db: AsyncSession = Depends(get_db)):
    """Create a new test case."""
    existing = await db.execute(select(TestCase).where(TestCase.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Test case with this name already exists")
    
    test_case = TestCase(**data.model_dump())
    db.add(test_case)
    await db.commit()
    await db.refresh(test_case)
    return test_case


@router.get("/{test_case_name}", response_model=TestCaseResponse)
async def get_test_case(test_case_name: str, db: AsyncSession = Depends(get_db)):
    """Get a specific test case."""
    result = await db.execute(select(TestCase).where(TestCase.name == test_case_name))
    test_case = result.scalar_one_or_none()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    return test_case


@router.patch("/{test_case_name}", response_model=TestCaseResponse)
async def update_test_case(test_case_name: str, data: TestCaseUpdate, db: AsyncSession = Depends(get_db)):
    """Update a test case."""
    result = await db.execute(select(TestCase).where(TestCase.name == test_case_name))
    test_case = result.scalar_one_or_none()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(test_case, key, value)
    
    await db.commit()
    await db.refresh(test_case)
    return test_case


@router.delete("/{test_case_name}")
async def delete_test_case(test_case_name: str, db: AsyncSession = Depends(get_db)):
    """Delete a test case."""
    result = await db.execute(select(TestCase).where(TestCase.name == test_case_name))
    test_case = result.scalar_one_or_none()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    await db.delete(test_case)
    await db.commit()
    return {"message": "Test case deleted"}


@router.post("/seed-defaults")
async def seed_default_test_cases(db: AsyncSession = Depends(get_db)):
    """Seed the database with default test cases."""
    
    # Task A: Strict Adherence - Python Rate Limiter
    task_a = {
        "name": "rate-limiter-adherence",
        "task_type": "adherence",
        "description": "Implement a Token Bucket Rate Limiter with strict adherence to 10 rules",
        "mode": "code",
        "prompt": """Implement a Token Bucket Rate Limiter in Python with the following STRICT requirements:

You must follow these rules EXACTLY. Do not add any features, validations, or code not explicitly requested.

1. The class MUST be named exactly `TokenBucketLimiter`
2. Constructor must accept exactly two parameters: `capacity` (int) and `rate` (float, tokens per second)
3. Implement a method `try_consume(tokens: int = 1)` that returns a tuple `(bool, float)` where:
   - First element: True if tokens were consumed, False otherwise
   - Second element: Time in seconds until enough tokens will be available (0 if consumed)
4. Use `time.monotonic()` for time tracking (NOT time.time())
5. Use `threading.Lock` for thread safety
6. Tokens should refill continuously based on elapsed time
7. Do NOT add input validation (no checking if capacity > 0, rate > 0, etc.)
8. Do NOT add any methods beyond __init__ and try_consume
9. Do NOT add docstrings or comments
10. Keep the implementation minimal - under 40 lines of code

Generate ONLY the Python code, nothing else.""",
        "rules": [
            {"id": 1, "description": "Class name must be exactly TokenBucketLimiter"},
            {"id": 2, "description": "Constructor accepts capacity and rate parameters"},
            {"id": 3, "description": "try_consume returns tuple (bool, float)"},
            {"id": 4, "description": "Uses time.monotonic()"},
            {"id": 5, "description": "Uses threading.Lock"},
            {"id": 6, "description": "Continuous token refill"},
            {"id": 7, "description": "No input validation"},
            {"id": 8, "description": "Only __init__ and try_consume methods"},
            {"id": 9, "description": "No docstrings or comments"},
            {"id": 10, "description": "Under 40 lines of code"}
        ],
        "golden_output": """import time
import threading

class TokenBucketLimiter:
    def __init__(self, capacity: int, rate: float):
        self.capacity = capacity
        self.rate = rate
        self.tokens = capacity
        self.last_update = time.monotonic()
        self.lock = threading.Lock()

    def try_consume(self, tokens: int = 1) -> tuple[bool, float]:
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return (True, 0.0)
            else:
                wait_time = (tokens - self.tokens) / self.rate
                return (False, wait_time)"""
    }
    
    # Task B: Legacy Refactoring - TypeScript API Handler
    task_b = {
        "name": "typescript-refactoring",
        "task_type": "refactoring",
        "description": "Refactor a legacy TypeScript API handler with security issues",
        "mode": "code",
        "prompt": """Refactor the following legacy TypeScript API handler. The code has multiple issues:
- SQL injection vulnerabilities
- Hardcoded secrets
- Mixed naming conventions
- No input validation
- Monolithic structure

Your task:
1. Split into Service/Controller/Repository layers
2. Add Zod validation for all inputs
3. Fix SQL injection vulnerabilities (use parameterized queries)
4. Move secrets to environment variables
5. Implement proper error handling with custom error classes
6. Add rate limiting headers
7. Use database transactions where appropriate
8. Maintain backward compatibility with existing field names
9. Use consistent camelCase naming
10. Add TypeScript types (no 'any')

Generate the refactored code with all layers.""",
        "input_code": """// Legacy API Handler - user_api.ts
const mysql = require('mysql');
const API_SECRET = "sk-prod-12345-secret-key";
const DB_PASSWORD = "admin123";

const db = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: DB_PASSWORD,
  database: 'users_db'
});

export async function handleRequest(req: any, res: any) {
  const { action, user_id, userData } = req.body;
  
  if (action === 'get_user') {
    // SQL Injection vulnerability
    const query = `SELECT * FROM users WHERE id = ${user_id}`;
    db.query(query, (err: any, results: any) => {
      if (err) {
        res.status(500).json({ error: 'Database error' });
        return;
      }
      res.json(results[0]);
    });
  }
  
  if (action === 'create_user') {
    const { name, email, Title } = userData;
    // Mixed naming: Title vs title
    const query = `INSERT INTO users (name, email, title) VALUES ('${name}', '${email}', '${Title}')`;
    db.query(query, (err: any, result: any) => {
      if (err) {
        res.status(500).json({ error: 'Failed to create user' });
        return;
      }
      res.json({ id: result.insertId, success: true });
    });
  }
  
  if (action === 'update_user') {
    const { name, email } = userData;
    const query = `UPDATE users SET name = '${name}', email = '${email}' WHERE id = ${user_id}`;
    db.query(query, (err: any) => {
      if (err) {
        res.status(500).json({ error: 'Update failed' });
        return;
      }
      res.json({ success: true });
    });
  }
  
  if (action === 'delete_user') {
    const query = `DELETE FROM users WHERE id = ${user_id}`;
    db.query(query, (err: any) => {
      if (err) {
        res.status(500).json({ error: 'Delete failed' });
        return;
      }
      res.json({ success: true });
    });
  }
  
  if (action === 'search_users') {
    const { searchTerm } = userData;
    const query = `SELECT * FROM users WHERE name LIKE '%${searchTerm}%' OR email LIKE '%${searchTerm}%'`;
    db.query(query, (err: any, results: any) => {
      if (err) {
        res.status(500).json({ error: 'Search failed' });
        return;
      }
      res.json(results);
    });
  }
  
  if (action === 'bulk_update') {
    const { users } = userData;
    // No transaction handling
    for (const user of users) {
      const query = `UPDATE users SET name = '${user.name}' WHERE id = ${user.id}`;
      db.query(query);
    }
    res.json({ success: true });
  }
  
  if (action === 'verify_api_key') {
    const { apiKey } = req.headers;
    if (apiKey === API_SECRET) {
      res.json({ valid: true });
    } else {
      res.status(401).json({ valid: false });
    }
  }
}""",
        "rules": [
            {"id": 1, "description": "Service/Controller/Repository separation"},
            {"id": 2, "description": "Zod validation"},
            {"id": 3, "description": "Parameterized SQL queries"},
            {"id": 4, "description": "Environment variables for secrets"},
            {"id": 5, "description": "Custom error classes"},
            {"id": 6, "description": "Rate limiting headers"},
            {"id": 7, "description": "Database transactions"},
            {"id": 8, "description": "Backward compatibility"},
            {"id": 9, "description": "Consistent camelCase"},
            {"id": 10, "description": "No 'any' types"}
        ]
    }
    
    # Task C: System Extension - Notification System (Ask Mode)
    task_c_ask = {
        "name": "notification-system-analysis",
        "task_type": "extension",
        "description": "Analyze the notification system architecture and identify patterns/bugs",
        "mode": "ask",
        "prompt": """Analyze the following notification system code. Please:

1. Identify the design patterns used (be specific about pattern names)
2. Explain the overall architecture
3. Identify any bugs or issues in the implementation
4. Describe how new notification channels are added
5. Note any hard-coded values that should be configurable

Be thorough in your analysis.""",
        "input_code": """// notification_system.ts
interface NotificationPayload {
  recipient: string;
  message: string;
  priority: 'low' | 'medium' | 'high';
  metadata?: Record<string, any>;
}

interface NotificationHandler {
  channel: string;
  send(payload: NotificationPayload): Promise<boolean>;
}

class NotificationRegistry {
  private handlers: Map<string, NotificationHandler> = new Map();
  private observers: ((event: string, data: any) => void)[] = [];
  
  register(handler: NotificationHandler): void {
    this.handlers.set(handler.channel, handler);
    this.notify('handler_registered', { channel: handler.channel });
  }
  
  subscribe(observer: (event: string, data: any) => void): void {
    this.observers.push(observer);
  }
  
  private notify(event: string, data: any): void {
    this.observers.forEach(obs => obs(event, data));
  }
  
  async dispatch(channel: string, payload: NotificationPayload): Promise<boolean> {
    const handler = this.handlers.get(channel);
    if (!handler) {
      // BUG: Hard-coded fallback channel
      if (channel === 'email') {
        console.log('Email handler not found, skipping');
        return false;
      }
      throw new Error(`No handler for channel: ${channel}`);
    }
    
    this.notify('dispatch_start', { channel, recipient: payload.recipient });
    const result = await handler.send(payload);
    this.notify('dispatch_complete', { channel, success: result });
    return result;
  }
}

class WebhookHandler implements NotificationHandler {
  channel = 'webhook';
  private endpoint: string;
  
  constructor(endpoint: string) {
    this.endpoint = endpoint;
  }
  
  async send(payload: NotificationPayload): Promise<boolean> {
    try {
      const response = await fetch(this.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

class SMSHandler implements NotificationHandler {
  channel = 'sms';
  // BUG: Hard-coded API key
  private apiKey = 'twilio-key-12345';
  
  async send(payload: NotificationPayload): Promise<boolean> {
    // Simulated SMS sending
    console.log(`Sending SMS to ${payload.recipient}: ${payload.message}`);
    return true;
  }
}

// Usage
const registry = new NotificationRegistry();
registry.register(new WebhookHandler('https://api.example.com/webhook'));
registry.register(new SMSHandler());

registry.subscribe((event, data) => {
  console.log(`Event: ${event}`, data);
});"""
    }
    
    # Task C: System Extension - Notification System (Code Mode)
    task_c_code = {
        "name": "notification-system-extension",
        "task_type": "extension",
        "description": "Add an Email Handler to the notification system",
        "mode": "code",
        "prompt": """Based on the notification system code provided, implement an EmailHandler class that:

1. Follows the existing NotificationHandler interface
2. Mirrors the architecture of WebhookHandler and SMSHandler
3. Supports multiple recipients (comma-separated in recipient field)
4. Includes template management (HTML templates)
5. Handles attachments (array of file paths in metadata)
6. Uses environment variables for SMTP configuration
7. Implements proper error handling
8. Includes retry logic for failed sends

Generate ONLY the EmailHandler class and any supporting types/interfaces needed.""",
        "input_code": """// notification_system.ts
interface NotificationPayload {
  recipient: string;
  message: string;
  priority: 'low' | 'medium' | 'high';
  metadata?: Record<string, any>;
}

interface NotificationHandler {
  channel: string;
  send(payload: NotificationPayload): Promise<boolean>;
}

class WebhookHandler implements NotificationHandler {
  channel = 'webhook';
  private endpoint: string;
  
  constructor(endpoint: string) {
    this.endpoint = endpoint;
  }
  
  async send(payload: NotificationPayload): Promise<boolean> {
    try {
      const response = await fetch(this.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

class SMSHandler implements NotificationHandler {
  channel = 'sms';
  
  async send(payload: NotificationPayload): Promise<boolean> {
    console.log(`Sending SMS to ${payload.recipient}: ${payload.message}`);
    return true;
  }
}""",
        "rules": [
            {"id": 1, "description": "Implements NotificationHandler interface"},
            {"id": 2, "description": "Follows existing architecture"},
            {"id": 3, "description": "Multiple recipients support"},
            {"id": 4, "description": "Template management"},
            {"id": 5, "description": "Attachment handling"},
            {"id": 6, "description": "Environment variables for config"},
            {"id": 7, "description": "Error handling"},
            {"id": 8, "description": "Retry logic"}
        ]
    }
    
    test_cases = [task_a, task_b, task_c_ask, task_c_code]
    created = []
    
    for tc_data in test_cases:
        existing = await db.execute(select(TestCase).where(TestCase.name == tc_data["name"]))
        if not existing.scalar_one_or_none():
            test_case = TestCase(**tc_data)
            db.add(test_case)
            created.append(tc_data["name"])
    
    await db.commit()
    return {"message": f"Created test cases: {created}"}
