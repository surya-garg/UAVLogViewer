"""Agentic chatbot for MAVLink log analysis."""
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config import settings
from mavlink_parser import MAVLinkParser


class FlightAnalysisAgent:
    """
    Agentic chatbot that analyzes MAVLink flight logs.
    Maintains conversation state and can proactively ask for clarifications.
    """
    
    def __init__(self, session_id: str, parser: Optional[MAVLinkParser] = None):
        """Initialize the agent with a session ID and optional parser."""
        self.session_id = session_id
        self.parser = parser
        self.conversation_history: List[Dict[str, str]] = []
        self.context = {}
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    def set_parser(self, parser: MAVLinkParser):
        """Set or update the MAVLink parser."""
        self.parser = parser
        self.context['log_loaded'] = True
        self.context['log_summary'] = parser.get_summary()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with MAVLink documentation and context."""
        base_prompt = """You are an expert UAV flight analyst specializing in MAVLink telemetry data analysis. 
You help users understand their flight logs, identify issues, and provide insights about flight performance.

Your capabilities:
1. Answer specific questions about flight data (altitude, battery, GPS, errors, etc.)
2. Detect and explain anomalies in flight behavior
3. Provide recommendations for flight safety and performance
4. Ask clarifying questions when needed to better assist the user

MAVLink Message Types Reference:
- GPS: Position, altitude, ground speed, satellite count
- BATT/BAT: Battery voltage, current, remaining capacity, temperature
- ATT: Attitude (roll, pitch, yaw)
- IMU: Accelerometer and gyroscope data
- VIBE: Vibration levels
- ERR: Error messages with subsystem and error codes
- MODE: Flight mode changes
- RCIN: RC input channels
- RCOU: RC output (servo/motor commands)
- EKF: Extended Kalman Filter status

Documentation: https://ardupilot.org/plane/docs/logmessages.html

When analyzing data:
- Be specific and cite actual values from the log
- Explain technical terms in user-friendly language
- Highlight safety-critical issues
- Provide context for anomalies (e.g., "This is normal during landing" vs "This indicates a problem")
- Ask for clarification if the user's question is ambiguous

Conversation Guidelines:
- Maintain context from previous messages
- Be proactive in identifying related issues
- Suggest follow-up analyses when relevant
- If you need more specific data to answer accurately, ask for it
"""
        
        # Add log context if available
        if self.parser and self.context.get('log_loaded'):
            summary = self.context['log_summary']
            metadata = summary.get('metadata', {})
            
            context_info = f"""
Current Log Context:
- Flight Duration: {metadata.get('duration_seconds', 0):.1f} seconds ({metadata.get('duration_seconds', 0)/60:.1f} minutes)
- Altitude Range: {metadata.get('min_altitude_m', 'N/A')} to {metadata.get('max_altitude_m', 'N/A')} meters
- Message Types Available: {', '.join(summary.get('message_types', [])[:20])}
- Total Messages: {metadata.get('total_messages', 0)}
"""
            
            if metadata.get('errors'):
                context_info += f"\n- Errors Detected: {len(metadata['errors'])} error(s)"
            
            if metadata.get('gps_loss_events'):
                context_info += f"\n- GPS Issues: {len(metadata['gps_loss_events'])} GPS signal loss event(s)"
            
            if metadata.get('rc_loss_events'):
                context_info += f"\n- RC Issues: {len(metadata['rc_loss_events'])} RC signal loss event(s)"
            
            base_prompt += context_info
        else:
            base_prompt += "\n\nNote: No flight log is currently loaded. Ask the user to upload a .bin file first."
        
        return base_prompt
    
    def _build_tools(self) -> List[Dict[str, Any]]:
        """Build function calling tools for the LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_flight_data",
                    "description": "Query specific flight data from the loaded MAVLink log. Use this to get precise values for altitude, battery, GPS, timing, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query describing what data to retrieve (e.g., 'maximum altitude', 'battery voltage', 'GPS loss events')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_anomalies",
                    "description": "Detect anomalies and potential issues in the flight data. Use this when asked about problems, issues, or anomalies.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "enum": ["all", "altitude", "battery", "gps", "vibration"],
                                "description": "Type of anomaly analysis to perform"
                            }
                        },
                        "required": ["analysis_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_message_data",
                    "description": "Get raw message data for a specific MAVLink message type. Use this for detailed analysis of specific message types.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message_type": {
                                "type": "string",
                                "description": "MAVLink message type (e.g., 'GPS', 'BATT', 'ATT', 'ERR')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of messages to return (default 100)",
                                "default": 100
                            }
                        },
                        "required": ["message_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_time_series",
                    "description": "Get time series data for a specific field to analyze trends over time.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message_type": {
                                "type": "string",
                                "description": "MAVLink message type (e.g., 'GPS', 'BATT')"
                            },
                            "field": {
                                "type": "string",
                                "description": "Field name to extract (e.g., 'Alt', 'Volt', 'NSats')"
                            }
                        },
                        "required": ["message_type", "field"]
                    }
                }
            }
        ]
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function and return the result."""
        if not self.parser:
            return {"error": "No flight log loaded. Please upload a .bin file first."}
        
        try:
            if tool_name == "query_flight_data":
                result = self.parser.query_data(arguments["query"])
                return {"success": True, "data": result}
            
            elif tool_name == "detect_anomalies":
                anomalies = self.parser.detect_anomalies()
                analysis_type = arguments.get("analysis_type", "all")
                
                if analysis_type == "all":
                    return {"success": True, "anomalies": anomalies}
                else:
                    key = f"{analysis_type}_anomalies"
                    return {"success": True, "anomalies": {key: anomalies.get(key, [])}}
            
            elif tool_name == "get_message_data":
                msg_type = arguments["message_type"]
                limit = arguments.get("limit", 100)
                messages = self.parser.get_messages(msg_type, limit)
                return {
                    "success": True,
                    "message_type": msg_type,
                    "count": len(messages),
                    "messages": messages[:10],  # Return first 10 for context
                    "total_available": len(messages)
                }
            
            elif tool_name == "get_time_series":
                msg_type = arguments["message_type"]
                field = arguments["field"]
                df = self.parser.get_time_series(msg_type, field)
                
                if df is None:
                    return {"error": f"No data found for {msg_type}.{field}"}
                
                # Return summary statistics
                return {
                    "success": True,
                    "message_type": msg_type,
                    "field": field,
                    "count": len(df),
                    "min": float(df['value'].min()),
                    "max": float(df['value'].max()),
                    "mean": float(df['value'].mean()),
                    "std": float(df['value'].std()),
                    "sample_data": df.head(5).to_dict('records')
                }
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        Maintains conversation history and uses tools as needed.
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ] + self.conversation_history
        
        # Call OpenAI with function calling
        response = self._chat_openai(messages)
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def _chat_openai(self, messages: List[Dict[str, str]]) -> str:
        """Handle OpenAI chat completion with function calling."""
        tools = self._build_tools()
        max_iterations = 5
        
        for iteration in range(max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # If no tool calls, return the response
            if not message.tool_calls:
                return message.content
            
            # Execute tool calls
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [tc.model_dump() for tc in message.tool_calls]
            })
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                result = self._execute_tool(function_name, arguments)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
        
        # Final response after tool calls
        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        
        return final_response.choices[0].message.content
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the full conversation history."""
        return self.conversation_history
