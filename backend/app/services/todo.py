from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate


async def get_todos(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    completed: bool | None = None,
) -> tuple[list[Todo], int]:
    """Get paginated todos for a user."""
    query = select(Todo).where(Todo.user_id == user_id)

    if completed is not None:
        query = query.where(Todo.completed == completed)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Get paginated results
    query = query.order_by(Todo.priority.desc(), Todo.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    todos = list(result.scalars().all())

    return todos, total


async def get_todo_by_id(db: AsyncSession, todo_id: int, user_id: int) -> Todo | None:
    """Get a todo by ID for a specific user."""
    result = await db.execute(
        select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_todo(db: AsyncSession, user_id: int, todo_in: TodoCreate) -> Todo:
    """Create a new todo."""
    todo = Todo(
        title=todo_in.title,
        description=todo_in.description,
        priority=todo_in.priority,
        user_id=user_id,
    )
    db.add(todo)
    await db.flush()
    await db.refresh(todo)
    return todo


async def update_todo(db: AsyncSession, todo: Todo, todo_in: TodoUpdate) -> Todo:
    """Update a todo."""
    update_data = todo_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)

    await db.flush()
    await db.refresh(todo)
    return todo


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    """Delete a todo."""
    await db.delete(todo)
    await db.commit()


async def toggle_todo(db: AsyncSession, todo: Todo) -> Todo:
    """Toggle todo completed status."""
    todo.completed = not todo.completed
    await db.flush()
    await db.refresh(todo)
    return todo
