"""
Self-Reflection Module - Continuous Learning and Quality Assessment
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

@dataclass
class ReflectionResult:
    """Result of self-reflection analysis"""
    confidence_score: float
    quality_assessment: str
    improvement_suggestions: List[str]
    compliance_assessment: str
    accuracy_score: float
    completeness_score: float
    clarity_score: float
    notes: str
    learning_points: List[str]
    escalation_recommended: bool

class SelfReflectionModule:
    """
    Advanced self-reflection module for continuous learning and quality improvement
    """
    
    def __init__(self, llm: ChatOpenAI, config: Dict[str, Any]):
        self.llm = llm
        self.config = config
        self.logger = logging.getLogger('SelfReflectionModule')
        
        # Reflection prompts
        self.reflection_prompt = self._create_reflection_prompt()
        
        # Quality metrics tracking
        self.quality_history = []
        self.learning_database = []
        
    def _create_reflection_prompt(self) -> str:
        """Create system prompt for self-reflection"""
        return """You are an expert quality assessment and self-reflection module for a banking AI agent. Your role is to evaluate the quality of responses and identify areas for improvement.

EVALUATION CRITERIA:
1. Accuracy: Is the information provided correct and up-to-date?
2. Completeness: Does the response fully address the customer's query?
3. Clarity: Is the response clear, well-structured, and easy to understand?
4. Compliance: Does the response meet banking regulations and compliance requirements?
5. Helpfulness: Does the response provide actionable guidance to the customer?
6. Security: Are appropriate security measures and warnings included?

ASSESSMENT FRAMEWORK:
- Confidence Score (0-1): Overall confidence in response quality
- Quality Scores (0-1): Individual scores for accuracy, completeness, clarity
- Compliance Assessment: Regulatory compliance evaluation
- Improvement Suggestions: Specific recommendations for enhancement
- Learning Points: Key insights for future interactions
- Escalation Assessment: Whether human intervention is recommended

REFLECTION PRINCIPLES:
- Be objective and constructive in assessments
- Focus on customer value and safety
- Consider regulatory and compliance requirements
- Identify patterns for systematic improvement
- Recommend escalation when appropriate

OUTPUT FORMAT:
Provide a comprehensive assessment including:
- Numerical scores for each quality dimension
- Detailed qualitative assessment
- Specific improvement recommendations
- Compliance evaluation
- Learning insights
- Escalation recommendation

