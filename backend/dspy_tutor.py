import dspy
from typing import List, Dict, Any
from config import OLLAMA_URL, LLAMA_MODEL

class MathTutor(dspy.Signature):
    """Generate step-by-step mathematical solutions for educational purposes."""
    
    question = dspy.InputField(desc="Mathematical question or problem")
    context = dspy.InputField(desc="Relevant mathematical context or knowledge")
    grade_level = dspy.InputField(desc="Target grade level (elementary, intermediate, advanced)")
    
    reasoning = dspy.OutputField(desc="Step-by-step mathematical reasoning")
    solution = dspy.OutputField(desc="Final answer with clear explanation")
    educational_notes = dspy.OutputField(desc="Additional educational insights")

class MathKnowledgeRetriever(dspy.Signature):
    """Retrieve relevant mathematical knowledge for a given question."""
    
    question = dspy.InputField(desc="Mathematical question")
    retrieved_knowledge = dspy.OutputField(desc="Relevant mathematical concepts and formulas")

class DSPyMathAgent:
    def __init__(self):
        # Configure DSPy with Ollama
        self.lm = dspy.OllamaLocal(
            model=LLAMA_MODEL,
            base_url=OLLAMA_URL,
            max_tokens=1000
        )
        dspy.settings.configure(lm=self.lm)
        
        # Initialize modules
        self.knowledge_retriever = dspy.ChainOfThought(MathKnowledgeRetriever)
        self.math_tutor = dspy.ChainOfThought(MathTutor)
        
    def solve_problem(self, question: str, context: str = "", grade_level: str = "intermediate") -> Dict[str, Any]:
        """Solve mathematical problem with educational focus"""
        try:
            # First, retrieve relevant knowledge
            knowledge_result = self.knowledge_retriever(question=question)
            
            # Combine context with retrieved knowledge
            full_context = f"{context}\n\nRelevant Knowledge: {knowledge_result.retrieved_knowledge}"
            
            # Generate educational solution
            solution_result = self.math_tutor(
                question=question,
                context=full_context,
                grade_level=grade_level
            )
            
            return {
                "success": True,
                "reasoning": solution_result.reasoning,
                "solution": solution_result.solution,
                "educational_notes": solution_result.educational_notes,
                "retrieved_knowledge": knowledge_result.retrieved_knowledge
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "reasoning": "",
                "solution": "Unable to generate solution. Please try again.",
                "educational_notes": "",
                "retrieved_knowledge": ""
            }
    
    def format_educational_response(self, result: Dict[str, Any]) -> str:
        """Format response for educational presentation"""
        if not result["success"]:
            return f"Error: {result['error']}"
        
        formatted = f"""**Mathematical Solution:**

**Step-by-Step Reasoning:**
{result['reasoning']}

**Final Answer:**
{result['solution']}

**Educational Notes:**
{result['educational_notes']}

**Related Concepts:**
{result['retrieved_knowledge']}
"""
        return formatted