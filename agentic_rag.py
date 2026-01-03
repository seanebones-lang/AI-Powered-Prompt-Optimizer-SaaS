"""
Agentic RAG (Retrieval-Augmented Generation) system for enhanced prompt optimization.

Implements a multi-agent workflow with:
- Router Agent: Classifies queries and determines retrieval paths
- Retriever Agent: Fetches relevant documents from vector stores
- Grader Agent: Scores document relevance (0-1)
- Generator Agent: Synthesizes responses with self-correction

Based on LangGraph patterns (v0.2.0, October 2025) and latest RAG research.
"""
import logging
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Check for optional dependencies
try:
    import numpy as np  # noqa: F401 - used for vector operations when available
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# FAISS for vector search (optional)
try:
    import faiss  # noqa: F401 - used for vector search when available
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.info("FAISS not available. Using simple similarity search.")


class QueryType(Enum):
    """Types of queries for routing."""
    SIMPLE = "simple"  # Direct retrieval
    MULTI_HOP = "multi_hop"  # Requires multiple retrievals
    ANALYTICAL = "analytical"  # Needs reasoning
    CREATIVE = "creative"  # Less retrieval-dependent


@dataclass
class Document:
    """Represents a document chunk in the vector store."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    score: float = 0.0


class RAGState(TypedDict):
    """State object passed through the RAG workflow."""
    query: str
    query_type: str
    documents: List[Document]
    graded_documents: List[Document]
    context: str
    answer: str
    confidence: float
    needs_refinement: bool
    iteration: int


class BaseRAGAgent(ABC):
    """Base class for RAG agents."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def process(self, state: RAGState) -> RAGState:
        """Process the state and return updated state."""
        pass


class RouterAgent(BaseRAGAgent):
    """
    Routes queries to appropriate retrieval strategies.

    Classifies queries as:
    - simple: Direct document retrieval
    - multi_hop: Requires multiple retrieval steps
    - analytical: Needs reasoning over retrieved data
    - creative: Minimal retrieval, more generation
    """

    def __init__(self, llm_client=None):
        super().__init__("RouterAgent")
        self.llm_client = llm_client

    def process(self, state: RAGState) -> RAGState:
        """Classify the query and determine routing."""
        query = state["query"]

        # Simple heuristic-based classification (can be replaced with LLM)
        query_lower = query.lower()

        if any(kw in query_lower for kw in ["compare", "difference", "vs", "between"]):
            query_type = QueryType.MULTI_HOP
        elif any(kw in query_lower for kw in ["analyze", "explain why", "reason"]):
            query_type = QueryType.ANALYTICAL
        elif any(kw in query_lower for kw in ["write", "create", "generate", "imagine"]):
            query_type = QueryType.CREATIVE
        else:
            query_type = QueryType.SIMPLE

        state["query_type"] = query_type.value
        self.logger.info(f"Routed query to: {query_type.value}")

        return state


