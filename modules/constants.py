from discord import AllowedMentions

class Mentions:
    NONE = AllowedMentions(everyone=False, users=False, roles=False)
    DEFAULT = AllowedMentions(everyone=False)

class TaskStatus:
    COMPLETED = 'COMPLETED'
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    FAILED = 'FAILED'
    SCHEDULED = 'SCHEDULED'

    @staticmethod
    def from_str(s):
        s = s.lower().replace(' ', '')
        return {
            'completed': TaskStatus.COMPLETED,
            'pending': TaskStatus.PENDING,
            'failed': TaskStatus.FAILED,
            'scheduled': TaskStatus.SCHEDULED,
            'progress': TaskStatus.IN_PROGRESS,
            'inprogress': TaskStatus.IN_PROGRESS,
            'in_progress': TaskStatus.IN_PROGRESS
        }[s]