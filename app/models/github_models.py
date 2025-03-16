"""
GitHub veri modelleri.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class GitHubUser:
    """GitHub kullanıcı modeli."""
    
    login: str
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    html_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubUser':
        """Sözlükten nesne oluşturur.
        
        Args:
            data: Sözlük verisi
            
        Returns:
            GitHubUser nesnesi
        """
        return cls(
            login=data.get('login', ''),
            id=data.get('id', 0),
            name=data.get('name'),
            email=data.get('email'),
            avatar_url=data.get('avatar_url'),
            html_url=data.get('html_url')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Nesneyi sözlüğe dönüştürür.
        
        Returns:
            Sözlük verisi
        """
        return {
            'login': self.login,
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'html_url': self.html_url
        }


@dataclass
class GitHubLabel:
    """GitHub etiket modeli."""
    
    name: str
    id: int
    color: str
    description: Optional[str] = None
    url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubLabel':
        """Sözlükten nesne oluşturur.
        
        Args:
            data: Sözlük verisi
            
        Returns:
            GitHubLabel nesnesi
        """
        return cls(
            name=data.get('name', ''),
            id=data.get('id', 0),
            color=data.get('color', ''),
            description=data.get('description'),
            url=data.get('url')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Nesneyi sözlüğe dönüştürür.
        
        Returns:
            Sözlük verisi
        """
        return {
            'name': self.name,
            'id': self.id,
            'color': self.color,
            'description': self.description,
            'url': self.url
        }


@dataclass
class GitHubMilestone:
    """GitHub milestone modeli."""
    
    title: str
    id: int
    number: int
    state: str
    description: Optional[str] = None
    due_on: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    closed_at: Optional[str] = None
    html_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubMilestone':
        """Sözlükten nesne oluşturur.
        
        Args:
            data: Sözlük verisi
            
        Returns:
            GitHubMilestone nesnesi
        """
        return cls(
            title=data.get('title', ''),
            id=data.get('id', 0),
            number=data.get('number', 0),
            state=data.get('state', ''),
            description=data.get('description'),
            due_on=data.get('due_on'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            closed_at=data.get('closed_at'),
            html_url=data.get('html_url')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Nesneyi sözlüğe dönüştürür.
        
        Returns:
            Sözlük verisi
        """
        return {
            'title': self.title,
            'id': self.id,
            'number': self.number,
            'state': self.state,
            'description': self.description,
            'due_on': self.due_on,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'closed_at': self.closed_at,
            'html_url': self.html_url
        }


@dataclass
class GitHubIssue:
    """GitHub issue modeli."""
    
    title: str
    id: int
    number: int
    state: str
    body: Optional[str] = None
    user: Optional[GitHubUser] = None
    labels: List[GitHubLabel] = field(default_factory=list)
    milestone: Optional[GitHubMilestone] = None
    assignees: List[GitHubUser] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    closed_at: Optional[str] = None
    html_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubIssue':
        """Sözlükten nesne oluşturur.
        
        Args:
            data: Sözlük verisi
            
        Returns:
            GitHubIssue nesnesi
        """
        user = None
        if data.get('user'):
            user = GitHubUser.from_dict(data['user'])
        
        labels = []
        for label_data in data.get('labels', []):
            labels.append(GitHubLabel.from_dict(label_data))
        
        milestone = None
        if data.get('milestone'):
            milestone = GitHubMilestone.from_dict(data['milestone'])
        
        assignees = []
        for assignee_data in data.get('assignees', []):
            assignees.append(GitHubUser.from_dict(assignee_data))
        
        return cls(
            title=data.get('title', ''),
            id=data.get('id', 0),
            number=data.get('number', 0),
            state=data.get('state', ''),
            body=data.get('body'),
            user=user,
            labels=labels,
            milestone=milestone,
            assignees=assignees,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            closed_at=data.get('closed_at'),
            html_url=data.get('html_url')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Nesneyi sözlüğe dönüştürür.
        
        Returns:
            Sözlük verisi
        """
        result = {
            'title': self.title,
            'id': self.id,
            'number': self.number,
            'state': self.state,
            'body': self.body,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'closed_at': self.closed_at,
            'html_url': self.html_url
        }
        
        if self.user:
            result['user'] = self.user.to_dict()
        
        if self.labels:
            result['labels'] = [label.to_dict() for label in self.labels]
        
        if self.milestone:
            result['milestone'] = self.milestone.to_dict()
        
        if self.assignees:
            result['assignees'] = [assignee.to_dict() for assignee in self.assignees]
        
        return result


@dataclass
class GitHubCard:
    """GitHub proje kartı modeli."""
    
    id: int
    note: Optional[str] = None
    content_url: Optional[str] = None
    content: Optional[GitHubIssue] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    archived: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubCard':
        """Sözlükten nesne oluşturur.
        
        Args:
            data: Sözlük verisi
            
        Returns:
            GitHubCard nesnesi
        """
        content = None
        if data.get('content'):
            content = GitHubIssue.from_dict(data['content'])
        
        return cls(
            id=data.get('id', 0),
            note=data.get('note'),
            content_url=data.get('content_url'),
            content=content,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            archived=data.get('archived', False)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Nesneyi sözlüğe dönüştürür.
        
        Returns:
            Sözlük verisi
        """
        result = {
            'id': self.id,
            'note': self.note,
            'content_url': self.content_url,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'archived': self.archived
        }
        
        if self.content:
            result['content'] = self.content.to_dict()
        
        return result


@dataclass
class GitHubColumn:
    """GitHub proje sütunu modeli."""
    
    id: int
    name: str
    cards: List[GitHubCard] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubColumn':
        """Sözlükten nesne oluşturur.
        
        Args:
            data: Sözlük verisi
            
        Returns:
            GitHubColumn nesnesi
        """
        cards = []
        for card_data in data.get('cards', []):
            cards.append(GitHubCard.from_dict(card_data))
        
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            cards=cards,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Nesneyi sözlüğe dönüştürür.
        
        Returns:
            Sözlük verisi
        """
        return {
            'id': self.id,
            'name': self.name,
            'cards': [card.to_dict() for card in self.cards],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class GitHubProject:
    """GitHub proje modeli."""
    
    id: int
    name: str
    body: Optional[str] = None
    number: Optional[int] = None
    state: str = 'open'
    columns: List[GitHubColumn] = field(default_factory=list)
    creator: Optional[GitHubUser] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    html_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubProject':
        """Sözlükten nesne oluşturur.
        
        Args:
            data: Sözlük verisi
            
        Returns:
            GitHubProject nesnesi
        """
        columns = []
        for column_data in data.get('columns', []):
            columns.append(GitHubColumn.from_dict(column_data))
        
        creator = None
        if data.get('creator'):
            creator = GitHubUser.from_dict(data['creator'])
        
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            body=data.get('body'),
            number=data.get('number'),
            state=data.get('state', 'open'),
            columns=columns,
            creator=creator,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            html_url=data.get('html_url')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Nesneyi sözlüğe dönüştürür.
        
        Returns:
            Sözlük verisi
        """
        result = {
            'id': self.id,
            'name': self.name,
            'body': self.body,
            'number': self.number,
            'state': self.state,
            'columns': [column.to_dict() for column in self.columns],
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'html_url': self.html_url
        }
        
        if self.creator:
            result['creator'] = self.creator.to_dict()
        
        return result


@dataclass
class GitHubRepository:
    """GitHub repository modeli."""
    
    id: int
    name: str
    full_name: str
    owner: GitHubUser
    description: Optional[str] = None
    html_url: Optional[str] = None
    projects: List[GitHubProject] = field(default_factory=list)
    issues: List[GitHubIssue] = field(default_factory=list)
    milestones: List[GitHubMilestone] = field(default_factory=list)
    labels: List[GitHubLabel] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pushed_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubRepository':
        """Sözlükten nesne oluşturur.
        
        Args:
            data: Sözlük verisi
            
        Returns:
            GitHubRepository nesnesi
        """
        owner = GitHubUser.from_dict(data.get('owner', {}))
        
        projects = []
        for project_data in data.get('projects', []):
            projects.append(GitHubProject.from_dict(project_data))
        
        issues = []
        for issue_data in data.get('issues', []):
            issues.append(GitHubIssue.from_dict(issue_data))
        
        milestones = []
        for milestone_data in data.get('milestones', []):
            milestones.append(GitHubMilestone.from_dict(milestone_data))
        
        labels = []
        for label_data in data.get('labels', []):
            labels.append(GitHubLabel.from_dict(label_data))
        
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            full_name=data.get('full_name', ''),
            owner=owner,
            description=data.get('description'),
            html_url=data.get('html_url'),
            projects=projects,
            issues=issues,
            milestones=milestones,
            labels=labels,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            pushed_at=data.get('pushed_at')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Nesneyi sözlüğe dönüştürür.
        
        Returns:
            Sözlük verisi
        """
        return {
            'id': self.id,
            'name': self.name,
            'full_name': self.full_name,
            'owner': self.owner.to_dict(),
            'description': self.description,
            'html_url': self.html_url,
            'projects': [project.to_dict() for project in self.projects],
            'issues': [issue.to_dict() for issue in self.issues],
            'milestones': [milestone.to_dict() for milestone in self.milestones],
            'labels': [label.to_dict() for label in self.labels],
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'pushed_at': self.pushed_at
        } 