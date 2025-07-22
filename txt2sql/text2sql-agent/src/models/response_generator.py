"""
Natural Language Response Generation System for Text-to-SQL Agent

This module converts query results into natural language responses and
handles data visualization and formatting.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import pandas as pd
import numpy as np
from openai import OpenAI
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64


@dataclass
class ResponseContext:
    """Context for response generation"""
    original_question: str
    sql_query: str
    query_result: Any  # QueryResult object
    intent: str
    entities: List[str]
    user_preferences: Dict[str, Any]


@dataclass
class GeneratedResponse:
    """Generated natural language response"""
    text_response: str
    summary: str
    key_insights: List[str]
    data_table: Optional[str]  # HTML table
    visualization: Optional[str]  # Base64 encoded image
    confidence_score: float
    response_type: str
    metadata: Dict[str, Any]


class DataFormatter:
    """Formats query results for presentation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format_dataframe(self, df: pd.DataFrame, max_rows: int = 20) -> str:
        """Format DataFrame as HTML table"""
        if df is None or df.empty:
            return "<p>No data found.</p>"
        
        try:
            # Limit rows if necessary
            if len(df) > max_rows:
                df_display = df.head(max_rows)
                truncated_note = f"<p><em>Showing first {max_rows} of {len(df)} rows</em></p>"
            else:
                df_display = df
                truncated_note = ""
            
            # Format numeric columns
            df_formatted = df_display.copy()
            for col in df_formatted.columns:
                if df_formatted[col].dtype in ['float64', 'float32']:
                    # Round to 2 decimal places for currency/percentages
                    if 'price' in col.lower() or 'cost' in col.lower() or 'revenue' in col.lower():
                        df_formatted[col] = df_formatted[col].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
                    elif 'percent' in col.lower() or 'margin' in col.lower() or 'elasticity' in col.lower():
                        df_formatted[col] = df_formatted[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
                    else:
                        df_formatted[col] = df_formatted[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
                elif df_formatted[col].dtype in ['int64', 'int32']:
                    df_formatted[col] = df_formatted[col].apply(lambda x: f"{x:,}" if pd.notna(x) else "N/A")
            
            # Convert to HTML
            html_table = df_formatted.to_html(
                classes='table table-striped table-hover',
                table_id='results-table',
                escape=False,
                index=False
            )
            
            return truncated_note + html_table
            
        except Exception as e:
            self.logger.error(f"Error formatting DataFrame: {str(e)}")
            return f"<p>Error formatting data: {str(e)}</p>"
    
    def create_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create summary statistics from DataFrame"""
        if df is None or df.empty:
            return {}
        
        try:
            stats = {
                'total_rows': len(df),
                'columns': list(df.columns),
                'numeric_summaries': {}
            }
            
            # Get summaries for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                col_stats = {
                    'count': int(df[col].count()),
                    'mean': float(df[col].mean()) if df[col].count() > 0 else 0,
                    'median': float(df[col].median()) if df[col].count() > 0 else 0,
                    'min': float(df[col].min()) if df[col].count() > 0 else 0,
                    'max': float(df[col].max()) if df[col].count() > 0 else 0,
                    'std': float(df[col].std()) if df[col].count() > 1 else 0
                }
                stats['numeric_summaries'][col] = col_stats
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error creating summary stats: {str(e)}")
            return {}


class DataVisualizer:
    """Creates visualizations from query results"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Set style for better-looking plots
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def create_visualization(self, df: pd.DataFrame, intent: str, 
                           question: str) -> Optional[str]:
        """
        Create appropriate visualization based on data and intent
        
        Args:
            df: DataFrame with query results
            intent: Query intent (e.g., 'price_analysis', 'sales_analysis')
            question: Original question for context
            
        Returns:
            Base64 encoded image string or None
        """
        if df is None or df.empty or len(df) < 2:
            return None
        
        try:
            # Determine visualization type based on intent and data
            viz_type = self._determine_viz_type(df, intent, question)
            
            if viz_type == 'bar_chart':
                return self._create_bar_chart(df)
            elif viz_type == 'line_chart':
                return self._create_line_chart(df)
            elif viz_type == 'scatter_plot':
                return self._create_scatter_plot(df)
            elif viz_type == 'histogram':
                return self._create_histogram(df)
            elif viz_type == 'pie_chart':
                return self._create_pie_chart(df)
            else:
                return self._create_default_chart(df)
                
        except Exception as e:
            self.logger.error(f"Error creating visualization: {str(e)}")
            return None
    
    def _determine_viz_type(self, df: pd.DataFrame, intent: str, question: str) -> str:
        """Determine the best visualization type"""
        question_lower = question.lower()
        
        # Check for time series data
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'week' in col.lower()]
        if date_cols and len(df) > 3:
            return 'line_chart'
        
        # Check for ranking/top queries
        if any(word in question_lower for word in ['top', 'bottom', 'highest', 'lowest', 'rank']):
            return 'bar_chart'
        
        # Check for distribution analysis
        if 'distribution' in question_lower or 'histogram' in question_lower:
            return 'histogram'
        
        # Check for correlation analysis
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2 and ('correlation' in question_lower or 'relationship' in question_lower):
            return 'scatter_plot'
        
        # Check for categorical breakdown
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0 and len(df) <= 10:
            return 'pie_chart'
        
        # Default to bar chart for most cases
        return 'bar_chart'
    
    def _create_bar_chart(self, df: pd.DataFrame) -> str:
        """Create bar chart visualization"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Find best columns for x and y
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            
            # Limit to top 15 categories for readability
            if len(df) > 15:
                df_plot = df.nlargest(15, y_col)
            else:
                df_plot = df
            
            bars = ax.bar(df_plot[x_col], df_plot[y_col])
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())
            ax.set_title(f'{y_col.replace("_", " ").title()} by {x_col.replace("_", " ").title()}')
            
            # Rotate x-axis labels if they're long
            plt.xticks(rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_line_chart(self, df: pd.DataFrame) -> str:
        """Create line chart visualization"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Find date and numeric columns
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'week' in col.lower()]
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if date_cols and numeric_cols:
            date_col = date_cols[0]
            
            # Convert date column to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                df[date_col] = pd.to_datetime(df[date_col])
            
            # Sort by date
            df_sorted = df.sort_values(date_col)
            
            # Plot up to 3 numeric columns
            for i, col in enumerate(numeric_cols[:3]):
                ax.plot(df_sorted[date_col], df_sorted[col], 
                       marker='o', label=col.replace('_', ' ').title())
            
            ax.set_xlabel(date_col.replace('_', ' ').title())
            ax.set_ylabel('Value')
            ax.set_title('Trend Over Time')
            ax.legend()
            
            # Format x-axis dates
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_scatter_plot(self, df: pd.DataFrame) -> str:
        """Create scatter plot visualization"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
            scatter = ax.scatter(df[x_col], df[y_col], alpha=0.6, s=50)
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())
            ax.set_title(f'{y_col.replace("_", " ").title()} vs {x_col.replace("_", " ").title()}')
            
            # Add trend line
            z = np.polyfit(df[x_col].dropna(), df[y_col].dropna(), 1)
            p = np.poly1d(z)
            ax.plot(df[x_col], p(df[x_col]), "r--", alpha=0.8)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_histogram(self, df: pd.DataFrame) -> str:
        """Create histogram visualization"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            col = numeric_cols[0]
            ax.hist(df[col].dropna(), bins=20, alpha=0.7, edgecolor='black')
            ax.set_xlabel(col.replace('_', ' ').title())
            ax.set_ylabel('Frequency')
            ax.set_title(f'Distribution of {col.replace("_", " ").title()}')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_pie_chart(self, df: pd.DataFrame) -> str:
        """Create pie chart visualization"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        categorical_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # Group by category and sum numeric values
            grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False)
            
            # Limit to top 8 categories
            if len(grouped) > 8:
                top_categories = grouped.head(7)
                other_sum = grouped.tail(len(grouped) - 7).sum()
                top_categories['Other'] = other_sum
                grouped = top_categories
            
            wedges, texts, autotexts = ax.pie(grouped.values, labels=grouped.index, 
                                            autopct='%1.1f%%', startangle=90)
            ax.set_title(f'{num_col.replace("_", " ").title()} by {cat_col.replace("_", " ").title()}')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_default_chart(self, df: pd.DataFrame) -> str:
        """Create default visualization when type can't be determined"""
        return self._create_bar_chart(df)
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        return image_base64


