"""
Built-in templates for common agentic AI patterns.
Provides pre-defined prompt templates for various use cases.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Represents a built-in prompt template."""
    name: str
    template: str
    prompt_type: str
    description: str
    tags: List[str]
    category: str


# Agent Development Templates
AGENT_TEMPLATES = [
    PromptTemplate(
        name="Agentic AI System Prompt",
        template="""You are [AGENT_NAME], an AI assistant specialized in [SPECIALIZATION].

Your core capabilities:
- [CAPABILITY_1]
- [CAPABILITY_2]
- [CAPABILITY_3]

Guidelines for interaction:
- Always maintain [PERSONA_TRAIT] demeanor
- Use [COMMUNICATION_STYLE] language
- Focus on [PRIMARY_GOAL]
- Handle errors by [ERROR_HANDLING_STRATEGY]

When responding:
1. Analyze the user's request thoroughly
2. Break down complex tasks into manageable steps
3. Provide clear, actionable solutions
4. Ask for clarification when needed
5. Maintain context throughout conversations""",
        prompt_type="system_prompt",
        description="Template for creating system prompts for AI agents",
        tags=["agent", "system", "template"],
        category="agent_development"
    ),

    PromptTemplate(
        name="Agent Persona Builder",
        template="""You are [AGENT_NAME], an AI with the following characteristics:

## Personality Traits
- **Primary Trait:** [MAIN_CHARACTERISTIC]
- **Communication Style:** [FORMAL/CASUAL/TECHNICAL]
- **Expertise Level:** [NOVICE/INTERMEDIATE/EXPERT]
- **Temperament:** [HELPFUL/ASSERTIVE/ANALYTICAL]

## Background & Expertise
- **Domain:** [SPECIALIZATION_AREA]
- **Experience Level:** [YEARS_OF_EXPERIENCE_SIMULATED]
- **Key Skills:** [SKILL_1, SKILL_2, SKILL_3]

## Behavioral Guidelines
- **Approach to Problems:** [ANALYTICAL/CREATIVE/STRUCTURED]
- **Decision Making:** [DATA_DRIVEN/INTUITIVE/BALANCED]
- **Risk Tolerance:** [CONSERVATIVE/MODERATE/AGGRESSIVE]

## Interaction Preferences
- **Response Length:** [BRIEF/DETAILED/CONCISE]
- **Technical Detail Level:** [HIGH/MEDIUM/LOW]
- **Use of Examples:** [FREQUENT/OCCASIONAL/RARE]

Always stay in character and maintain consistency in your responses.""",
        prompt_type="agent_persona",
        description="Detailed agent persona and behavior template",
        tags=["agent", "persona", "behavior", "template"],
        category="agent_development"
    ),

    PromptTemplate(
        name="Multi-Agent Workflow",
        template="""# Multi-Agent System: [SYSTEM_NAME]

## System Overview
This system coordinates [NUMBER] specialized agents to accomplish [PRIMARY_GOAL].

## Agent Roles & Responsibilities

### 1. [AGENT_1_NAME] - [AGENT_1_ROLE]
**Responsibilities:**
- [RESPONSIBILITY_1]
- [RESPONSIBILITY_2]
- [RESPONSIBILITY_3]

**Inputs:** [EXPECTED_INPUTS]
**Outputs:** [PRODUCED_OUTPUTS]
**Decision Authority:** [HIGH/MEDIUM/LOW]

### 2. [AGENT_2_NAME] - [AGENT_2_ROLE]
**Responsibilities:**
- [RESPONSIBILITY_1]
- [RESPONSIBILITY_2]
- [RESPONSIBILITY_3]

**Inputs:** [EXPECTED_INPUTS]
**Outputs:** [PRODUCED_OUTPUTS]
**Decision Authority:** [HIGH/MEDIUM/LOW]

## Communication Protocol
### Message Format
```
{
  "from_agent": "agent_name",
  "to_agent": "target_agent",
  "message_type": "request|response|notification|error",
  "content": "...",
  "metadata": {
    "task_id": "uuid",
    "priority": "high|medium|low",
    "deadline": "timestamp"
  }
}
```

### Workflow States
- **INIT:** System initialization
- **PLANNING:** Task decomposition and assignment
- **EXECUTION:** Parallel agent processing
- **COORDINATION:** Inter-agent communication
- **VALIDATION:** Result verification
- **COMPLETION:** Final output delivery

## Error Handling
- **Timeout:** [TIMEOUT_SECONDS] seconds
- **Retry Policy:** [MAX_RETRIES] attempts with exponential backoff
- **Fallback Strategy:** [FALLBACK_APPROACH]
- **Monitoring:** [MONITORING_METRICS]

## Success Criteria
- [CRITERION_1]: [MEASUREMENT_METHOD]
- [CRITERION_2]: [MEASUREMENT_METHOD]
- [CRITERION_3]: [MEASUREMENT_METHOD]""",
        prompt_type="multi_agent",
        description="Template for designing multi-agent system workflows",
        tags=["multi-agent", "workflow", "coordination", "template"],
        category="agent_development"
    )
]