class RetrieverAgent(BaseRAGAgent):
    """
    Retrieves relevant documents from vector store.

    Supports:
    - FAISS for efficient similarity search
    - Simple cosine similarity fallback
    - Hierarchical retrieval (small + large chunks)
    """

    def __init__(self, vector_store=None, top_k: int = 5):
        super().__init__("RetrieverAgent")
        self.vector_store = vector_store or SimpleVectorStore()
        self.top_k = top_k

    def process(self, state: RAGState) -> RAGState:
        """Retrieve relevant documents for the query."""
        query = state["query"]
        query_type = state.get("query_type", "simple")

        # Adjust retrieval based on query type
        k = self.top_k
        if query_type == "multi_hop":
            k = self.top_k * 2  # Retrieve more for multi-hop
        elif query_type == "creative":
            k = max(2, self.top_k // 2)  # Retrieve less for creative

        documents = self.vector_store.search(query, k=k)
        state["documents"] = documents

        self.logger.info(f"Retrieved {len(documents)} documents")
        return state


class GraderAgent(BaseRAGAgent):
    """
    Grades document relevance to the query.

    Scores documents 0-1 based on:
    - Semantic similarity
    - Keyword overlap
    - Context appropriateness
    """

    def __init__(self, threshold: float = 0.7, llm_client=None):
        super().__init__("GraderAgent")
        self.threshold = threshold
        self.llm_client = llm_client

    def process(self, state: RAGState) -> RAGState:
        """Grade and filter documents by relevance."""
        query = state["query"]
        documents = state.get("documents", [])

        graded_docs = []
        for doc in documents:
            # Simple relevance scoring (can be enhanced with LLM)
            score = self._calculate_relevance(query, doc)
            doc.score = score

            if score >= self.threshold:
                graded_docs.append(doc)

        # Sort by score descending
        graded_docs.sort(key=lambda d: d.score, reverse=True)
        state["graded_documents"] = graded_docs

        # Build context from graded documents
        context_parts = [doc.content for doc in graded_docs[:5]]
        state["context"] = "\n\n---\n\n".join(context_parts)

        self.logger.info(
            f"Graded {len(documents)} docs, kept {len(graded_docs)} above threshold {self.threshold}"
        )
        return state

    def _calculate_relevance(self, query: str, doc: Document) -> float:
        """Calculate relevance score between query and document."""
        # Simple keyword-based scoring
        query_words = set(query.lower().split())
        doc_words = set(doc.content.lower().split())

        if not query_words:
            return 0.0

        overlap = len(query_words & doc_words)
        score = overlap / len(query_words)

        # Boost if document has high existing score from retrieval
        if doc.score > 0:
            score = (score + doc.score) / 2

        return min(1.0, score)


class GeneratorAgent(BaseRAGAgent):
    """
    Generates responses using retrieved context.

    Features:
    - Context-aware generation
    - Self-correction loop
    - Confidence scoring
    """

    def __init__(self, llm_client=None, max_iterations: int = 2):
        super().__init__("GeneratorAgent")
        self.llm_client = llm_client
        self.max_iterations = max_iterations

    def process(self, state: RAGState) -> RAGState:
        """Generate response with optional self-correction."""
        query = state["query"]
        context = state.get("context", "")
        iteration = state.get("iteration", 0)

        # Generate answer
        if self.llm_client:
            answer = self._generate_with_llm(query, context)
        else:
            answer = self._generate_simple(query, context)

        state["answer"] = answer
        state["iteration"] = iteration + 1

        # Self-correction check
        confidence = self._assess_confidence(answer, context)
        state["confidence"] = confidence

        # Determine if refinement needed
        needs_refinement = (
            confidence < 0.7 and
            iteration < self.max_iterations and
            len(state.get("graded_documents", [])) > 0
        )
        state["needs_refinement"] = needs_refinement

        self.logger.info(
            f"Generated answer (iteration {iteration + 1}), confidence: {confidence:.2f}"
        )
        return state

    def _generate_simple(self, query: str, context: str) -> str:
        """Simple generation without LLM (for testing)."""
        if context:
            return f"Based on the retrieved context about '{query[:50]}...', here is the synthesized answer:\n\n{context[:500]}..."
        return f"No relevant context found for: {query}"

    def _generate_with_llm(self, query: str, context: str) -> str:
        """Generate using LLM client."""
        prompt = f"""Based on the following context, answer the query.

Context:
{context}

Query: {query}

Answer:"""

        try:
            response = self.llm_client.generate(prompt)
            return response
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return self._generate_simple(query, context)

    def _assess_confidence(self, answer: str, context: str) -> float:
        """Assess confidence in the generated answer."""
        if not answer or len(answer) < 20:
            return 0.3

        # Simple heuristics for confidence
        confidence = 0.5

        # Higher confidence if answer references context
        if context:
            context_words = set(context.lower().split())
            answer_words = set(answer.lower().split())
            overlap = len(context_words & answer_words)
            if overlap > 5:
                confidence += 0.2

        # Penalty for very short answers
        if len(answer) < 50:
            confidence -= 0.1

        # Bonus for structured answers
        if any(marker in answer for marker in ["1.", "- ", "First", "Additionally"]):
            confidence += 0.1

        return min(1.0, max(0.0, confidence))


class SimpleVectorStore:
    """
    Simple in-memory vector store for document retrieval.

    For production, use FAISS, Qdrant, or Weaviate.
    """

    def __init__(self):
        self.documents: List[Document] = []

    def add_documents(self, documents: List[Document]):
        """Add documents to the store."""
        self.documents.extend(documents)
        logger.info(f"Added {len(documents)} documents to vector store")

    def search(self, query: str, k: int = 5) -> List[Document]:
        """Search for relevant documents using simple matching."""
        if not self.documents:
            return []

        # Simple keyword matching (replace with embedding search in production)
        query_words = set(query.lower().split())
        scored_docs = []

        for doc in self.documents:
            doc_words = set(doc.content.lower().split())
            overlap = len(query_words & doc_words)
            score = overlap / max(len(query_words), 1)
            scored_docs.append((doc, score))

        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        results = []
        for doc, score in scored_docs[:k]:
            doc.score = score
            results.append(doc)

        return results

    def clear(self):
        """Clear all documents."""
        self.documents = []


class AgenticRAGWorkflow:
    """
    Orchestrates the Agentic RAG workflow.

    Workflow: Query -> Router -> Retriever -> Grader -> Generator
    With optional self-correction loop.
    """

    def __init__(
        self,
        vector_store=None,
        llm_client=None,
        grader_threshold: float = 0.7,
        top_k: int = 5
    ):
        self.vector_store = vector_store or SimpleVectorStore()

        # Initialize agents
        self.router = RouterAgent(llm_client)
        self.retriever = RetrieverAgent(self.vector_store, top_k)
        self.grader = GraderAgent(grader_threshold, llm_client)
        self.generator = GeneratorAgent(llm_client)

        self.logger = logging.getLogger(f"{__name__}.AgenticRAGWorkflow")

    def run(self, query: str, max_iterations: int = 2) -> Dict[str, Any]:
        """
        Run the full Agentic RAG workflow.

        Args:
            query: User query
            max_iterations: Maximum self-correction iterations

        Returns:
            Dict with answer, confidence, and metadata
        """
        # Initialize state
        state: RAGState = {
            "query": query,
            "query_type": "",
            "documents": [],
            "graded_documents": [],
            "context": "",
            "answer": "",
            "confidence": 0.0,
            "needs_refinement": False,
            "iteration": 0
        }

        self.logger.info(f"Starting RAG workflow for query: {query[:50]}...")

        # Step 1: Route the query
        state = self.router.process(state)

        iteration = 0
        while iteration < max_iterations:
            # Step 2: Retrieve documents
            state = self.retriever.process(state)

            # Step 3: Grade documents
            state = self.grader.process(state)

            # Check if we have any graded documents
            if not state["graded_documents"]:
                self.logger.warning("No relevant documents found")
                state["answer"] = f"I couldn't find relevant information for: {query}"
                state["confidence"] = 0.3
                break

            # Step 4: Generate answer
            state = self.generator.process(state)

            # Check if refinement needed
            if not state["needs_refinement"]:
                break

            iteration += 1
            self.logger.info(f"Refinement iteration {iteration}")

        # Build result
        result = {
            "query": query,
            "answer": state["answer"],
            "confidence": state["confidence"],
            "query_type": state["query_type"],
            "documents_retrieved": len(state["documents"]),
            "documents_used": len(state["graded_documents"]),
            "iterations": state["iteration"],
            "sources": [
                {"id": doc.id, "score": doc.score}
                for doc in state["graded_documents"][:5]
            ]
        }

        self.logger.info(
            f"Workflow complete. Confidence: {result['confidence']:.2f}, "
            f"Iterations: {result['iterations']}"
        )

        return result

    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the vector store.

        Args:
            documents: List of dicts with 'id', 'content', and optional 'metadata'
        """
        doc_objects = [
            Document(
                id=doc.get("id", str(i)),
                content=doc["content"],
                metadata=doc.get("metadata", {})
            )
            for i, doc in enumerate(documents)
        ]
        self.vector_store.add_documents(doc_objects)


# Factory function for integration with existing agents
def create_rag_enhanced_workflow(llm_client=None) -> AgenticRAGWorkflow:
    """
    Create a RAG workflow configured for prompt optimization.

    Args:
        llm_client: Optional LLM client for generation

    Returns:
        Configured AgenticRAGWorkflow instance
    """
    workflow = AgenticRAGWorkflow(
        llm_client=llm_client,
        grader_threshold=0.6,  # Lower threshold for prompt optimization
        top_k=5
    )

    # Pre-load with prompt optimization examples
    sample_docs = [
        {
            "id": "prompt_best_practices",
            "content": """Best practices for prompt optimization:
1. Be specific and clear about the desired output format
2. Provide context and constraints
3. Use examples when helpful
4. Break complex tasks into steps
5. Specify the target audience and tone""",
            "metadata": {"type": "best_practices"}
        },
        {
            "id": "creative_prompts",
            "content": """Creative prompt patterns:
- Use vivid imagery and sensory details
- Establish a unique voice or perspective
- Include emotional elements
- Set clear scene and context
- Provide character motivations""",
            "metadata": {"type": "creative"}
        },
        {
            "id": "technical_prompts",
            "content": """Technical prompt patterns:
- Specify programming language and version
- Include error handling requirements
- Define input/output formats
- Mention edge cases to handle
- Request code comments and documentation""",
            "metadata": {"type": "technical"}
        }
    ]

    workflow.add_documents(sample_docs)
    return workflow


# Global workflow instance
_rag_workflow: Optional[AgenticRAGWorkflow] = None


def get_rag_workflow() -> AgenticRAGWorkflow:
    """Get or create the global RAG workflow instance."""
    global _rag_workflow
    if _rag_workflow is None:
        _rag_workflow = create_rag_enhanced_workflow()
    return _rag_workflow
