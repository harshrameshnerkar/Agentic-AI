# LangGraph StateGraph Architecture

## 1. Mermaid Flowchart
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	assistant(assistant)
	tools(tools)
	__end__([<p>__end__</p>]):::last
	__start__ --> assistant;
	assistant -.-> __end__;
	assistant -.-> tools;
	tools --> assistant;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc


## 2. ASCII Graph Representation
        +-----------+         
        | __start__ |         
        +-----------+         
               *              
               *              
               *              
        +-----------+         
        | assistant |         
        +-----------+         
          .         .         
        ..           ..       
       .               .      
+---------+         +-------+ 
| __end__ |         | tools | 
+---------+         +-------+ 

## 3. Graph Structure Breakdown
- **START**: Entrypoint routing into `assistant` node.
- **Node `assistant`**: LLM invocation evaluating messages & emitting tool calls or final answer.
- **Conditional Edge `should_continue`**:
  - `tools`: If `last_message.tool_calls` is non-empty.
  - `END`: If model has produced final text output.
- **Node `tools`**: Executes requested tools (`search`, `calculate`) and emits `role='tool'` observations.
- **Cyclic Edge**: `tools` routes directly back to `assistant`.