Be thorough but concise in your evaluation."""

    async def reflect_on_response(self,
                                query: str,
                                response: str,
                                plan: Any,
                                context: Optional[Dict[str, Any]] = None) -> ReflectionResult:
        """
        Perform comprehensive reflection on agent response
        """
        try:
            self.logger.info("Performing self-reflection on response")
            
            # Prepare context information
            context_info = ""
            if context:
                context_info = f"Context: {json.dumps(context, indent=2)}"
            
            plan_info = ""
            if plan:
                plan_info = f"Execution Plan: {getattr(plan, 'plan_id', 'unknown')} with {len(getattr(plan, 'steps', []))} steps"
            
            # Create reflection messages
            messages = [
                SystemMessage(content=self.reflection_prompt),
                HumanMessage(content=f"""
                Evaluate this banking AI agent interaction:
                
                Customer Query: {query}
                
                Agent Response: {response}
                
                {plan_info}
                {context_info}
                
                Provide a comprehensive quality assessment including:
                1. Confidence score (0-1) for overall response quality
                2. Individual scores for accuracy, completeness, clarity (0-1 each)
                3. Compliance assessment and any regulatory concerns
                4. Specific improvement suggestions
                5. Key learning points for future interactions
                6. Recommendation for human escalation if needed
                
                Focus on banking-specific quality criteria including security, compliance, and customer service excellence.
                """)
            ]
            
            # Get reflection from LLM
            reflection_response = await self.llm.ainvoke(messages)
            
            # Parse reflection result
            reflection_result = self._parse_reflection_response(reflection_response.content)
            
            # Store reflection for learning
            await self._store_reflection(query, response, reflection_result)
            
            self.logger.info(f"Reflection completed with confidence score: {reflection_result.confidence_score}")
            return reflection_result
            
        except Exception as e:
            self.logger.error(f"Error in self-reflection: {str(e)}")
            return self._create_fallback_reflection()
    
    def _parse_reflection_response(self, response: str) -> ReflectionResult:
        """Parse LLM reflection response into structured result"""
        try:
            # Try to extract structured data from response
            lines = response.split('\n')
            
            # Initialize default values
            confidence_score = 0.7
            accuracy_score = 0.7
            completeness_score = 0.7
            clarity_score = 0.7
            quality_assessment = "Standard response quality"
            compliance_assessment = "Compliant"
            improvement_suggestions = []
            learning_points = []
            escalation_recommended = False
            
            # Parse response for key metrics
            for line in lines:
                line = line.strip().lower()
                
                # Extract confidence score
                if 'confidence' in line and any(char.isdigit() for char in line):
                    try:
                        # Extract number from line
                        numbers = [float(s) for s in line.split() if s.replace('.', '').isdigit()]
                        if numbers:
                            score = numbers[0]
                            if score > 1:  # Convert percentage to decimal
                                score = score / 100
                            confidence_score = min(max(score, 0), 1)
                    except:
                        pass
                
                # Extract quality scores
                if 'accuracy' in line and any(char.isdigit() for char in line):
                    try:
                        numbers = [float(s) for s in line.split() if s.replace('.', '').isdigit()]
                        if numbers:
                            score = numbers[0]
                            if score > 1:
                                score = score / 100
                            accuracy_score = min(max(score, 0), 1)
                    except:
                        pass
                
                if 'completeness' in line and any(char.isdigit() for char in line):
                    try:
                        numbers = [float(s) for s in line.split() if s.replace('.', '').isdigit()]
                        if numbers:
                            score = numbers[0]
                            if score > 1:
                                score = score / 100
                            completeness_score = min(max(score, 0), 1)
                    except:
                        pass
                
                if 'clarity' in line and any(char.isdigit() for char in line):
                    try:
                        numbers = [float(s) for s in line.split() if s.replace('.', '').isdigit()]
                        if numbers:
                            score = numbers[0]
                            if score > 1:
                                score = score / 100
                            clarity_score = min(max(score, 0), 1)
                    except:
                        pass
                
                # Check for escalation recommendation
                if any(word in line for word in ['escalate', 'human', 'transfer', 'complex']):
                    escalation_recommended = True
            
            # Extract improvement suggestions and learning points
            response_lower = response.lower()
            
            if 'improvement' in response_lower or 'suggestion' in response_lower:
                # Simple extraction of suggestions
                suggestion_lines = [line.strip() for line in lines if 
                                  line.strip().startswith('-') or line.strip().startswith('•')]
                improvement_suggestions = suggestion_lines[:5]  # Limit to 5
            
            if 'learning' in response_lower or 'insight' in response_lower:
                learning_lines = [line.strip() for line in lines if 
                                line.strip().startswith('-') or line.strip().startswith('•')]
                learning_points = learning_lines[:3]  # Limit to 3
            
            # Determine overall quality assessment
            avg_score = (accuracy_score + completeness_score + clarity_score) / 3
            if avg_score >= 0.8:
                quality_assessment = "High quality response"
            elif avg_score >= 0.6:
                quality_assessment = "Good quality response"
            elif avg_score >= 0.4:
                quality_assessment = "Acceptable quality response"
            else:
                quality_assessment = "Below standard response quality"
            
            return ReflectionResult(
                confidence_score=confidence_score,
                quality_assessment=quality_assessment,
                improvement_suggestions=improvement_suggestions,
                compliance_assessment=compliance_assessment,
                accuracy_score=accuracy_score,
                completeness_score=completeness_score,
                clarity_score=clarity_score,
                notes=response[:500],  # First 500 chars as notes
                learning_points=learning_points,
                escalation_recommended=escalation_recommended
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing reflection response: {str(e)}")
            return self._create_fallback_reflection()
    
    def _create_fallback_reflection(self) -> ReflectionResult:
        """Create fallback reflection when parsing fails"""
        return ReflectionResult(
            confidence_score=0.5,
            quality_assessment="Unable to assess quality",
            improvement_suggestions=["Review response generation process"],
            compliance_assessment="Unknown",
            accuracy_score=0.5,
            completeness_score=0.5,
            clarity_score=0.5,
            notes="Reflection analysis failed",
            learning_points=["Improve reflection system reliability"],
            escalation_recommended=True
        )
    
    async def _store_reflection(self, query: str, response: str, reflection: ReflectionResult):
        """Store reflection result for learning and analysis"""
        try:
            reflection_record = {
                'timestamp': datetime.now().isoformat(),
                'query': query[:200],  # Truncate for storage
                'response': response[:500],  # Truncate for storage
                'confidence_score': reflection.confidence_score,
                'quality_assessment': reflection.quality_assessment,
                'accuracy_score': reflection.accuracy_score,
                'completeness_score': reflection.completeness_score,
                'clarity_score': reflection.clarity_score,
                'compliance_assessment': reflection.compliance_assessment,
                'improvement_suggestions': reflection.improvement_suggestions,
                'learning_points': reflection.learning_points,
                'escalation_recommended': reflection.escalation_recommended
            }
            
            # Add to quality history
            self.quality_history.append(reflection_record)
            
            # Keep only recent history (last 100 interactions)
            if len(self.quality_history) > 100:
                self.quality_history = self.quality_history[-100:]
            
            # Extract learning points for future reference
            for point in reflection.learning_points:
                if point not in self.learning_database:
                    self.learning_database.append(point)
            
            # Keep learning database manageable
            if len(self.learning_database) > 50:
                self.learning_database = self.learning_database[-50:]
            
        except Exception as e:
            self.logger.error(f"Error storing reflection: {str(e)}")
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get aggregated quality metrics"""
        try:
            if not self.quality_history:
                return {
                    "average_confidence": 0.0,
                    "average_accuracy": 0.0,
                    "average_completeness": 0.0,
                    "average_clarity": 0.0,
                    "total_interactions": 0,
                    "escalation_rate": 0.0
                }
            
            # Calculate averages
            total = len(self.quality_history)
            avg_confidence = sum(r['confidence_score'] for r in self.quality_history) / total
            avg_accuracy = sum(r['accuracy_score'] for r in self.quality_history) / total
            avg_completeness = sum(r['completeness_score'] for r in self.quality_history) / total
            avg_clarity = sum(r['clarity_score'] for r in self.quality_history) / total
            
            # Calculate escalation rate
            escalations = sum(1 for r in self.quality_history if r['escalation_recommended'])
            escalation_rate = escalations / total if total > 0 else 0
            
            return {
                "average_confidence": round(avg_confidence, 3),
                "average_accuracy": round(avg_accuracy, 3),
                "average_completeness": round(avg_completeness, 3),
                "average_clarity": round(avg_clarity, 3),
                "total_interactions": total,
                "escalation_rate": round(escalation_rate, 3),
                "recent_trend": self._calculate_trend()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating quality metrics: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_trend(self) -> str:
        """Calculate quality trend over recent interactions"""
        try:
            if len(self.quality_history) < 10:
                return "insufficient_data"
            
            # Compare last 5 vs previous 5 interactions
            recent_5 = self.quality_history[-5:]
            previous_5 = self.quality_history[-10:-5]
            
            recent_avg = sum(r['confidence_score'] for r in recent_5) / 5
            previous_avg = sum(r['confidence_score'] for r in previous_5) / 5
            
            if recent_avg > previous_avg + 0.05:
                return "improving"
            elif recent_avg < previous_avg - 0.05:
                return "declining"
            else:
                return "stable"
                
        except Exception:
            return "unknown"
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get learning insights and recommendations"""
        return {
            "total_learning_points": len(self.learning_database),
            "recent_learning_points": self.learning_database[-10:],
            "common_improvement_areas": self._get_common_improvements(),
            "quality_trends": self.get_quality_metrics()
        }
    
    def _get_common_improvements(self) -> List[str]:
        """Identify common improvement suggestions"""
        try:
            all_suggestions = []
            for record in self.quality_history[-20:]:  # Last 20 interactions
                all_suggestions.extend(record.get('improvement_suggestions', []))
            
            # Simple frequency counting
            suggestion_counts = {}
            for suggestion in all_suggestions:
                suggestion_lower = suggestion.lower()
                suggestion_counts[suggestion_lower] = suggestion_counts.get(suggestion_lower, 0) + 1
            
            # Return top 5 most common suggestions
            sorted_suggestions = sorted(suggestion_counts.items(), key=lambda x: x[1], reverse=True)
            return [suggestion for suggestion, count in sorted_suggestions[:5]]
            
        except Exception as e:
            self.logger.error(f"Error getting common improvements: {str(e)}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get reflection module status"""
        return {
            "module": "reflection",
            "status": "healthy",
            "quality_metrics": self.get_quality_metrics(),
            "learning_insights": {
                "total_learning_points": len(self.learning_database),
                "quality_history_size": len(self.quality_history)
            },
            "capabilities": [
                "quality_assessment",
                "continuous_learning",
                "performance_monitoring",
                "improvement_identification",
                "escalation_detection"
            ]
        }