class ResponseGenerator:
    """Main response generation class using GPT-4o"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Response Generator
        
        Args:
            api_key: OpenAI API key (uses environment variable if not provided)
        """
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.data_formatter = DataFormatter()
        self.data_visualizer = DataVisualizer()
        self.logger = logging.getLogger(__name__)
    
    def generate_response(self, context: ResponseContext) -> GeneratedResponse:
        """
        Generate natural language response from query results
        
        Args:
            context: ResponseContext with question, results, and metadata
            
        Returns:
            GeneratedResponse with formatted response
        """
        try:
            query_result = context.query_result
            
            if not query_result.success:
                return self._generate_error_response(context)
            
            # Format data table
            data_table = self.data_formatter.format_dataframe(query_result.data)
            
            # Create summary statistics
            summary_stats = self.data_formatter.create_summary_stats(query_result.data)
            
            # Create visualization
            visualization = self.data_visualizer.create_visualization(
                query_result.data, context.intent, context.original_question
            )
            
            # Generate natural language response
            text_response = self._generate_text_response(context, summary_stats)
            
            # Extract key insights
            key_insights = self._extract_key_insights(context, summary_stats)
            
            # Generate summary
            summary = self._generate_summary(context, summary_stats)
            
            return GeneratedResponse(
                text_response=text_response,
                summary=summary,
                key_insights=key_insights,
                data_table=data_table,
                visualization=visualization,
                confidence_score=0.9,  # High confidence for successful queries
                response_type=context.intent,
                metadata={
                    'row_count': query_result.row_count,
                    'execution_time': query_result.execution_time,
                    'cache_hit': query_result.cache_hit,
                    'summary_stats': summary_stats
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return self._generate_error_response(context, str(e))
    
    def _generate_text_response(self, context: ResponseContext, 
                              summary_stats: Dict[str, Any]) -> str:
        """Generate natural language text response using GPT-4o"""
        try:
            # Build prompt for response generation
            system_prompt = """You are an expert retail analytics assistant for Revionics. 
            Your task is to interpret query results and provide clear, actionable insights in natural language.
            
            GUIDELINES:
            1. Be conversational and professional
            2. Focus on business insights and actionable recommendations
            3. Use specific numbers and percentages from the data
            4. Explain what the results mean for business decisions
            5. Keep responses concise but informative (2-3 paragraphs max)
            6. Use retail and pricing terminology appropriately
            7. Highlight any notable patterns or anomalies
            
            CONTEXT:
            - This is a retail analytics system for pricing optimization
            - Users are typically pricing analysts, category managers, or executives
            - Focus on pricing, elasticity, margins, and competitive positioning insights"""
            
            # Prepare data summary for the prompt
            data_summary = self._prepare_data_summary(context, summary_stats)
            
            user_prompt = f"""
            ORIGINAL QUESTION: {context.original_question}
            
            QUERY RESULTS SUMMARY:
            {data_summary}
            
            SQL QUERY EXECUTED:
            {context.sql_query}
            
            Please provide a natural language response that:
            1. Directly answers the user's question
            2. Highlights key findings from the data
            3. Provides business context and implications
            4. Suggests any relevant follow-up actions or considerations
            
            Keep the response professional, concise, and focused on actionable insights."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Low temperature for consistent, factual responses
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating text response: {str(e)}")
            return f"I found {summary_stats.get('total_rows', 0)} results for your query. The data shows various insights related to your question about {context.original_question.lower()}."
    
    def _extract_key_insights(self, context: ResponseContext, 
                            summary_stats: Dict[str, Any]) -> List[str]:
        """Extract key insights from the data"""
        insights = []
        
        try:
            df = context.query_result.data
            if df is None or df.empty:
                return insights
            
            # Row count insight
            row_count = len(df)
            if row_count == 1:
                insights.append("Found a single specific result matching your criteria")
            elif row_count > 100:
                insights.append(f"Large dataset with {row_count:,} records - consider filtering for more focused analysis")
            else:
                insights.append(f"Found {row_count} relevant records")
            
            # Numeric insights
            for col, stats in summary_stats.get('numeric_summaries', {}).items():
                if stats['count'] > 0:
                    col_name = col.replace('_', ' ').title()
                    
                    # Price-related insights
                    if 'price' in col.lower():
                        avg_price = stats['mean']
                        min_price = stats['min']
                        max_price = stats['max']
                        insights.append(f"{col_name}: Average ${avg_price:.2f}, Range ${min_price:.2f} - ${max_price:.2f}")
                    
                    # Percentage insights
                    elif 'percent' in col.lower() or 'margin' in col.lower():
                        avg_pct = stats['mean']
                        insights.append(f"{col_name}: Average {avg_pct:.1f}%")
                    
                    # Elasticity insights
                    elif 'elasticity' in col.lower():
                        avg_elasticity = stats['mean']
                        if avg_elasticity > 1:
                            insights.append(f"Products show elastic demand (average elasticity: {avg_elasticity:.2f})")
                        else:
                            insights.append(f"Products show inelastic demand (average elasticity: {avg_elasticity:.2f})")
            
            # Execution performance insight
            exec_time = context.query_result.execution_time
            if exec_time > 10:
                insights.append(f"Complex query took {exec_time:.1f} seconds to execute")
            elif context.query_result.cache_hit:
                insights.append("Results retrieved from cache for faster response")
            
        except Exception as e:
            self.logger.error(f"Error extracting insights: {str(e)}")
        
        return insights[:5]  # Limit to top 5 insights
    
    def _generate_summary(self, context: ResponseContext, 
                         summary_stats: Dict[str, Any]) -> str:
        """Generate a brief summary of the results"""
        try:
            row_count = summary_stats.get('total_rows', 0)
            
            if row_count == 0:
                return "No data found matching your criteria."
            elif row_count == 1:
                return "Found one specific result for your query."
            else:
                return f"Retrieved {row_count} records with relevant data for your analysis."
                
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return "Query completed successfully."
    
    def _prepare_data_summary(self, context: ResponseContext, 
                            summary_stats: Dict[str, Any]) -> str:
        """Prepare data summary for LLM prompt"""
        try:
            df = context.query_result.data
            if df is None or df.empty:
                return "No data returned from query."
            
            summary_parts = [
                f"Total rows: {len(df)}",
                f"Columns: {', '.join(df.columns)}"
            ]
            
            # Add sample data (first few rows)
            if len(df) > 0:
                sample_data = df.head(3).to_dict('records')
                summary_parts.append(f"Sample data: {json.dumps(sample_data, default=str)}")
            
            # Add numeric summaries
            for col, stats in summary_stats.get('numeric_summaries', {}).items():
                if stats['count'] > 0:
                    summary_parts.append(
                        f"{col}: mean={stats['mean']:.2f}, min={stats['min']:.2f}, max={stats['max']:.2f}"
                    )
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"Error preparing data summary: {str(e)}")
            return "Data summary unavailable."
    
    def _generate_error_response(self, context: ResponseContext, 
                               error_details: Optional[str] = None) -> GeneratedResponse:
        """Generate response for failed queries"""
        error_msg = error_details or context.query_result.error_message or "Unknown error occurred"
        
        # Generate helpful error response
        if "syntax error" in error_msg.lower():
            text_response = "I encountered a syntax error while processing your question. This might be due to the complexity of the query or missing data. Could you try rephrasing your question or being more specific about what you're looking for?"
        elif "not found" in error_msg.lower():
            text_response = "I couldn't find the requested data. This might be because the table or column doesn't exist, or the data isn't available for the specified criteria. Please check your question and try again."
        elif "permission" in error_msg.lower() or "forbidden" in error_msg.lower():
            text_response = "I don't have permission to access the requested data. Please contact your administrator to ensure you have the necessary access rights."
        else:
            text_response = f"I encountered an issue while processing your question: {error_msg}. Please try rephrasing your question or contact support if the problem persists."
        
        return GeneratedResponse(
            text_response=text_response,
            summary="Query execution failed",
            key_insights=[f"Error: {error_msg}"],
            data_table="<p>No data available due to query error.</p>",
            visualization=None,
            confidence_score=0.1,
            response_type="error",
            metadata={'error': error_msg}
        )


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data for testing
    sample_data = pd.DataFrame({
        'upc_code': ['001', '002', '003', '004', '005'],
        'product_name': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],
        'current_price': [10.99, 15.49, 8.99, 22.99, 12.49],
        'suggested_price': [11.49, 14.99, 9.49, 21.99, 13.99],
        'elasticity_value': [1.2, 0.8, 1.5, 0.6, 1.1],
        'margin_percent': [25.5, 30.2, 22.1, 35.8, 28.9]
    })
    
    # Mock query result
    class MockQueryResult:
        def __init__(self):
            self.success = True
            self.data = sample_data
            self.row_count = len(sample_data)
            self.execution_time = 1.2
            self.cache_hit = False
            self.error_message = None
    
    # Test response generation
    response_generator = ResponseGenerator()
    
    context = ResponseContext(
        original_question="What are the current prices and elasticity values for our top products?",
        sql_query="SELECT upc_code, product_name, current_price, suggested_price, elasticity_value, margin_percent FROM products LIMIT 5",
        query_result=MockQueryResult(),
        intent="price_analysis",
        entities=['price', 'elasticity'],
        user_preferences={}
    )
    
    response = response_generator.generate_response(context)
    
    print("Generated Response:")
    print(f"Text: {response.text_response}")
    print(f"Summary: {response.summary}")
    print(f"Key Insights: {response.key_insights}")
    print(f"Confidence: {response.confidence_score}")
    print(f"Has visualization: {response.visualization is not None}")