# Build Planning Templates
BUILD_TEMPLATES = [
    PromptTemplate(
        name="Build Plan Structure",
        template="""# Project Build Plan: [PROJECT_NAME]

## Overview
[BRIEF_PROJECT_DESCRIPTION]

## Objectives
- [OBJECTIVE_1]
- [OBJECTIVE_2]
- [OBJECTIVE_3]

## Scope & Requirements
### Functional Requirements
- [FUNCTIONAL_REQ_1]
- [FUNCTIONAL_REQ_2]

### Technical Requirements
- [TECHNICAL_REQ_1]
- [TECHNICAL_REQ_2]

### Constraints
- [CONSTRAINT_1]
- [CONSTRAINT_2]

## Architecture & Design
### System Components
- [COMPONENT_1]: [DESCRIPTION]
- [COMPONENT_2]: [DESCRIPTION]

### Data Flow
[DESCRIBE_HOW_DATA_MOVES_THROUGH_SYSTEM]

## Implementation Plan
### Phase 1: Foundation
- [TASK_1] - [ESTIMATED_TIME]
- [TASK_2] - [ESTIMATED_TIME]

### Phase 2: Core Features
- [TASK_3] - [ESTIMATED_TIME]
- [TASK_4] - [ESTIMATED_TIME]

### Phase 3: Integration & Testing
- [TASK_5] - [ESTIMATED_TIME]

## Success Metrics
- [METRIC_1]: [TARGET_VALUE]
- [METRIC_2]: [TARGET_VALUE]

## Risks & Mitigations
- [RISK_1]: [MITIGATION_STRATEGY]
- [RISK_2]: [MITIGATION_STRATEGY]""",
        prompt_type="build_plan",
        description="Comprehensive project build plan template",
        tags=["build", "planning", "project", "template"],
        category="build_planning"
    ),

    PromptTemplate(
        name="API Design Specification",
        template="""# API Design Specification: [API_NAME]

## Overview
**Purpose:** [API_PURPOSE]
**Target Audience:** [PRIMARY_USERS]
**Version:** [VERSION_NUMBER]

## Architecture
**Style:** [REST/GraphQL/gRPC]
**Authentication:** [AUTH_METHODS]
**Rate Limiting:** [RATE_LIMIT_POLICY]
**Versioning Strategy:** [VERSIONING_APPROACH]

## Endpoints

### [ENDPOINT_1]
**Method:** [HTTP_METHOD]
**Path:** [API_PATH]
**Purpose:** [ENDPOINT_PURPOSE]

**Request:**
```json
{
  "parameters": {
    "param1": "type (required/optional)",
    "param2": "type (required/optional)"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "field1": "value",
    "field2": "value"
  }
}
```

**Error Responses:**
- `400 Bad Request`: [ERROR_CONDITION]
- `401 Unauthorized`: [ERROR_CONDITION]
- `404 Not Found`: [ERROR_CONDITION]

### [ENDPOINT_2]
**Method:** [HTTP_METHOD]
**Path:** [API_PATH]
**Purpose:** [ENDPOINT_PURPOSE]

[REQUEST_RESPONSE_FORMAT]

## Data Models

### [MODEL_NAME]
```typescript
interface [ModelName] {
  id: string;
  name: string;
  createdAt: Date;
  updatedAt: Date;
  // ... other fields
}
```

## Authentication & Security
- **API Keys:** [KEY_MANAGEMENT]
- **OAuth:** [OAUTH_IMPLEMENTATION]
- **CORS:** [CORS_POLICY]
- **Input Validation:** [VALIDATION_RULES]

## Performance Requirements
- **Latency:** [MAX_RESPONSE_TIME]
- **Throughput:** [MAX_REQUESTS_PER_SECOND]
- **Availability:** [UPTIME_REQUIREMENT]

## Monitoring & Analytics
- **Metrics:** [TRACKED_METRICS]
- **Logging:** [LOG_LEVELS_AND_FORMAT]
- **Alerts:** [ALERT_CONDITIONS]""",
        prompt_type="api_design",
        description="Complete API design and specification template",
        tags=["api", "design", "specification", "template"],
        category="build_planning"
    ),

    PromptTemplate(
        name="System Architecture Design",
        template="""# System Architecture: [SYSTEM_NAME]

## System Overview
**Domain:** [BUSINESS_DOMAIN]
**Scale:** [USER_SCALE] users, [DATA_SCALE] data volume
**Criticality:** [HIGH/MEDIUM/LOW] business impact

## Architectural Principles
- [PRINCIPLE_1]: [RATIONALE]
- [PRINCIPLE_2]: [RATIONALE]
- [PRINCIPLE_3]: [RATIONALE]

## Component Architecture

### Frontend Layer
**Technology Stack:** [FRAMEWORK_LIBRARY_CHOICES]
**Responsibilities:**
- User interface and experience
- Client-side validation
- State management
- API communication

**Key Components:**
- [COMPONENT_1]: [PURPOSE]
- [COMPONENT_2]: [PURPOSE]

### Backend Layer
**Technology Stack:** [LANGUAGE_FRAMEWORK_CHOICES]
**Architecture Pattern:** [MVC/MICROSERVICES/SERVERLESS]

**Services:**
- **[SERVICE_1]**: [RESPONSIBILITIES]
  - Technology: [TECH_STACK]
  - Database: [DB_CHOICE]
  - API: [API_STYLE]

- **[SERVICE_2]**: [RESPONSIBILITIES]
  - Technology: [TECH_STACK]
  - Database: [DB_CHOICE]
  - API: [API_STYLE]

### Data Layer
**Primary Database:** [DB_TECHNOLOGY] - [RATIONALE]
**Caching:** [REDIS/MEMCACHED/NONE] - [CACHE_STRATEGY]
**Search:** [ELASTICSEARCH/SOLR/NONE] - [SEARCH_REQUIREMENTS]

**Data Models:**
- [MODEL_1]: [PURPOSE_AND_RELATIONSHIPS]
- [MODEL_2]: [PURPOSE_AND_RELATIONSHIPS]

## Infrastructure & Deployment

### Cloud Platform
**Provider:** [AWS/GCP/Azure] - [RATIONALE]
**Regions:** [PRIMARY_REGION], [BACKUP_REGION]

### Compute Resources
- **Web Servers:** [INSTANCE_TYPE] x [COUNT]
- **Application Servers:** [INSTANCE_TYPE] x [COUNT]
- **Database:** [INSTANCE_TYPE] x [COUNT]
- **Cache:** [INSTANCE_TYPE] x [COUNT]

### Networking
**Load Balancing:** [ALB/NLB/CloudFront]
**CDN:** [CloudFront/Cloudflare/Akamai]
**Security:** [WAF, DDoS protection, VPC configuration]

## Scalability & Performance

### Horizontal Scaling
- **Auto-scaling triggers:** [CPU > 70%, Request count > 1000/min]
- **Minimum instances:** [MIN_COUNT]
- **Maximum instances:** [MAX_COUNT]

### Performance Targets
- **Response Time:** [TARGET_LATENCY]ms (p95)
- **Throughput:** [TARGET_RPS] requests/second
- **Availability:** [TARGET_UPTIME]% uptime

### Caching Strategy
- **Application Level:** [REDIS/MEMCACHED] for [WHAT_DATA]
- **Database Level:** [QUERY_CACHING_STRATEGY]
- **CDN Level:** [STATIC_ASSETS, API_RESPONSES]

## Security Architecture

### Authentication & Authorization
- **Method:** [JWT/OAuth/SAML]
- **Multi-factor:** [REQUIRED/OPTIONAL/NONE]
- **Session Management:** [STRATEGY]

### Data Protection
- **Encryption at Rest:** [AES_256_ENCRYPTION]
- **Encryption in Transit:** [TLS_1_3]
- **PII Handling:** [COMPLIANCE_REQUIREMENTS]

## Monitoring & Observability

### Application Metrics
- **Business Metrics:** [USER_REGISTRATIONS, CONVERSIONS]
- **Technical Metrics:** [RESPONSE_TIME, ERROR_RATE, THROUGHPUT]
- **Infrastructure:** [CPU, MEMORY, DISK_IO]

### Logging Strategy
- **Centralized Logging:** [ELK/EFK_STACK]
- **Log Levels:** [ERROR, WARN, INFO, DEBUG]
- **Retention:** [LOG_RETENTION_PERIOD]

### Alerting
- **Critical Alerts:** [SYSTEM_DOWN, DATA_LOSS]
- **Warning Alerts:** [HIGH_LATENCY, HIGH_ERROR_RATE]
- **Info Alerts:** [DEPLOYMENT_SUCCESS, BACKUP_COMPLETED]""",
        prompt_type="architecture",
        description="Comprehensive system architecture design template",
        tags=["architecture", "system", "design", "template"],
        category="build_planning"
    )
]

