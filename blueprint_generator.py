"""
Agent Blueprint Generator
Creates comprehensive agent architecture specifications for enterprise deployment.

Generates:
- System prompts with personality and constraints
- Tool definitions and schemas
- Workflow diagrams and orchestration patterns
- Integration requirements
- Testing scenarios
- Deployment configurations
- Code exports (Python, TypeScript)
"""

import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import api_utils as grok_api

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents that can be generated."""
    CONVERSATIONAL = "conversational"  # Chat-based assistant
    TASK_EXECUTOR = "task_executor"  # Performs specific tasks
    ANALYST = "analyst"  # Data analysis and insights
    ORCHESTRATOR = "orchestrator"  # Coordinates multiple agents
    SPECIALIST = "specialist"  # Domain-specific expert
    VALIDATOR = "validator"  # Validation and quality control
    ROUTER = "router"  # Routes requests to appropriate handlers


class ToolCategory(Enum):
    """Categories of tools an agent might use."""
    DATA_ACCESS = "data_access"
    COMPUTATION = "computation"
    COMMUNICATION = "communication"
    FILE_OPERATIONS = "file_operations"
    API_INTEGRATION = "api_integration"
    WORKFLOW = "workflow"


@dataclass
class ToolDefinition:
    """Represents a tool the agent can use."""
    name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    example_usage: str
    error_handling: str


@dataclass
class WorkflowStep:
    """Represents a step in the agent workflow."""
    step_number: int
    name: str
    description: str
    input_from: Optional[str]
    output_to: Optional[str]
    tools_used: List[str]
    error_handling: str
    timeout_seconds: int


@dataclass
class IntegrationRequirement:
    """External integration requirements."""
    service: str
    purpose: str
    authentication: str
    endpoints: List[str]
    rate_limits: Optional[str]
    fallback_strategy: str


@dataclass
class TestScenario:
    """Test scenario for the agent."""
    scenario_name: str
    input: str
    expected_behavior: str
    success_criteria: List[str]
    edge_cases: List[str]


@dataclass
class AgentBlueprint:
    """Complete agent architecture specification."""
    # Metadata
    blueprint_id: str
    name: str
    version: str
    created_at: str
    agent_type: AgentType
    
    # Core Components
    system_prompt: str
    personality_traits: List[str]
    capabilities: List[str]
    constraints: List[str]
    
    # Tools & Integrations
    tools: List[ToolDefinition]
    integrations: List[IntegrationRequirement]
    
    # Workflow
    workflow_steps: List[WorkflowStep]
    orchestration_pattern: str
    
    # Configuration
    model_config: Dict[str, Any]
    context_window: int
    max_tokens: int
    temperature: float
    
    # Testing & Validation
    test_scenarios: List[TestScenario]
    validation_rules: List[str]
    
    # Deployment
    deployment_config: Dict[str, Any]
    monitoring_metrics: List[str]
    scaling_strategy: str
    
    # Documentation
    usage_examples: List[str]
    best_practices: List[str]
    known_limitations: List[str]


class BlueprintGenerator:
    """Generates comprehensive agent blueprints."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_blueprint(
        self,
        agent_description: str,
        agent_type: AgentType,
        domain: str,
        use_cases: List[str],
        constraints: Optional[List[str]] = None,
        required_integrations: Optional[List[str]] = None
    ) -> AgentBlueprint:
        """
        Generate a complete agent blueprint from high-level description.
        
        Args:
            agent_description: Natural language description of the agent
            agent_type: Type of agent to generate
            domain: Domain/industry (e.g., "healthcare", "finance")
            use_cases: List of primary use cases
            constraints: Optional constraints (e.g., "HIPAA compliant", "low latency")
            required_integrations: Optional list of required integrations
            
        Returns:
            Complete AgentBlueprint object
        """
        self.logger.info(f"Generating blueprint for {agent_type.value} agent in {domain} domain")
        
        # Generate system prompt
        system_prompt = self._generate_system_prompt(
            agent_description, agent_type, domain, use_cases, constraints
        )
        
        # Generate personality traits
        personality_traits = self._generate_personality_traits(agent_type, domain)
        
        # Generate capabilities
        capabilities = self._generate_capabilities(agent_description, use_cases)
        
        # Generate constraints
        agent_constraints = self._generate_constraints(constraints, domain)
        
        # Generate tools
        tools = self._generate_tools(use_cases, agent_type, required_integrations)
        
        # Generate integrations
        integrations = self._generate_integrations(required_integrations, domain)
        
        # Generate workflow
        workflow_steps = self._generate_workflow(use_cases, tools, agent_type)
        orchestration_pattern = self._determine_orchestration_pattern(agent_type, workflow_steps)
        
        # Generate model configuration
        model_config = self._generate_model_config(agent_type, domain)
        
        # Generate test scenarios
        test_scenarios = self._generate_test_scenarios(use_cases, agent_type)
        
        # Generate validation rules
        validation_rules = self._generate_validation_rules(domain, constraints)
        
        # Generate deployment config
        deployment_config = self._generate_deployment_config(agent_type, domain)
        
        # Generate monitoring metrics
        monitoring_metrics = self._generate_monitoring_metrics(agent_type)
        
        # Generate usage examples
        usage_examples = self._generate_usage_examples(use_cases, agent_type)
        
        # Generate best practices
        best_practices = self._generate_best_practices(agent_type, domain)
        
        # Generate known limitations
        known_limitations = self._generate_limitations(agent_type, constraints)
        
        # Create blueprint
        blueprint = AgentBlueprint(
            blueprint_id=f"bp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=self._extract_agent_name(agent_description),
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            agent_type=agent_type,
            system_prompt=system_prompt,
            personality_traits=personality_traits,
            capabilities=capabilities,
            constraints=agent_constraints,
            tools=tools,
            integrations=integrations,
            workflow_steps=workflow_steps,
            orchestration_pattern=orchestration_pattern,
            model_config=model_config,
            context_window=model_config.get("context_window", 128000),
            max_tokens=model_config.get("max_tokens", 4000),
            temperature=model_config.get("temperature", 0.4),
            test_scenarios=test_scenarios,
            validation_rules=validation_rules,
            deployment_config=deployment_config,
            monitoring_metrics=monitoring_metrics,
            scaling_strategy=self._determine_scaling_strategy(agent_type),
            usage_examples=usage_examples,
            best_practices=best_practices,
            known_limitations=known_limitations
        )
        
        return blueprint
    
    def _generate_system_prompt(
        self,
        description: str,
        agent_type: AgentType,
        domain: str,
        use_cases: List[str],
        constraints: Optional[List[str]]
    ) -> str:
        """Generate comprehensive system prompt using Grok."""
        prompt = f"""Generate a comprehensive, production-ready system prompt for an AI agent with these specifications:

Agent Description: {description}
Agent Type: {agent_type.value}
Domain: {domain}
Primary Use Cases: {', '.join(use_cases)}
Constraints: {', '.join(constraints) if constraints else 'None specified'}

The system prompt should include:
1. Clear identity and role definition
2. Core capabilities and responsibilities
3. Interaction guidelines and communication style
4. Error handling and edge case management
5. Security and privacy considerations
6. Output format specifications
7. Constraints and limitations

Make it professional, comprehensive, and production-ready. The agent should identify as "NextEleven AI - [Agent Name]"."""

        try:
            response = grok_api.generate_completion(
                prompt=prompt,
                system_prompt="You are an expert AI architect specializing in agent system design.",
                temperature=0.4,
                max_tokens=3000
            )
            return response["content"]
        except Exception as e:
            self.logger.error(f"Error generating system prompt: {str(e)}")
            return self._fallback_system_prompt(description, agent_type)
    
    def _fallback_system_prompt(self, description: str, agent_type: AgentType) -> str:
        """Fallback system prompt if API fails."""
        return f"""You are NextEleven AI - {agent_type.value.replace('_', ' ').title()} Agent.

{description}

Your core responsibilities:
- Understand user requests thoroughly
- Execute tasks accurately and efficiently
- Provide clear, actionable responses
- Handle errors gracefully
- Maintain context throughout conversations

Guidelines:
- Always be professional and helpful
- Ask for clarification when needed
- Explain your reasoning when appropriate
- Respect user privacy and data security
- Stay within your defined capabilities"""
    
    def _generate_personality_traits(self, agent_type: AgentType, domain: str) -> List[str]:
        """Generate appropriate personality traits for the agent."""
        base_traits = {
            AgentType.CONVERSATIONAL: ["friendly", "patient", "empathetic", "clear communicator"],
            AgentType.TASK_EXECUTOR: ["efficient", "precise", "reliable", "detail-oriented"],
            AgentType.ANALYST: ["analytical", "thorough", "objective", "insightful"],
            AgentType.ORCHESTRATOR: ["organized", "strategic", "coordinated", "decisive"],
            AgentType.SPECIALIST: ["expert", "knowledgeable", "authoritative", "precise"],
            AgentType.VALIDATOR: ["meticulous", "critical", "thorough", "unbiased"],
            AgentType.ROUTER: ["intelligent", "efficient", "accurate", "responsive"]
        }
        
        traits = base_traits.get(agent_type, ["professional", "helpful", "reliable"])
        
        # Add domain-specific traits
        if domain.lower() in ["healthcare", "medical"]:
            traits.extend(["compassionate", "careful", "compliant"])
        elif domain.lower() in ["finance", "banking"]:
            traits.extend(["trustworthy", "secure", "compliant"])
        elif domain.lower() in ["education", "training"]:
            traits.extend(["patient", "encouraging", "adaptive"])
        
        return traits
    
    def _generate_capabilities(self, description: str, use_cases: List[str]) -> List[str]:
        """Extract and generate agent capabilities."""
        capabilities = []
        
        # Extract from use cases
        for use_case in use_cases:
            if "analyze" in use_case.lower():
                capabilities.append("Data analysis and interpretation")
            if "generate" in use_case.lower() or "create" in use_case.lower():
                capabilities.append("Content generation")
            if "search" in use_case.lower() or "find" in use_case.lower():
                capabilities.append("Information retrieval")
            if "validate" in use_case.lower() or "verify" in use_case.lower():
                capabilities.append("Validation and verification")
            if "recommend" in use_case.lower() or "suggest" in use_case.lower():
                capabilities.append("Recommendations and suggestions")
        
        # Add common capabilities
        capabilities.extend([
            "Natural language understanding",
            "Context retention across conversations",
            "Error detection and recovery",
            "Multi-step reasoning"
        ])
        
        return list(set(capabilities))  # Remove duplicates
    
    def _generate_constraints(self, constraints: Optional[List[str]], domain: str) -> List[str]:
        """Generate agent constraints and limitations."""
        agent_constraints = constraints or []
        
        # Add domain-specific constraints
        if domain.lower() in ["healthcare", "medical"]:
            agent_constraints.extend([
                "Must comply with HIPAA regulations",
                "Cannot provide medical diagnoses",
                "Must maintain patient confidentiality"
            ])
        elif domain.lower() in ["finance", "banking"]:
            agent_constraints.extend([
                "Must comply with financial regulations",
                "Cannot provide financial advice without disclaimers",
                "Must ensure data encryption"
            ])
        
        # Add common constraints
        agent_constraints.extend([
            "Must respect user privacy",
            "Cannot access unauthorized data",
            "Must handle errors gracefully",
            "Should acknowledge uncertainty"
        ])
        
        return list(set(agent_constraints))
    
    def _generate_tools(
        self,
        use_cases: List[str],
        agent_type: AgentType,
        required_integrations: Optional[List[str]]
    ) -> List[ToolDefinition]:
        """Generate tool definitions based on use cases."""
        tools = []
        
        # Common tools for all agents
        tools.append(ToolDefinition(
            name="log_event",
            description="Log important events and actions for monitoring",
            category=ToolCategory.WORKFLOW,
            parameters={
                "event_type": "string",
                "message": "string",
                "severity": "string (info|warning|error)"
            },
            returns={"success": "boolean"},
            example_usage='log_event("user_query", "Processing user request", "info")',
            error_handling="Returns false on failure, continues execution"
        ))
        
        # Add tools based on use cases
        if any("search" in uc.lower() or "find" in uc.lower() for uc in use_cases):
            tools.append(ToolDefinition(
                name="search_knowledge_base",
                description="Search internal knowledge base for relevant information",
                category=ToolCategory.DATA_ACCESS,
                parameters={
                    "query": "string",
                    "limit": "integer",
                    "filters": "object (optional)"
                },
                returns={"results": "array of documents", "count": "integer"},
                example_usage='search_knowledge_base("customer policies", limit=5)',
                error_handling="Returns empty results on failure, logs error"
            ))
        
        if any("analyze" in uc.lower() for uc in use_cases):
            tools.append(ToolDefinition(
                name="analyze_data",
                description="Perform statistical analysis on provided data",
                category=ToolCategory.COMPUTATION,
                parameters={
                    "data": "array or object",
                    "analysis_type": "string (summary|trend|correlation)",
                    "options": "object (optional)"
                },
                returns={"analysis": "object", "insights": "array"},
                example_usage='analyze_data(sales_data, "trend", {"period": "monthly"})',
                error_handling="Returns error object with details, suggests alternatives"
            ))
        
        if any("send" in uc.lower() or "notify" in uc.lower() for uc in use_cases):
            tools.append(ToolDefinition(
                name="send_notification",
                description="Send notifications to users or systems",
                category=ToolCategory.COMMUNICATION,
                parameters={
                    "recipient": "string",
                    "message": "string",
                    "channel": "string (email|slack|webhook)",
                    "priority": "string (low|medium|high)"
                },
                returns={"sent": "boolean", "message_id": "string"},
                example_usage='send_notification("user@example.com", "Task completed", "email", "medium")',
                error_handling="Retries 3 times with exponential backoff, logs failure"
            ))
        
        # Add integration-specific tools
        if required_integrations:
            for integration in required_integrations:
                if integration.lower() == "database":
                    tools.append(ToolDefinition(
                        name="query_database",
                        description="Execute database queries safely",
                        category=ToolCategory.DATA_ACCESS,
                        parameters={
                            "query": "string (parameterized)",
                            "parameters": "object"
                        },
                        returns={"rows": "array", "count": "integer"},
                        example_usage='query_database("SELECT * FROM users WHERE id = ?", {"id": 123})',
                        error_handling="Validates query, prevents SQL injection, returns error on failure"
                    ))
        
        return tools
    
    def _generate_integrations(
        self,
        required_integrations: Optional[List[str]],
        domain: str
    ) -> List[IntegrationRequirement]:
        """Generate integration requirements."""
        integrations = []
        
        if not required_integrations:
            return integrations
        
        for integration in required_integrations:
            if integration.lower() == "database":
                integrations.append(IntegrationRequirement(
                    service="PostgreSQL/MySQL Database",
                    purpose="Persistent data storage and retrieval",
                    authentication="Connection string with credentials",
                    endpoints=["Read queries", "Write operations", "Transactions"],
                    rate_limits="Connection pool: 10-50 connections",
                    fallback_strategy="Cache recent queries, queue writes, alert on failure"
                ))
            elif integration.lower() == "api":
                integrations.append(IntegrationRequirement(
                    service="External REST API",
                    purpose="Third-party service integration",
                    authentication="API key or OAuth 2.0",
                    endpoints=["GET /resource", "POST /resource", "PUT /resource"],
                    rate_limits="100 requests/minute",
                    fallback_strategy="Exponential backoff, circuit breaker pattern"
                ))
            elif integration.lower() == "slack":
                integrations.append(IntegrationRequirement(
                    service="Slack Workspace",
                    purpose="Team notifications and interactions",
                    authentication="Slack Bot Token",
                    endpoints=["chat.postMessage", "conversations.list"],
                    rate_limits="Tier 3: 50+ requests/minute",
                    fallback_strategy="Queue messages, retry with backoff"
                ))
        
        return integrations
    
    def _generate_workflow(
        self,
        use_cases: List[str],
        tools: List[ToolDefinition],
        agent_type: AgentType
    ) -> List[WorkflowStep]:
        """Generate workflow steps."""
        steps = []
        
        # Step 1: Input validation
        steps.append(WorkflowStep(
            step_number=1,
            name="Input Validation",
            description="Validate and sanitize user input",
            input_from="user_request",
            output_to="validated_input",
            tools_used=["log_event"],
            error_handling="Return validation error to user with suggestions",
            timeout_seconds=5
        ))
        
        # Step 2: Context retrieval (if applicable)
        if any(t.category == ToolCategory.DATA_ACCESS for t in tools):
            steps.append(WorkflowStep(
                step_number=2,
                name="Context Retrieval",
                description="Retrieve relevant context and information",
                input_from="validated_input",
                output_to="context_data",
                tools_used=["search_knowledge_base"],
                error_handling="Continue with limited context, log warning",
                timeout_seconds=10
            ))
        
        # Step 3: Processing
        steps.append(WorkflowStep(
            step_number=len(steps) + 1,
            name="Core Processing",
            description="Execute main agent logic and reasoning",
            input_from="context_data" if len(steps) > 1 else "validated_input",
            output_to="processing_result",
            tools_used=[t.name for t in tools if t.category == ToolCategory.COMPUTATION],
            error_handling="Retry with simplified approach, return partial results",
            timeout_seconds=30
        ))
        
        # Step 4: Response generation
        steps.append(WorkflowStep(
            step_number=len(steps) + 1,
            name="Response Generation",
            description="Format and generate user-facing response",
            input_from="processing_result",
            output_to="final_response",
            tools_used=["log_event"],
            error_handling="Return generic error message, log details",
            timeout_seconds=10
        ))
        
        # Step 5: Post-processing (if needed)
        if any(t.category == ToolCategory.COMMUNICATION for t in tools):
            steps.append(WorkflowStep(
                step_number=len(steps) + 1,
                name="Notification & Logging",
                description="Send notifications and log results",
                input_from="final_response",
                output_to="completion_status",
                tools_used=["send_notification", "log_event"],
                error_handling="Log failure but don't block response",
                timeout_seconds=5
            ))
        
        return steps
    
    def _determine_orchestration_pattern(
        self,
        agent_type: AgentType,
        workflow_steps: List[WorkflowStep]
    ) -> str:
        """Determine the orchestration pattern."""
        if agent_type == AgentType.ORCHESTRATOR:
            return "Multi-Agent Coordination (Hub-and-Spoke)"
        elif len(workflow_steps) > 4:
            return "Sequential Pipeline with Parallel Sub-tasks"
        elif agent_type == AgentType.ROUTER:
            return "Dynamic Routing with Conditional Branching"
        else:
            return "Linear Sequential Processing"
    
    def _generate_model_config(self, agent_type: AgentType, domain: str) -> Dict[str, Any]:
        """Generate model configuration."""
        base_config = {
            "model": "grok-beta",
            "context_window": 131072,
            "max_tokens": 4000,
            "temperature": 0.4,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        # Adjust based on agent type
        if agent_type == AgentType.CONVERSATIONAL:
            base_config["temperature"] = 0.7
        elif agent_type in [AgentType.ANALYST, AgentType.VALIDATOR]:
            base_config["temperature"] = 0.2
        elif agent_type == AgentType.TASK_EXECUTOR:
            base_config["temperature"] = 0.3
        
        return base_config
    
    def _generate_test_scenarios(
        self,
        use_cases: List[str],
        agent_type: AgentType
    ) -> List[TestScenario]:
        """Generate test scenarios."""
        scenarios = []
        
        # Happy path scenario
        scenarios.append(TestScenario(
            scenario_name="Happy Path - Standard Request",
            input=f"Standard {use_cases[0] if use_cases else 'request'}",
            expected_behavior="Agent processes request successfully and returns appropriate response",
            success_criteria=[
                "Response is relevant and accurate",
                "Response time < 5 seconds",
                "No errors in logs"
            ],
            edge_cases=[]
        ))
        
        # Error handling scenario
        scenarios.append(TestScenario(
            scenario_name="Error Handling - Invalid Input",
            input="Invalid or malformed input data",
            expected_behavior="Agent detects invalid input and returns helpful error message",
            success_criteria=[
                "Error message is clear and actionable",
                "Agent doesn't crash or hang",
                "Appropriate error logged"
            ],
            edge_cases=["Empty input", "Extremely long input", "Special characters"]
        ))
        
        # Edge case scenario
        scenarios.append(TestScenario(
            scenario_name="Edge Case - Ambiguous Request",
            input="Ambiguous or unclear request requiring clarification",
            expected_behavior="Agent asks clarifying questions",
            success_criteria=[
                "Agent identifies ambiguity",
                "Clarifying questions are relevant",
                "Agent doesn't make assumptions"
            ],
            edge_cases=["Multiple interpretations possible", "Missing critical information"]
        ))
        
        # Load test scenario
        scenarios.append(TestScenario(
            scenario_name="Load Test - Concurrent Requests",
            input="Multiple simultaneous requests",
            expected_behavior="Agent handles concurrent requests without degradation",
            success_criteria=[
                "All requests processed successfully",
                "Response time remains acceptable",
                "No resource exhaustion"
            ],
            edge_cases=["100+ concurrent requests", "Sustained high load"]
        ))
        
        return scenarios
    
    def _generate_validation_rules(
        self,
        domain: str,
        constraints: Optional[List[str]]
    ) -> List[str]:
        """Generate validation rules."""
        rules = [
            "Input must be non-empty and within size limits",
            "Output must be properly formatted and complete",
            "Response time must be within acceptable thresholds",
            "No sensitive data in logs",
            "All errors must be handled gracefully"
        ]
        
        if domain.lower() in ["healthcare", "medical"]:
            rules.extend([
                "PHI must be encrypted at rest and in transit",
                "Access must be logged and auditable",
                "Consent must be verified before data access"
            ])
        elif domain.lower() in ["finance", "banking"]:
            rules.extend([
                "PCI DSS compliance for payment data",
                "Transaction integrity must be maintained",
                "Audit trail required for all operations"
            ])
        
        return rules
    
    def _generate_deployment_config(self, agent_type: AgentType, domain: str) -> Dict[str, Any]:
        """Generate deployment configuration."""
        return {
            "runtime": "Python 3.11+",
            "container": "Docker",
            "orchestration": "Kubernetes (optional)",
            "scaling": {
                "min_instances": 1,
                "max_instances": 10,
                "target_cpu": 70,
                "target_memory": 80
            },
            "health_check": {
                "endpoint": "/health",
                "interval_seconds": 30,
                "timeout_seconds": 5,
                "unhealthy_threshold": 3
            },
            "environment_variables": [
                "XAI_API_KEY",
                "DATABASE_URL",
                "LOG_LEVEL",
                "ENVIRONMENT"
            ],
            "secrets": [
                "API_KEYS",
                "DATABASE_CREDENTIALS",
                "ENCRYPTION_KEYS"
            ],
            "networking": {
                "ports": [8000],
                "load_balancer": True,
                "ssl_termination": True
            }
        }
    
    def _generate_monitoring_metrics(self, agent_type: AgentType) -> List[str]:
        """Generate monitoring metrics."""
        return [
            "Request rate (requests/second)",
            "Response time (p50, p95, p99)",
            "Error rate (%)",
            "Token usage (total, per request)",
            "API call latency",
            "Cache hit rate",
            "Concurrent users",
            "Memory usage",
            "CPU utilization",
            "Queue depth",
            "Success rate by use case",
            "User satisfaction score"
        ]
    
    def _determine_scaling_strategy(self, agent_type: AgentType) -> str:
        """Determine scaling strategy."""
        if agent_type == AgentType.ORCHESTRATOR:
            return "Horizontal scaling with load balancing and request queuing"
        elif agent_type in [AgentType.ANALYST, AgentType.TASK_EXECUTOR]:
            return "Auto-scaling based on queue depth and CPU utilization"
        else:
            return "Horizontal scaling with session affinity"
    
    def _generate_usage_examples(self, use_cases: List[str], agent_type: AgentType) -> List[str]:
        """Generate usage examples."""
        examples = []
        
        for use_case in use_cases[:3]:  # Top 3 use cases
            examples.append(f"""
Example: {use_case}

Input:
```
{self._generate_example_input(use_case)}
```

Expected Output:
```
{self._generate_example_output(use_case, agent_type)}
```
""")
        
        return examples
    
    def _generate_example_input(self, use_case: str) -> str:
        """Generate example input for a use case."""
        return f"User request related to: {use_case}"
    
    def _generate_example_output(self, use_case: str, agent_type: AgentType) -> str:
        """Generate example output for a use case."""
        return f"Agent response addressing: {use_case}"
    
    def _generate_best_practices(self, agent_type: AgentType, domain: str) -> List[str]:
        """Generate best practices."""
        practices = [
            "Always validate input before processing",
            "Implement proper error handling and recovery",
            "Log all important events and errors",
            "Use caching to reduce API calls",
            "Implement rate limiting to prevent abuse",
            "Monitor performance and set up alerts",
            "Keep system prompts updated and tested",
            "Regularly review and update test scenarios",
            "Implement gradual rollouts for changes",
            "Maintain comprehensive documentation"
        ]
        
        if domain.lower() in ["healthcare", "medical", "finance", "banking"]:
            practices.extend([
                "Ensure compliance with industry regulations",
                "Implement strong authentication and authorization",
                "Encrypt sensitive data at rest and in transit",
                "Conduct regular security audits",
                "Maintain detailed audit logs"
            ])
        
        return practices
    
    def _generate_limitations(
        self,
        agent_type: AgentType,
        constraints: Optional[List[str]]
    ) -> List[str]:
        """Generate known limitations."""
        limitations = [
            "Cannot access real-time data without integrations",
            "Limited by context window size",
            "May require clarification for ambiguous requests",
            "Performance depends on API availability",
            "Cannot execute actions outside defined tools"
        ]
        
        if agent_type == AgentType.CONVERSATIONAL:
            limitations.append("May lose context in very long conversations")
        elif agent_type == AgentType.ANALYST:
            limitations.append("Analysis quality depends on data quality")
        
        return limitations
    
    def _extract_agent_name(self, description: str) -> str:
        """Extract a suitable agent name from description."""
        # Simple extraction - take first few words
        words = description.split()[:3]
        name = " ".join(words)
        if len(name) > 50:
            name = name[:50]
        return name.strip() + " Agent"
    
    def export_to_json(self, blueprint: AgentBlueprint) -> str:
        """Export blueprint to JSON format."""
        # Convert enums and dataclasses to dicts
        def convert(obj):
            if isinstance(obj, Enum):
                return obj.value
            elif hasattr(obj, '__dict__'):
                return {k: convert(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [convert(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            return obj
        
        blueprint_dict = convert(blueprint)
        return json.dumps(blueprint_dict, indent=2)
    
    def export_to_python(self, blueprint: AgentBlueprint) -> str:
        """Export blueprint as executable Python code."""
        code = f'''"""
{blueprint.name}
Generated by NextEleven AI Blueprint Generator
Version: {blueprint.version}
Created: {blueprint.created_at}
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class {blueprint.name.replace(" ", "")}:
    """
    {blueprint.agent_type.value.replace("_", " ").title()} Agent
    
    Capabilities:
{chr(10).join(f"    - {cap}" for cap in blueprint.capabilities)}
    
    Constraints:
{chr(10).join(f"    - {const}" for const in blueprint.constraints)}
    """
    
    def __init__(self):
        self.name = "{blueprint.name}"
        self.version = "{blueprint.version}"
        self.system_prompt = """
{blueprint.system_prompt}
        """
        self.config = {blueprint.model_config}
        self.logger = logging.getLogger(__name__)
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input through the agent workflow.
        
        Args:
            user_input: User's request or query
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Step 1: Validate input
            validated_input = self._validate_input(user_input)
            
            # Step 2: Retrieve context (if needed)
            context = self._retrieve_context(validated_input)
            
            # Step 3: Process with AI
            result = self._process_with_ai(validated_input, context)
            
            # Step 4: Format response
            response = self._format_response(result)
            
            return {{
                "success": True,
                "response": response,
                "metadata": {{
                    "agent": self.name,
                    "version": self.version
                }}
            }}
        except Exception as e:
            self.logger.error(f"Error processing request: {{str(e)}}")
            return {{
                "success": False,
                "error": str(e),
                "response": "I encountered an error processing your request."
            }}
    
    def _validate_input(self, user_input: str) -> str:
        """Validate and sanitize user input."""
        if not user_input or not user_input.strip():
            raise ValueError("Input cannot be empty")
        return user_input.strip()
    
    def _retrieve_context(self, validated_input: str) -> Dict[str, Any]:
        """Retrieve relevant context for processing."""
        # Implement context retrieval logic
        return {{"context": "relevant information"}}
    
    def _process_with_ai(self, user_input: str, context: Dict[str, Any]) -> str:
        """Process input with AI model."""
        # Implement AI processing logic
        # This would typically call your AI API (Grok, Claude, etc.)
        return "AI generated response"
    
    def _format_response(self, result: str) -> str:
        """Format the final response."""
        return result


# Tools
{self._generate_tool_code(blueprint.tools)}


# Usage Example
if __name__ == "__main__":
    agent = {blueprint.name.replace(" ", "")}()
    
    # Example usage
    result = agent.process("Your query here")
    print(result)
'''
        return code
    
    def _generate_tool_code(self, tools: List[ToolDefinition]) -> str:
        """Generate Python code for tools."""
        if not tools:
            return "# No tools defined"
        
        code_parts = []
        for tool in tools[:3]:  # First 3 tools as examples
            code_parts.append(f'''
def {tool.name}({", ".join(tool.parameters.keys())}):
    """
    {tool.description}
    
    Example: {tool.example_usage}
    """
    # Implement tool logic here
    pass
''')
        
        return "\n".join(code_parts)
    
    def export_to_markdown(self, blueprint: AgentBlueprint) -> str:
        """Export blueprint as comprehensive markdown documentation."""
        md = f"""# {blueprint.name}

**Version:** {blueprint.version}  
**Type:** {blueprint.agent_type.value.replace('_', ' ').title()}  
**Created:** {blueprint.created_at}  
**Blueprint ID:** {blueprint.blueprint_id}

---

## Overview

{blueprint.system_prompt[:500]}...

### Personality Traits
{chr(10).join(f"- {trait}" for trait in blueprint.personality_traits)}

### Core Capabilities
{chr(10).join(f"- {cap}" for cap in blueprint.capabilities)}

### Constraints
{chr(10).join(f"- {const}" for const in blueprint.constraints)}

---

## Architecture

### Orchestration Pattern
{blueprint.orchestration_pattern}

### Workflow Steps

{chr(10).join(f'''
#### Step {step.step_number}: {step.name}
- **Description:** {step.description}
- **Input:** {step.input_from}
- **Output:** {step.output_to}
- **Tools Used:** {", ".join(step.tools_used)}
- **Timeout:** {step.timeout_seconds}s
- **Error Handling:** {step.error_handling}
''' for step in blueprint.workflow_steps)}

---

## Tools & Integrations

### Available Tools

{chr(10).join(f'''
#### {tool.name}
- **Category:** {tool.category.value}
- **Description:** {tool.description}
- **Parameters:** {json.dumps(tool.parameters, indent=2)}
- **Returns:** {json.dumps(tool.returns, indent=2)}
- **Example:** `{tool.example_usage}`
- **Error Handling:** {tool.error_handling}
''' for tool in blueprint.tools)}

### Required Integrations

{chr(10).join(f'''
#### {integration.service}
- **Purpose:** {integration.purpose}
- **Authentication:** {integration.authentication}
- **Rate Limits:** {integration.rate_limits}
- **Fallback:** {integration.fallback_strategy}
''' for integration in blueprint.integrations) if blueprint.integrations else "No external integrations required"}

---

## Configuration

### Model Configuration
```json
{json.dumps(blueprint.model_config, indent=2)}
```

### Deployment Configuration
```json
{json.dumps(blueprint.deployment_config, indent=2)}
```

---

## Testing

### Test Scenarios

{chr(10).join(f'''
#### {scenario.scenario_name}
- **Input:** {scenario.input}
- **Expected Behavior:** {scenario.expected_behavior}
- **Success Criteria:**
{chr(10).join(f"  - {criterion}" for criterion in scenario.success_criteria)}
- **Edge Cases:** {", ".join(scenario.edge_cases)}
''' for scenario in blueprint.test_scenarios)}

### Validation Rules
{chr(10).join(f"- {rule}" for rule in blueprint.validation_rules)}

---

## Monitoring & Operations

### Key Metrics
{chr(10).join(f"- {metric}" for metric in blueprint.monitoring_metrics)}

### Scaling Strategy
{blueprint.scaling_strategy}

---

## Usage Examples

{chr(10).join(blueprint.usage_examples)}

---

## Best Practices

{chr(10).join(f"{i+1}. {practice}" for i, practice in enumerate(blueprint.best_practices))}

---

## Known Limitations

{chr(10).join(f"- {limitation}" for limitation in blueprint.known_limitations)}

---

## Maintenance

- Review and update system prompt quarterly
- Monitor performance metrics weekly
- Update test scenarios as new edge cases are discovered
- Keep dependencies up to date
- Conduct security audits regularly

---

*Generated by NextEleven AI Blueprint Generator*
"""
        return md


# Convenience function
def generate_agent_blueprint(
    description: str,
    agent_type: str,
    domain: str,
    use_cases: List[str],
    **kwargs
) -> AgentBlueprint:
    """
    Convenience function to generate an agent blueprint.
    
    Args:
        description: Natural language description of the agent
        agent_type: Type of agent (conversational, task_executor, etc.)
        domain: Domain/industry
        use_cases: List of primary use cases
        **kwargs: Additional options (constraints, required_integrations)
        
    Returns:
        Complete AgentBlueprint object
    """
    generator = BlueprintGenerator()
    agent_type_enum = AgentType(agent_type.lower())
    
    return generator.generate_blueprint(
        agent_description=description,
        agent_type=agent_type_enum,
        domain=domain,
        use_cases=use_cases,
        constraints=kwargs.get('constraints'),
        required_integrations=kwargs.get('required_integrations')
    )
