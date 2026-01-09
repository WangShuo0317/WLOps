"""
基础 Agent 类
所有智能体的抽象基类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from loguru import logger
from datetime import datetime

class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, name: str, llm_client=None, embedding_model=None):
        """
        初始化智能体
        
        Args:
            name: 智能体名称
            llm_client: LLM 客户端（用于复杂逻辑）
            embedding_model: Embedding 模型（用于语义处理）
        """
        self.name = name
        self.llm_client = llm_client
        self.embedding_model = embedding_model
        self.execution_history = []
        
        logger.info(f"初始化智能体: {self.name}")
    
    @abstractmethod
    def run(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        执行智能体任务
        
        Args:
            input_data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            执行结果
        """
        pass
    
    def log_execution(self, input_data: Any, output_data: Any, metadata: Dict = None):
        """记录执行历史"""
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "input_size": len(input_data) if isinstance(input_data, (list, dict)) else 1,
            "output_size": len(output_data) if isinstance(output_data, (list, dict)) else 1,
            "metadata": metadata or {}
        }
        self.execution_history.append(execution_record)
        logger.debug(f"[{self.name}] 执行记录: {execution_record}")
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        if not self.execution_history:
            return {"total_executions": 0}
        
        return {
            "total_executions": len(self.execution_history),
            "first_execution": self.execution_history[0]["timestamp"],
            "last_execution": self.execution_history[-1]["timestamp"],
            "total_input_processed": sum(r["input_size"] for r in self.execution_history),
            "total_output_generated": sum(r["output_size"] for r in self.execution_history)
        }
    
    def validate_input(self, input_data: Any, expected_type: type = None) -> bool:
        """验证输入数据"""
        if input_data is None:
            logger.error(f"[{self.name}] 输入数据为空")
            return False
        
        if expected_type and not isinstance(input_data, expected_type):
            logger.error(f"[{self.name}] 输入类型错误，期望 {expected_type}，实际 {type(input_data)}")
            return False
        
        return True
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}')>"


class AgentPipeline:
    """智能体流水线"""
    
    def __init__(self, name: str):
        self.name = name
        self.agents: List[BaseAgent] = []
        logger.info(f"创建智能体流水线: {self.name}")
    
    def add_agent(self, agent: BaseAgent):
        """添加智能体到流水线"""
        self.agents.append(agent)
        logger.info(f"[{self.name}] 添加智能体: {agent.name}")
    
    def run(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        执行流水线
        
        Args:
            input_data: 初始输入
            **kwargs: 传递给所有智能体的参数
            
        Returns:
            最终输出
        """
        logger.info(f"[{self.name}] 开始执行流水线，共 {len(self.agents)} 个智能体")
        
        current_data = input_data
        results = {}
        
        for i, agent in enumerate(self.agents, 1):
            logger.info(f"[{self.name}] 执行第 {i}/{len(self.agents)} 个智能体: {agent.name}")
            
            try:
                agent_result = agent.run(current_data, **kwargs)
                results[agent.name] = agent_result
                
                # 将当前智能体的输出作为下一个智能体的输入
                if "output" in agent_result:
                    current_data = agent_result["output"]
                
            except Exception as e:
                logger.error(f"[{self.name}] 智能体 {agent.name} 执行失败: {e}")
                results[agent.name] = {"error": str(e)}
                break
        
        logger.info(f"[{self.name}] 流水线执行完成")
        
        return {
            "pipeline": self.name,
            "agents_executed": len([r for r in results.values() if "error" not in r]),
            "results": results,
            "final_output": current_data
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取流水线统计"""
        return {
            "pipeline_name": self.name,
            "total_agents": len(self.agents),
            "agents": [
                {
                    "name": agent.name,
                    "stats": agent.get_execution_stats()
                }
                for agent in self.agents
            ]
        }