# Tool Definition Templates
TOOL_TEMPLATES = [
    PromptTemplate(
        name="Tool Definition Schema",
        template="""# Tool Definition: [TOOL_NAME]

## Overview
**Purpose:** [BRIEF_DESCRIPTION]

**Category:** [TOOL_CATEGORY]

## Interface Specification

### Function Signature
```python
def [FUNCTION_NAME](
    [PARAMETER_1]: [TYPE_1],
    [PARAMETER_2]: [TYPE_2] = [DEFAULT_VALUE]
) -> [RETURN_TYPE]:
    """
    [FUNCTION_DOCSTRING]
    """
```

### Parameters
- **[PARAMETER_1]**: [DESCRIPTION] (Required: [YES/NO])
  - Type: [TYPE]
  - Validation: [VALIDATION_RULES]
  - Example: [EXAMPLE_VALUE]

- **[PARAMETER_2]**: [DESCRIPTION] (Required: [YES/NO])
  - Type: [TYPE]
  - Default: [DEFAULT_VALUE]
  - Validation: [VALIDATION_RULES]

### Return Value
- **Type:** [RETURN_TYPE]
- **Description:** [RETURN_DESCRIPTION]
- **Success Cases:** [SUCCESS_EXAMPLES]
- **Error Cases:** [ERROR_EXAMPLES]

## Error Handling
### Input Validation Errors
- [ERROR_CONDITION_1]: [ERROR_MESSAGE_AND_HANDLING]

### Runtime Errors
- [ERROR_CONDITION_2]: [ERROR_MESSAGE_AND_HANDLING]

### Recovery Strategies
- [RECOVERY_STRATEGY_1]
- [RECOVERY_STRATEGY_2]

## Usage Examples

### Basic Usage
```python
result = [FUNCTION_NAME]([EXAMPLE_ARGS])
# Returns: [EXPECTED_RESULT]
```

### Advanced Usage
```python
# [COMPLEX_USAGE_SCENARIO]
result = [FUNCTION_NAME]([ADVANCED_ARGS])
# Returns: [ADVANCED_RESULT]
```

## Integration Notes
- **Dependencies:** [REQUIRED_LIBRARIES_OR_SERVICES]
- **Compatibility:** [COMPATIBILITY_REQUIREMENTS]
- **Performance:** [PERFORMANCE_CHARACTERISTICS]
- **Security:** [SECURITY_CONSIDERATIONS]""",
        prompt_type="tool_definition",
        description="Structured template for defining tools and functions",
        tags=["tool", "api", "function", "template"],
        category="tool_definition"
    )
]

