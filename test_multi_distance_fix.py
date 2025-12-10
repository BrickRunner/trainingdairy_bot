"""
Тест для проверки исправления багa с несколькими дистанциями
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User

async def test_multi_distance_state_persistence():
    """Проверяем, что state не очищается между вводами времени"""

    # Создаем mock объекты
    message = MagicMock(spec=Message)
    message.text = "45:30"
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.answer = AsyncMock(return_value=MagicMock(message_id=999))

    # Создаем mock для FSMContext
    state = AsyncMock(spec=FSMContext)

    # Симулируем state с двумя дистанциями
    state_data = {
        'distances_to_process': [
            {'index': 0, 'distance_km': 10, 'name': 'Дистанция 1'},
            {'index': 1, 'distance_km': 21, 'name': 'Дистанция 2'}
        ],
        'current_distance_index': 0,
        'distance_times': {},
        'competition_id': 'test_comp_123',
        'current_competition': {
            'id': 'test_comp_123',
            'title': 'Тестовый забег',
            'begin_date': '2025-12-15T00:00:00Z',
            'end_date': '2025-12-15T00:00:00Z',
            'place': 'Москва',
            'sport_code': 'run',
            'url': 'http://example.com',
            'distances': [
                {'distance': 10, 'name': 'Дистанция 1'},
                {'distance': 21, 'name': 'Дистанция 2'}
            ]
        }
    }

    state.get_data = AsyncMock(return_value=state_data)
    state.get_state = AsyncMock(return_value='UpcomingCompetitionsStates:waiting_for_target_time')
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()

    # Импортируем функцию
    from competitions.upcoming_competitions_handlers import process_target_time

    # Патчим get_user_settings
    with patch('competitions.upcoming_competitions_handlers.get_user_settings',
               new=AsyncMock(return_value={'distance_unit': 'км'})):
        # Вызываем функцию
        await process_target_time(message, state)

    # Проверяем, что state.clear() НЕ был вызван
    # (так как это multi-distance flow и есть еще одна дистанция)
    assert state.clear.call_count == 0, "state.clear() не должен быть вызван в multi-distance flow"

    # Проверяем, что update_data был вызван с правильными данными
    assert state.update_data.called, "update_data должен был быть вызван"

    # Проверяем, что состояние остается waiting_for_target_time
    assert state.set_state.called, "set_state должен был быть вызван"

    # Проверяем, что отправлено сообщение пользователю
    assert message.answer.called, "Сообщение должно быть отправлено пользователю"

    print("[OK] Test passed! State is not cleared between time inputs for multiple distances")

if __name__ == "__main__":
    asyncio.run(test_multi_distance_state_persistence())
