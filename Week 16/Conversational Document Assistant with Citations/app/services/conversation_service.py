from sqlalchemy.orm import Session

from app.models import Conversation, ConversationMessage


def create_conversation(db: Session) -> Conversation:
    conversation = Conversation()
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_or_create_conversation(
    db: Session,
    conversation_id: int | None
) -> Conversation:
    if conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if conversation:
            return conversation

    return create_conversation(db)


def add_message(
    db: Session,
    conversation_id: int,
    role: str,
    message: str
) -> ConversationMessage:
    chat_message = ConversationMessage(
        conversation_id=conversation_id,
        role=role,
        message=message
    )

    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)

    return chat_message


def get_recent_history(
    db: Session,
    conversation_id: int,
    limit: int = 6
) -> list[ConversationMessage]:
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.id.desc())
        .limit(limit)
        .all()
    )