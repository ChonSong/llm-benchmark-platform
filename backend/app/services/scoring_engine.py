import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class ScoreResult:
    overall_score: float
    adherence_score: float
    completeness_score: float
    security_score: float
    architecture_score: float
    defensiveness_score: float
    precision_score: float
    verbosity_score: float
    breakdown: Dict[str, Any]
    issues: List[str]


class ScoringEngine:
    """Engine for scoring LLM-generated code against specific criteria."""
    
    def score_task_a_adherence(self, code: str, rules: List[Dict]) -> ScoreResult:
        """
        Score Task A: Strict Adherence (Python Rate Limiter)
        Evaluates how literally the model followed the 10 rigid rules.
        """
        issues = []
        breakdown = {}
        total_points = 0
        max_points = 100
        
        # Rule 1: Class name must be exactly TokenBucketLimiter
        if "class TokenBucketLimiter" in code:
            breakdown["class_name"] = {"passed": True, "points": 10}
            total_points += 10
        else:
            breakdown["class_name"] = {"passed": False, "points": 0}
            issues.append("Class name is not exactly 'TokenBucketLimiter'")
        
        # Rule 2: Must use time.monotonic
        if "time.monotonic" in code:
            breakdown["time_monotonic"] = {"passed": True, "points": 10}
            total_points += 10
        else:
            breakdown["time_monotonic"] = {"passed": False, "points": 0}
            issues.append("Does not use time.monotonic()")
        
        # Rule 3: Must use threading.Lock
        if "threading.Lock" in code or "Lock()" in code:
            breakdown["threading_lock"] = {"passed": True, "points": 10}
            total_points += 10
        else:
            breakdown["threading_lock"] = {"passed": False, "points": 0}
            issues.append("Does not use threading.Lock")
        
        # Rule 4: try_consume method returning tuple
        try_consume_match = re.search(r"def try_consume\s*\([^)]*\)\s*->\s*tuple", code, re.IGNORECASE)
        if try_consume_match or ("def try_consume" in code and "return " in code):
            breakdown["try_consume_signature"] = {"passed": True, "points": 10}
            total_points += 10
        else:
            breakdown["try_consume_signature"] = {"passed": False, "points": 0}
            issues.append("try_consume method signature doesn't match requirements")
        
        # Rule 5: Constructor parameters match spec
        init_match = re.search(r"def __init__\s*\(\s*self\s*,\s*capacity\s*[,:][^)]*rate", code)
        if init_match or ("def __init__" in code and "capacity" in code and "rate" in code):
            breakdown["constructor_params"] = {"passed": True, "points": 10}
            total_points += 10
        else:
            breakdown["constructor_params"] = {"passed": False, "points": 0}
            issues.append("Constructor parameters don't match specification")
        
        # Rule 6: No unrequested input validation (defensive coding penalty)
        defensive_patterns = [
            r"if\s+capacity\s*<=?\s*0",
            r"if\s+rate\s*<=?\s*0",
            r"raise\s+ValueError",
            r"raise\s+TypeError",
            r"isinstance\s*\(",
        ]
        defensive_count = sum(1 for p in defensive_patterns if re.search(p, code))
        if defensive_count == 0:
            breakdown["no_defensive_code"] = {"passed": True, "points": 15}
            total_points += 15
        else:
            penalty = min(15, defensive_count * 5)
            breakdown["no_defensive_code"] = {"passed": False, "points": 15 - penalty, "deductions": defensive_count}
            total_points += (15 - penalty)
            issues.append(f"Added {defensive_count} unrequested defensive checks")
        
        # Rule 7: Proper token bucket algorithm
        if "tokens" in code.lower() and ("refill" in code.lower() or "elapsed" in code.lower()):
            breakdown["algorithm_impl"] = {"passed": True, "points": 15}
            total_points += 15
        else:
            breakdown["algorithm_impl"] = {"passed": False, "points": 5}
            total_points += 5
            issues.append("Token bucket algorithm implementation unclear")
        
        # Rule 8: Thread safety with context manager
        if "with self" in code or "acquire" in code:
            breakdown["thread_safety"] = {"passed": True, "points": 10}
            total_points += 10
        else:
            breakdown["thread_safety"] = {"passed": False, "points": 0}
            issues.append("Thread safety implementation missing")
        
        # Rule 9: No extra methods beyond spec
        method_count = len(re.findall(r"def \w+\s*\(", code))
        expected_methods = 3  # __init__, try_consume, maybe one helper
        if method_count <= expected_methods + 1:
            breakdown["minimal_methods"] = {"passed": True, "points": 5}
            total_points += 5
        else:
            breakdown["minimal_methods"] = {"passed": False, "points": 0}
            issues.append(f"Added {method_count - expected_methods} extra methods beyond spec")
        
        # Rule 10: Clean, minimal implementation
        loc = len([l for l in code.split('\n') if l.strip() and not l.strip().startswith('#')])
        if loc <= 40:
            breakdown["minimal_loc"] = {"passed": True, "points": 5}
            total_points += 5
        else:
            breakdown["minimal_loc"] = {"passed": False, "points": 2}
            total_points += 2
            issues.append(f"Implementation is {loc} lines, expected <= 40")
        
        # Calculate qualitative scores
        defensiveness = min(100, defensive_count * 25)
        precision = total_points  # Higher adherence = higher precision
        verbosity = min(100, max(0, (loc - 30) * 3))
        
        return ScoreResult(
            overall_score=total_points,
            adherence_score=total_points,
            completeness_score=total_points * 0.8,
            security_score=100 if "Lock" in code else 50,
            architecture_score=80,
            defensiveness_score=defensiveness,
            precision_score=precision,
            verbosity_score=verbosity,
            breakdown=breakdown,
            issues=issues
        )
    
    def score_task_b_refactoring(self, code: str, original_code: str) -> ScoreResult:
        """
        Score Task B: Legacy Refactoring (TypeScript API Handler)
        Evaluates security fixes, architecture, and completeness.
        """
        issues = []
        breakdown = {}
        total_points = 0
        
        # Security checks (30 points)
        security_score = 0
        
        # Check for SQL injection fixes (parameterized queries)
        if re.search(r"\$\d+|:\w+|\?\s*,|\bprepare\b|\bparameterized\b", code, re.IGNORECASE):
            breakdown["sql_injection_fixed"] = {"passed": True, "points": 10}
            security_score += 10
        else:
            breakdown["sql_injection_fixed"] = {"passed": False, "points": 0}
            issues.append("SQL injection vulnerabilities may not be fixed")
        
        # Check for secrets handling (env vars)
        if re.search(r"process\.env\.|env\[|getenv|Environment|config\.", code, re.IGNORECASE):
            breakdown["secrets_env_vars"] = {"passed": True, "points": 10}
            security_score += 10
        else:
            breakdown["secrets_env_vars"] = {"passed": False, "points": 0}
            issues.append("Secrets should be moved to environment variables")
        
        # Check for input validation (Zod)
        if "zod" in code.lower() or "z.object" in code or "z.string" in code:
            breakdown["zod_validation"] = {"passed": True, "points": 10}
            security_score += 10
        else:
            breakdown["zod_validation"] = {"passed": False, "points": 0}
            issues.append("Zod validation not implemented")
        
        total_points += security_score
        
        # Architecture checks (30 points)
        architecture_score = 0
        
        # Service layer
        if re.search(r"class\s+\w*Service|Service\s*{|\bservice\b.*=", code, re.IGNORECASE):
            breakdown["service_layer"] = {"passed": True, "points": 10}
            architecture_score += 10
        else:
            breakdown["service_layer"] = {"passed": False, "points": 0}
            issues.append("Service layer not clearly separated")
        
        # Controller layer
        if re.search(r"class\s+\w*Controller|Controller\s*{|\bcontroller\b.*=", code, re.IGNORECASE):
            breakdown["controller_layer"] = {"passed": True, "points": 10}
            architecture_score += 10
        else:
            breakdown["controller_layer"] = {"passed": False, "points": 0}
            issues.append("Controller layer not clearly separated")
        
        # Repository layer
        if re.search(r"class\s+\w*Repository|Repository\s*{|\brepository\b.*=", code, re.IGNORECASE):
            breakdown["repository_layer"] = {"passed": True, "points": 10}
            architecture_score += 10
        else:
            breakdown["repository_layer"] = {"passed": False, "points": 0}
            issues.append("Repository layer not clearly separated")
        
        total_points += architecture_score
        
        # Completeness checks (25 points)
        completeness_score = 0
        
        # Rate limiting
        if re.search(r"rate.?limit|RateLimit|x-ratelimit|429", code, re.IGNORECASE):
            breakdown["rate_limiting"] = {"passed": True, "points": 8}
            completeness_score += 8
        else:
            breakdown["rate_limiting"] = {"passed": False, "points": 0}
            issues.append("Rate limiting not implemented")
        
        # Database transactions
        if re.search(r"transaction|BEGIN|COMMIT|ROLLBACK|\.transaction\(", code, re.IGNORECASE):
            breakdown["db_transactions"] = {"passed": True, "points": 8}
            completeness_score += 8
        else:
            breakdown["db_transactions"] = {"passed": False, "points": 0}
            issues.append("Database transactions not implemented")
        
        # Error handling
        if re.search(r"try\s*{|catch\s*\(|\.catch\(|throw\s+new", code):
            breakdown["error_handling"] = {"passed": True, "points": 9}
            completeness_score += 9
        else:
            breakdown["error_handling"] = {"passed": False, "points": 0}
            issues.append("Proper error handling not implemented")
        
        total_points += completeness_score
        
        # Backward compatibility (15 points)
        backward_score = 0
        
        # Check if old field names are supported
        if "title" in original_code.lower() and "title" in code.lower():
            breakdown["backward_compat"] = {"passed": True, "points": 15}
            backward_score += 15
        else:
            breakdown["backward_compat"] = {"passed": False, "points": 7}
            backward_score += 7
            issues.append("Backward compatibility with old field names unclear")
        
        total_points += backward_score
        
        # Calculate qualitative scores
        loc = len([l for l in code.split('\n') if l.strip()])
        original_loc = len([l for l in original_code.split('\n') if l.strip()]) if original_code else 365
        
        defensiveness = min(100, max(0, (loc - original_loc) / 2))
        precision = min(100, total_points)
        verbosity = min(100, max(0, (loc - original_loc) * 0.5))
        
        return ScoreResult(
            overall_score=total_points,
            adherence_score=total_points * 0.7,
            completeness_score=completeness_score * 4,
            security_score=security_score * 3.33,
            architecture_score=architecture_score * 3.33,
            defensiveness_score=defensiveness,
            precision_score=precision,
            verbosity_score=verbosity,
            breakdown=breakdown,
            issues=issues
        )
    
    def score_task_c_extension(self, code: str, original_code: str, mode: str = "code") -> ScoreResult:
        """
        Score Task C: System Extension (Notification System)
        Evaluates architecture adherence and completeness.
        """
        issues = []
        breakdown = {}
        total_points = 0
        
        if mode == "ask":
            # Scoring for analysis mode
            # Check if model identified patterns
            patterns_identified = 0
            
            if re.search(r"strategy|Strategy", code, re.IGNORECASE):
                patterns_identified += 1
                breakdown["strategy_pattern"] = {"passed": True, "points": 15}
            else:
                breakdown["strategy_pattern"] = {"passed": False, "points": 0}
                issues.append("Did not identify Strategy pattern")
            
            if re.search(r"observer|Observer", code, re.IGNORECASE):
                patterns_identified += 1
                breakdown["observer_pattern"] = {"passed": True, "points": 15}
            else:
                breakdown["observer_pattern"] = {"passed": False, "points": 0}
                issues.append("Did not identify Observer pattern")
            
            # Check if bugs were identified
            if re.search(r"hard.?coded|hardcoded|bug|issue|problem", code, re.IGNORECASE):
                breakdown["bugs_identified"] = {"passed": True, "points": 20}
                total_points += 20
            else:
                breakdown["bugs_identified"] = {"passed": False, "points": 0}
                issues.append("Did not identify bugs in the code")
            
            total_points += patterns_identified * 15
            
            # Architecture understanding
            if re.search(r"channel|handler|notification", code, re.IGNORECASE):
                breakdown["architecture_understanding"] = {"passed": True, "points": 25}
                total_points += 25
            else:
                breakdown["architecture_understanding"] = {"passed": False, "points": 10}
                total_points += 10
            
            # Completeness of analysis
            word_count = len(code.split())
            if word_count >= 100:
                breakdown["analysis_depth"] = {"passed": True, "points": 25}
                total_points += 25
            else:
                breakdown["analysis_depth"] = {"passed": False, "points": 10}
                total_points += 10
                issues.append("Analysis lacks depth")
            
        else:
            # Scoring for code generation mode
            # Architecture adherence (40 points)
            arch_score = 0
            
            # Check if followed existing pattern
            if re.search(r"class\s+Email(Handler|Channel|Notification)", code, re.IGNORECASE):
                breakdown["email_handler_class"] = {"passed": True, "points": 15}
                arch_score += 15
            else:
                breakdown["email_handler_class"] = {"passed": False, "points": 0}
                issues.append("Email handler class not properly named")
            
            # Check for interface/base class implementation
            if re.search(r"extends|implements|NotificationHandler|BaseHandler", code, re.IGNORECASE):
                breakdown["follows_interface"] = {"passed": True, "points": 15}
                arch_score += 15
            else:
                breakdown["follows_interface"] = {"passed": False, "points": 5}
                arch_score += 5
                issues.append("May not follow existing interface pattern")
            
            # Check for registration with system
            if re.search(r"register|addHandler|subscribe", code, re.IGNORECASE):
                breakdown["handler_registration"] = {"passed": True, "points": 10}
                arch_score += 10
            else:
                breakdown["handler_registration"] = {"passed": False, "points": 0}
                issues.append("Handler registration not implemented")
            
            total_points += arch_score
            
            # Completeness (40 points)
            complete_score = 0
            
            # Template management
            if re.search(r"template|Template|html|HTML", code, re.IGNORECASE):
                breakdown["template_management"] = {"passed": True, "points": 12}
                complete_score += 12
            else:
                breakdown["template_management"] = {"passed": False, "points": 0}
                issues.append("Template management not implemented")
            
            # Multiple recipients
            if re.search(r"recipients|to\s*:\s*\[|forEach|map\(|\.to\b", code, re.IGNORECASE):
                breakdown["multiple_recipients"] = {"passed": True, "points": 12}
                complete_score += 12
            else:
                breakdown["multiple_recipients"] = {"passed": False, "points": 0}
                issues.append("Multiple recipients not supported")
            
            # Attachment handling
            if re.search(r"attachment|Attachment|file|File", code, re.IGNORECASE):
                breakdown["attachments"] = {"passed": True, "points": 8}
                complete_score += 8
            else:
                breakdown["attachments"] = {"passed": False, "points": 0}
                issues.append("Attachment handling not implemented")
            
            # Error handling
            if re.search(r"try|catch|error|Error|throw", code, re.IGNORECASE):
                breakdown["error_handling"] = {"passed": True, "points": 8}
                complete_score += 8
            else:
                breakdown["error_handling"] = {"passed": False, "points": 0}
                issues.append("Error handling not implemented")
            
            total_points += complete_score
            
            # Code quality (20 points)
            quality_score = 0
            
            # Type annotations
            if re.search(r":\s*(string|number|boolean|void|Promise|interface|type\s+\w+)", code):
                breakdown["type_annotations"] = {"passed": True, "points": 10}
                quality_score += 10
            else:
                breakdown["type_annotations"] = {"passed": False, "points": 0}
                issues.append("Type annotations missing")
            
            # Async handling
            if re.search(r"async|await|Promise", code, re.IGNORECASE):
                breakdown["async_handling"] = {"passed": True, "points": 10}
                quality_score += 10
            else:
                breakdown["async_handling"] = {"passed": False, "points": 5}
                quality_score += 5
            
            total_points += quality_score
        
        # Calculate qualitative scores
        loc = len([l for l in code.split('\n') if l.strip()])
        
        defensiveness = 50  # Neutral for extension tasks
        precision = min(100, total_points)
        verbosity = min(100, max(0, loc - 50))
        
        return ScoreResult(
            overall_score=total_points,
            adherence_score=total_points * 0.8,
            completeness_score=total_points * 0.9,
            security_score=70,
            architecture_score=total_points * 0.85,
            defensiveness_score=defensiveness,
            precision_score=precision,
            verbosity_score=verbosity,
            breakdown=breakdown,
            issues=issues
        )
    
    def score(self, task_type: str, code: str, original_code: str = "", mode: str = "code", rules: List[Dict] = None) -> ScoreResult:
        """Main scoring method that delegates to specific task scorers."""
        if task_type == "adherence":
            return self.score_task_a_adherence(code, rules or [])
        elif task_type == "refactoring":
            return self.score_task_b_refactoring(code, original_code)
        elif task_type == "extension":
            return self.score_task_c_extension(code, original_code, mode)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
