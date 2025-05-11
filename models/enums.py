import enum
from sqlalchemy import Enum as SQLAEnum

class UserStatusEnum(str, enum.Enum):
    banned = 'banned'
    active = 'active'
    inactive = 'inactive'
    pending_approval = 'pending_approval'
    rejected = 'rejected'

class ProjectStatusEnum(str, enum.Enum):
    cancelled = 'cancelled'
    completed = 'completed'
    rejected = 'rejected'
    on_hold = 'on_hold'
    pending_approval = 'pending_approval'
    in_progress = 'in_progress'

class PriorityEnum(str, enum.Enum):
    very_low = 'very_low'
    low = 'low'
    medium = 'medium'
    high = 'high'
    critical = 'critical'

class TaskStatusEnum(str, enum.Enum):
    completed = 'completed'
    cancelled = 'cancelled'
    todo = 'todo'
    in_progress = 'in_progress' 