# Code & Technical Templates
CODE_TEMPLATES = [
    PromptTemplate(
        name="Code Review Guidelines",
        template="""# Code Review Guidelines for [PROJECT_NAME]

## Review Objectives
- **Quality Assurance:** Ensure code meets quality standards
- **Knowledge Sharing:** Disseminate best practices and patterns
- **Consistency:** Maintain uniform code style and architecture
- **Security:** Identify potential security vulnerabilities
- **Performance:** Optimize for speed and resource usage

## Review Checklist

### Code Quality
- [ ] **Readability:** Code is self-documenting with clear variable names
- [ ] **Structure:** Logical organization and separation of concerns
- [ ] **DRY Principle:** No unnecessary duplication
- [ ] **SOLID Principles:** Single responsibility, open/closed, etc.
- [ ] **Documentation:** Adequate comments and docstrings

### Functionality
- [ ] **Requirements:** All requirements implemented correctly
- [ ] **Edge Cases:** Handles all edge cases and error conditions
- [ ] **Input Validation:** Proper validation of all inputs
- [ ] **Output Verification:** Correct output format and content
- [ ] **Integration Points:** Works with dependent systems

### Performance
- [ ] **Algorithm Efficiency:** O(n) complexity appropriate for use case
- [ ] **Resource Usage:** Memory and CPU usage optimized
- [ ] **Database Queries:** Efficient queries with proper indexing
- [ ] **Caching:** Appropriate use of caching mechanisms
- [ ] **Scalability:** Can handle expected load increases

### Security
- [ ] **Input Sanitization:** All user inputs sanitized
- [ ] **Authentication:** Proper authentication checks
- [ ] **Authorization:** Correct permission validation
- [ ] **Data Exposure:** No sensitive data leaked
- [ ] **SQL Injection:** Parameterized queries used
- [ ] **XSS Prevention:** Output properly escaped

### Testing
- [ ] **Unit Tests:** Comprehensive unit test coverage
- [ ] **Integration Tests:** Component interaction tested
- [ ] **Edge Cases:** Unusual conditions tested
- [ ] **Error Handling:** Error conditions properly handled
- [ ] **Performance Tests:** Load and stress testing completed

## Review Process

### 1. Self-Review (Author)
- [ ] Run full test suite locally
- [ ] Check code against style guide
- [ ] Verify all requirements met
- [ ] Test edge cases manually
- [ ] Review for security issues

### 2. Peer Review (Reviewer)
- [ ] Review code for logic errors
- [ ] Check adherence to coding standards
- [ ] Verify test coverage
- [ ] Assess performance implications
- [ ] Identify potential improvements

### 3. Automated Checks
- [ ] Linting passes without errors
- [ ] Type checking passes
- [ ] Security scanning clean
- [ ] Performance benchmarks met
- [ ] Test coverage > [MINIMUM_PERCENTAGE]%

## Review Comments Template

### Issue Severity Levels
- **🔴 Blocker:** Must fix before merge (security, crashes, data loss)
- **🟡 Major:** Should fix (performance, correctness, maintainability)
- **🟢 Minor:** Nice to fix (style, documentation, optimization)
- **ℹ️ Info:** FYI or suggestion (alternative approaches)

### Comment Format
```
**[Severity] [Category]**: [Brief description]

[Location]: [file:line or function name]

[Issue]: [Detailed explanation of the problem]

[Suggestion]: [How to fix or improve]

[Impact]: [Why this matters]
```

## Common Issues & Solutions

### Performance Issues
**Problem:** Inefficient algorithm in data processing
**Solution:** Use [MORE_EFFICIENT_ALGORITHM] with O([COMPLEXITY]) complexity

### Security Issues
**Problem:** SQL injection vulnerability
**Solution:** Use parameterized queries or ORM methods

### Maintainability Issues
**Problem:** Large function with multiple responsibilities
**Solution:** Break into smaller, single-purpose functions

## Approval Criteria
- [ ] All blocker issues resolved
- [ ] All major issues addressed or justified
- [ ] Test coverage meets requirements
- [ ] No security vulnerabilities
- [ ] Performance requirements met
- [ ] Code follows established patterns

## Escalation Process
1. **Minor Issues:** Address in future refactoring
2. **Major Issues:** Fix before merge or create technical debt ticket
3. **Blocker Issues:** Must be resolved immediately
4. **Disagreements:** Escalate to senior developer or architect""",
        prompt_type="code_review",
        description="Comprehensive code review guidelines and checklist",
        tags=["code", "review", "quality", "template"],
        category="code_technical"
    )
]

