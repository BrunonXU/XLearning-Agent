"""
GitHub 仓库分析器

职责：
1. 获取仓库 README
2. 读取 requirements.txt 识别技术栈
3. 提取项目结构和关键信息

风险控制：
- 只读 README + requirements，不做代码遍历
- 避免范围失控

面试话术：
> "RepoAnalyzer 作为 Specialist，专门处理 GitHub 仓库解析。
>  只读 README 和 requirements，风险可控。
>  分析结果通过 to_learning_context() 转成 Planner 能理解的格式。"

TODO (Day 9):
- 实现 GitHub API 调用
- 提取更多仓库信息
"""

import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import httpx


class RepoInfo(BaseModel):
    """仓库信息"""
    name: str
    full_name: str
    description: str = ""
    readme: str = ""
    tech_stack: List[str] = []
    topics: List[str] = []
    stars: int = 0
    language: str = ""


class RepoAnalyzer:
    """
    GitHub 仓库分析器
    
    分析 GitHub 仓库，提取学习相关信息
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        初始化分析器
        
        Args:
            github_token: GitHub API Token（可选，用于提高 API 限额）
        """
        self.github_token = github_token
        self.headers = {}
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"
        self.headers["Accept"] = "application/vnd.github.v3+json"
    
    def analyze(self, url: str) -> RepoInfo:
        """
        分析 GitHub 仓库
        
        Args:
            url: GitHub 仓库 URL
            
        Returns:
            RepoInfo 对象
        """
        # 提取 owner/repo
        match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if not match:
            raise ValueError(f"Invalid GitHub URL: {url}")
        
        owner, repo = match.groups()
        repo = repo.rstrip('.git')
        
        # 获取仓库信息
        repo_info = self._get_repo_info(owner, repo)
        
        # 获取 README
        readme = self._get_readme(owner, repo)
        repo_info["readme"] = readme
        
        # 获取 requirements.txt 分析技术栈
        tech_stack = self._get_tech_stack(owner, repo)
        repo_info["tech_stack"] = tech_stack
        
        return RepoInfo(**repo_info)
    
    def _get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """获取仓库基本信息"""
        # TODO: 实现 GitHub API 调用
        # 目前返回模拟数据
        return {
            "name": repo,
            "full_name": f"{owner}/{repo}",
            "description": f"{repo} 项目",
            "stars": 0,
            "language": "Python",
            "topics": [],
        }
    
    def _get_readme(self, owner: str, repo: str) -> str:
        """获取 README 内容"""
        # TODO: 实现 GitHub API 调用
        # 目前返回模拟数据
        return f"# {repo}\n\n这是 {owner}/{repo} 仓库的 README。"
    
    def _get_tech_stack(self, owner: str, repo: str) -> List[str]:
        """从 requirements.txt 提取技术栈"""
        # TODO: 实现 GitHub API 调用
        # 目前返回模拟数据
        return ["Python", "LangChain", "ChromaDB"]
    
    def to_learning_context(self, repo_info: RepoInfo) -> str:
        """
        将仓库信息转换为学习上下文
        
        用于传递给 Planner Agent
        """
        parts = [
            f"# {repo_info.full_name}",
            "",
            f"**项目描述**: {repo_info.description}",
            f"**主要语言**: {repo_info.language}",
            f"**技术栈**: {', '.join(repo_info.tech_stack)}",
            "",
            "## README 内容",
            "",
            repo_info.readme[:3000] if len(repo_info.readme) > 3000 else repo_info.readme,
        ]
        return "\n".join(parts)
