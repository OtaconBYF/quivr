from logger import get_logger
from models.databases.supabase import (
    ApiKeyHandler,
    Brain,
    BrainKnowledges,
    BrainSubscription,
    Chats,
    File,
    Knowledges,
    Notifications,
    Prompts,
    UserUsage,
    Vector,
)

logger = get_logger(__name__)


class SupabaseDB(
    Brain,
    UserUsage,
    File,
    BrainSubscription,
    ApiKeyHandler,
    Chats,
    Vector,
    Prompts,
    Notifications,
    BrainKnowledges,
    Knowledges,
):
    def __init__(self, supabase_client):
        self.db = supabase_client
        Brain.__init__(self, supabase_client)
        UserUsage.__init__(self, supabase_client)
        File.__init__(self, supabase_client)
        BrainSubscription.__init__(self, supabase_client)
        ApiKeyHandler.__init__(self, supabase_client)
        Chats.__init__(self, supabase_client)
        Vector.__init__(self, supabase_client)
        Prompts.__init__(self, supabase_client)
        Notifications.__init__(self, supabase_client)
        BrainKnowledges.__init__(self, supabase_client)
        Knowledges.__init__(self, supabase_client)