# All templates combined
ALL_TEMPLATES = AGENT_TEMPLATES + BUILD_TEMPLATES + TOOL_TEMPLATES + CODE_TEMPLATES

# Template categories for UI organization
TEMPLATE_CATEGORIES = {
    "agent_development": {
        "name": "Agent Development",
        "description": "Templates for creating and configuring AI agents",
        "templates": AGENT_TEMPLATES
    },
    "build_planning": {
        "name": "Build Planning",
        "description": "Templates for project planning and architecture",
        "templates": BUILD_TEMPLATES
    },
    "tool_definition": {
        "name": "Tool Definition",
        "description": "Templates for defining tools and APIs",
        "templates": TOOL_TEMPLATES
    },
    "code_technical": {
        "name": "Code & Technical",
        "description": "Templates for code review and technical documentation",
        "templates": CODE_TEMPLATES
    }
}


def get_template_by_name(name: str) -> PromptTemplate:
    """Get a template by name."""
    for template in ALL_TEMPLATES:
        if template.name == name:
            return template
    raise ValueError(f"Template '{name}' not found")


def get_templates_by_category(category: str) -> List[PromptTemplate]:
    """Get all templates in a category."""
    if category not in TEMPLATE_CATEGORIES:
        raise ValueError(f"Category '{category}' not found")
    return TEMPLATE_CATEGORIES[category]["templates"]


def get_template_categories() -> Dict[str, Dict[str, Any]]:
    """Get all template categories with metadata."""
    return TEMPLATE_CATEGORIES


def search_templates(query: str) -> List[PromptTemplate]:
    """Search templates by name, description, or tags."""
    query_lower = query.lower()
    results = []

    for template in ALL_TEMPLATES:
        if (query_lower in template.name.lower() or
            query_lower in template.description.lower() or
            any(query_lower in tag.lower() for tag in template.tags)):
            results.append(template)

    return results