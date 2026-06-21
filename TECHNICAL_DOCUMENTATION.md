# Техническая документация: Исход Обречённых

## Обзор проекта

**Исход Обречённых** — это top-down roguelite шутер в жанре space battle, разработанный на Python с использованием Pygame. Игра представляет собой процедурно генерируемый галактический крейсер с пошаговой боевой системой, системой прогрессии и динамической AI.

### Основные характеристики
- **Язык**: Python 3.14+
- **Фреймворк**: Pygame 2.6+
- **Архитектура**: MVC (Model-View-Controller) с компонентно-ориентированной системой сущностей
- **Генерация контента**: Binary Space Partitioning (BSP) + Perlin Noise для создания галактик и фонов
- **Оптимизация коллизий**: QuadTree для broad-phase collision detection

### Используемые алгоритмы
#### Лёгкие (3 шт ×1 = 3 балла)
1. **Game loop + deltaTime** — в `game_loop.py`, обеспечивает независимость скорости игры от FPS.
2. **Fixed timestep accumulator** — в `game_loop.py`, физический шаг с постоянной частотой (например, 60 Гц).
3. **Seek / Flee / Arrive (steering)** — в `ai.py`, поведение патрулей Древних: преследование игрока, уход при низком здоровье, прибытие в точку патрулирования.

#### Средние (2 шт ×2 = 4 балла)
4. **QuadTree (recursive subdivision)** — в `utils/quad_tree.py`, пространственная индексация всех объектов в `StarSystem` для быстрого поиска коллизий.
5. **Behavior tree tick traversal** — в `ai.py`, дерево с последовательностями, селекторами, условиями и листовыми действиями. Каждый тик ИИ вызывается `tick()` на корневом узле.

#### Сложные (2 шт ×4 = 8 баллов)
6. **Perlin noise (gradient dot, fade)** — в `utils/perlin.py`, классический алгоритм: генерация псевдослучайных градиентов, fade-функция `6t^5 - 15t^4 + 10t^3`, интерполяция. Используется для фона туманностей в `views/background.py`.
7. **BSP dungeon generation (split + rooms + corridors)** — в `utils/bsp.py`, рекурсивное разбиение прямоугольного поля на листья, создание «комнат» (звёздных систем) и соединение их «коридорами» (гиперпространственными маршрутами). Используется для генерации карты галактики в `models/galaxy.py`.
---

## Архитектура приложения

```
python_game/
├── main.py                 # Точка входа
├── constants.py            # Глобальные константы конфигурации
├── controllers/            # Логика управления и обработки событий
│   ├── game_loop.py       # Основной цикл игры (координирует все компоненты)
│   ├── input_handler.py   # Обработка ввода (клавиатура, мышь)
│   ├── collision_manager.py # Разрешение коллизий
│   └── ai_controller.py   # Управление поведением врагов
├── models/                # Данные и логика сущностей
│   ├── entities.py        # Определения всех типов сущностей
│   ├── player.py          # Данные прогресса игрока (roguelite система)
│   ├── galaxy.py          # Генерация вселенной и систем
│   └── ai.py              # Деревья поведения и функции управления AI
├── views/                 # Отрисовка и визуализация
│   ├── renderer.py        # Отрисовка миров и сущностей
│   ├── hud.py            # Интерфейс, минимап, галактическая карта
│   ├── menu.py           # Меню (главное, пауза, настройки)
│   ├── background.py     # Процедурная генерация фонов
│   └── text.py           # Утилиты для работы с текстом
└── utils/                 # Вспомогательные алгоритмы
    ├── bsp.py            # Binary Space Partitioning для генерации комнат
    ├── quad_tree.py      # QuadTree пространственный индекс
    ├── perlin.py         # Классический Perlin Noise 2D
    └── save_load.py      # Сериализация игрового состояния
```

---

## Ключевые компоненты

### 1. **main.py** — Точка входа

```python
def main() -> None:
    """Create and run the game loop."""
    GameLoop().run()
```

**Назначение**: Инициализирует и запускает основной цикл игры.

---

### 2. **controllers/game_loop.py** — Главный игровой цикл

**Класс: `GameLoop`**

#### Основные методы:

| Метод | Назначение |
|-------|-----------|
| `__init__()` | Инициализирует Pygame, создает экран, инстанцирует все компоненты системы |
| `run()` | Главный цикл (работает до закрытия окна): обработка событий, обновление, рендеринг |
| `_run_playing()` | Игровая логика во время активной игры (обновление физики, обработка ввода) |
| `_run_menu()` | Обработка меню (главное, пауза, настройки) |
| `_run_dialog()` | Управление диалогами с планетами (пролистывание текста) |
| `_run_galaxy_map()` | Интерактивная карта галактики для гиперпрыжков |
| `_fixed_update(state, dt)` | Фиксированный timestep для физики (60 Hz) |

#### Архитектурные решения:

- **Delta-time accumulatор**: Используется паттерн фиксированного timestep (1/60 сек) для детерминированной физики, но обрабатывается с переменным frame rate до 120 Hz
- **Максимальный frame time**: Ограничение `MAX_FRAME_TIME = 0.25` сек предотвращает "проваливание" симуляции при лагах
- **Состояния режимов**: Система использует строковые идентификаторы режимов (`"playing"`, `"main"`, `"pause"`, `"dialog"`, `"galaxy_map"`) для управления переходами между состояниями

---

### 3. **controllers/input_handler.py** — Обработка ввода

**Класс: `InputHandler`**

**Структура: `InputState`** (dataclass)
```python
@dataclass
class InputState:
    movement: pygame.Vector2          # Нормализованный вектор движения (-1...1)
    aim_screen: pygame.Vector2        # Позиция мыши на экране
    firing: bool                      # Зажата ли левая кнопка мыши
    pause_pressed: bool              # Нажата ли ESC
    hyperjump_pressed: bool          # Нажата ли H
    interact_pressed: bool           # Нажата ли E
    weapon_delta: int                # -1/0/1 (прокрутка ко��еса мыши)
```

#### Основной метод:

| Метод | Назначение |
|-------|-----------|
| `poll()` -> (InputState, quit_flag) | Опрашивает события Pygame и возвращает нормализованное состояние ввода |

#### Обоснование подхода:

- **Scancode-based input**: Использует сканкоды вместо виртуальных кодов клавиш для поддержки различных раскладок клавиатуры (WASD работает независимо от языка)
- **Continuous key tracking**: Отслеживает нажатые клавиши между кадрами (не только нажатия в текущем кадре)
- **Window focus handling**: Очищает состояние клавиш при потере фокуса окна

---

### 4. **controllers/collision_manager.py** — Система коллизий

**Класс: `CollisionManager`**

#### Основной метод:

```python
def resolve(system: StarSystem) -> int:
    """Resolve collisions in a system.
    
    Returns: Number of enemies destroyed during this pass.
    """
```

#### Архитектура:

- **QuadTree broad-phase**: Весь мир разделён на иерархический пространственный индекс для быстрого поиска потенциальных коллизий
- **Узкая фаза**: Точная проверка коллизий через `collides_with()` только для сущностей, найденных в broad-phase
- **Разделение проверок**: 
  - **Projectiles**: Проверяет коллизии снарядов со всеми сущностями (кроме планет и снарядов)
  - **Ship-Asteroid**: Проверяет столкновение кораблей с астероидами (вызывает отскок и урон)

#### Оптимизация:

- **Факция-фильтр**: Снаряды не причиняют урон дружественным сущностям
- **Отскок объектов**: При столкновении корабля с астероидом применяется эффект отскока (reflection) с затуханием (0.35x скорость)

---

### 5. **controllers/ai_controller.py** — Управление AI врагов

**Класс: `AIController`**

#### Основной метод:

```python
def update(enemies: list[AncientShip], player: Ship, dt: float) -> list[Projectile]:
    """Tick all enemy AI trees and return spawned projectiles."""
```

#### Структура:

- **Деревья поведения на сущность**: Каждый враг имеет собственное дерево поведения (Behavior Tree)
- **Кэширование**: Деревья создаются один раз и переиспользуются (кэш по `id(enemy)`)
- **Очистка мёртвых**: При удалении врага его дерево удаляется из кэша

---

### 6. **models/entities.py** — Определение сущностей

**Базовый класс: `Entity`** (dataclass)

```python
@dataclass
class Entity:
    position: pygame.Vector2      # Мировые координаты
    velocity: pygame.Vector2      # Вектор скорости
    radius: float                 # Радиус для коллизий
    faction: Faction              # PLAYER / ANCIENT / NEUTRAL
    max_health: float
    health: float | None = None   # Заполняется автоматически в __post_init__
    alive: bool = True
```

#### Наследники Entity:

| Класс | Описание | Фракция |
|-------|---------|---------|
| `Projectile` | Снаряд с конечным временем жизни | Зависит от источника |
| `Ship` | Боевой корабль с щитами, энергией, оружием | PLAYER / ANCIENT |
| `AncientShip` | Враг с AI, патрулированием | ANCIENT |
| `Asteroid` | Нейтральное препятствие, вращается | NEUTRAL |
| `Planet` | Статичный объект квеста | NEUTRAL |

#### Ключевые методы:

| Метод | Назначение |
|-------|-----------|
| `bounds() -> Rect` | Возвращает AABB для broad-phase collision detection |
| `update(dt)` | Обновляет позицию на основе скорости |
| `apply_force(force, dt, max_speed)` | Применяет ускорение и ограничивает максимальную скорость |
| `take_damage(amount)` | Уменьшает здоровье, отмечает мёртвым если оно <= 0 |
| `collides_with(other) -> bool` | Точная проверка коллизии (расстояние между центрами vs сумма радиусов) |

#### Обоснование типизации:

- **Circular collision shapes**: Просто эффективно, соответствует форме кораблей/астероидов
- **Union types** (`health: float | None`): Позволяет различить "не имеет здоровья" от "имеет ноль HP"

#### Создатели сущностей (factory functions):

| Функция | Возвращает |
|---------|-----------|
| `create_player_ship()` | Корабль игрока с начальными параметрами |
| `create_ancient_ship(position, rng, world_size)` | Враг с 3 точками патрулирования |
| `create_asteroid(position, radius, rng)` | Дрейфующий астероид с вращением |

---

### 7. **models/player.py** — Система прогресса (Roguelite)

**Класс: `PlayerData`** (dataclass)

```python
@dataclass
class PlayerData:
    resources: int                      # Валюта для апгрейдов
    artifacts: list[str]               # Собранные артефакты (расскажи историю)
    upgrades: dict[str, int]           # Уровни постоянных улучшений
    unlocked_systems: list[int]        # Посещённые системы
    completed_quests: list[int]        # ID выполненных квестов
    current_system_id: int             # ID текущей системы
    runs_completed: int                # Счётчик завершённых попыток
    moral_choice: str | None           # Для будущего развития (выбор нравственности)
```

#### Основные методы:

| Метод | Назначение |
|-------|-----------|
| `upgrade_cost(key) -> int` | Вычисляет стоимость апгрейда: базовая + (уровень × базовая/2) |
| `buy_upgrade(key) -> bool` | Пытается купить апгрейд, возвращает успех |
| `to_dict() / from_dict()` | Сериализация/десериализация для сохранений |

#### Формула стоимости апгрейдов:

```
cost(level) = base_cost + level × (base_cost / 2)
```

**Обоснование**: Экспоненциальный рост стоимости (хотя и не истинная экспонента) поощряет разнообразие инвестиций вместо максимизации одного апгрейда.

---

### 8. **models/galaxy.py** — Генерация вселенной и систем

#### **Класс: `SystemNode`**

Представляет звёздную систему на галактической карте:

```python
@dataclass
class SystemNode:
    system_id: int                    # Уникальный ID
    name: str                         # "Сектор 01"
    map_position: tuple[int, int]    # Позиция на галактической карте
    room: Rect                        # BSP комната, из которой сгенерирована система
    connections: set[int]            # IDs соседних систем
    visited: bool                     # Была ли посещена
```

#### **Класс: `StarSystem`**

Текущая играбельная система:

```python
@dataclass
class StarSystem:
    node: SystemNode                 # Ссылка на узел галактики
    seed: int                        # Уникальный seed для детерминированного RNG
    player: Ship                     # Корабль игрока
    asteroids: list[Asteroid]       # Препятствия
    enemies: list[AncientShip]      # Враги
    planet: Planet | None            # Опциональный объект квеста
    projectiles: list[Projectile]   # Снаряды (синтезируются во время обновления)
    hit_effects: list[HitEffect]    # Визуальные эффекты попаданий
    objective_text: str              # Текст на HUD ("Уничтожьте патруль")
    reward_granted: bool             # Был ли выдан награда за очистку
```

#### **Класс: `Universe`**

Контейнер всех систем с поддержкой навигации:

```python
def __init__(self, seed: int | None = None):
    self.seed = seed if seed is not None else random.randint(1, 999_999)
    self._random = random.Random(self.seed)
    self.systems: list[SystemNode] = []
    self._generate()
```

#### Генерация галактики (алгоритм BSP):

1. **Binary Space Partitioning** (`utils/bsp.py`):
   - Рекурсивно разбивает 100×60 прямоугольник галактики на комнаты
   - Параметры: `MIN_LEAF_SIZE=14`, `MAX_DEPTH=5`
   - Каждый лист содержит комнату (звёздную систему)

2. **Выбор систем**: 
   - Из всех комнат выбирается 8-15 случайных
   - Каждой назначается ID и имя ("Сектор 01")

3. **Соединение систем**:
   - Смежные системы (по ID) соединяются в цепь
   - BSP коридоры также соединяют системы

#### Генерация содержимого системы (`create_star_system`):

```python
def create_star_system(self, system_id: int, player_data: PlayerData) -> StarSystem:
    """Generate playable content for a system."""
    
    node = self.systems[system_id]
    node.visited = True
    
    rng = random.Random(self.seed + system_id * 997)  # Детерминированный RNG
    
    # Применить апгрейды игрока к кораблю
    player = create_player_ship(...)
    player.max_health += player_data.upgrades.get("hull", 0) * 18.0
    
    # Создать астероиды
    asteroids = [create_asteroid(...) for _ in range(rng.randint(22, 42))]
    
    # Создать врагов
    enemies = [create_ancient_ship(...) for _ in range(rng.randint(4, 8))]
    
    # Опциональная планета (50% шанс)
    planet = self._create_planet(node, rng, player_data)
    
    return StarSystem(...)
```

#### Обоснование детерминизма:

```python
rng = random.Random(self.seed + system_id * 997)
```

- **Воспроизводимость**: Одна и та же система всегда содержит одни и те же враги/астероиды
- **Нечувствительность к порядку посещения**: Множитель 997 (простое число) предотвращает коллизии seeds при разных ID
- **Roguelite ощущение**: Игрок может выбрать новый seed для новой вселенной, но конкретная система всегда одинакова

---

### 9. **models/ai.py** — Система поведения врагов

#### **Паттерн: Behavior Tree (Дерево поведения)**

Иерархия узлов, каждый из которых возвращает `BehaviorStatus`:

```python
class BehaviorStatus(Enum):
    SUCCESS = auto()   # Действие выполнено
    FAILURE = auto()   # Условие не выполнено
    RUNNING = auto()   # Действие всё ещё выполняется
```

#### **Типы узлов:**

| Класс | Поведение |
|-------|-----------|
| `SequenceNode` | Выполняет детей по порядку до первого FAILURE |
| `SelectorNode` | Выполняет детей до первого SUCCESS или RUNNING |
| `ConditionNode` | Возвращает SUCCESS если предикат истинен |
| `ActionNode` | Выполняет действие и возвращает его статус |

#### **Дерево поведения Ancient (враг):**

```
SelectorNode [
    SequenceNode [              # 1. Если здоровье низкое
        _is_low_health(),       #    Проверить здоровье < 28%
        _flee_from_player()     #    Убежать
    ],
    SequenceNode [              # 2. Если видит игрока
        _can_detect_player(),   #    Проверить расстояние < 620
        _attack_player()        #    Атаковать (seek + стрельба)
    ],
    _patrol()                   # 3. По умолчанию - патрулирование
]
```

#### **Функции управления (steering behaviors):**

| Функция | Назначение |
|---------|-----------|
| `seek()` | Ускорение к цели (для атаки) |
| `flee()` | Ускорение от угрозы (для бегства) |
| `arrive()` | Ускорение с замедлением при приближении (для патрулирования) |

#### Реализация `seek`:

```python
def seek(position, target, velocity, max_speed):
    """Return steering force toward a target."""
    desired = target - position
    if desired.length_squared() == 0.0:
        return pygame.Vector2()
    desired = desired.normalize() * max_speed
    return desired - velocity  # Steering = desired_velocity - current_velocity
```

**Обоснование**: Это классический алгоритм управления из Craig Reynolds. Субъект ускоряется в направлении между собой и целью, но не превышает максимальную скорость.

#### `arrive` с замедлением:

```python
def arrive(position, target, velocity, max_speed, slowing_radius=180.0):
    desired = target - position
    distance = desired.length()
    if distance == 0.0:
        return -velocity  # Остановить
    speed = max_speed * min(distance / slowing_radius, 1.0)  # Снизить скорость на подходе
    desired = desired.normalize() * speed
    return desired - velocity
```

**Эффект**: Враги не врезаются в точку патрулирования, а плавно тормозят при приближении.

---

### 10. **views/renderer.py** — Рендеринг игровых объектов

**Класс: `Renderer`**

#### Основные методы:

| Метод | Назначение |
|-------|-----------|
| `draw_system(system)` | Отрисовка фона, всех сущностей, эффектов |
| `screen_to_world(screen_pos, focus)` | Конвертирование экранных координат в мировые |
| `_camera_for(focus)` | Вычисление позиции камеры для центрирования на объекте |
| `_draw_ship()` | Отрисовка корабля с ориентацией по скорости |
| `_draw_asteroid()` | Отрисовка астероида (кружок) |
| `_draw_planet()` | Отрисовка планеты (кружок + дуга, сияние) |
| `_draw_projectile()` | Отрисовка снаряда (голубой для игрока, оранжевый для врагов) |
| `_draw_hit_effect()` | Отрисовка эффекта попадания (расширяющееся кольцо) |
| `_draw_warnings()` | Красные кружки вокруг близких врагов |

#### Система камеры:

```python
def _camera_for(self, focus: pygame.Vector2) -> pygame.Vector2:
    """Center camera on focus, but don't go beyond world bounds."""
    return pygame.Vector2(
        max(0.0, min(focus.x - SCREEN_WIDTH/2, 
                     WORLD_WIDTH - SCREEN_WIDTH)),
        max(0.0, min(focus.y - SCREEN_HEIGHT/2, 
                     WORLD_HEIGHT - SCREEN_HEIGHT))
    )
```

**Обоснование**: Камера следует за игроком, но не выходит за границы мира (避免черный экран).

#### Ориентация спрайтов:

```python
def _orient_sprite(sprite, velocity):
    """Rotate sprite to face velocity direction."""
    if velocity.length_squared() <= 1.0:
        return sprite
    angle = math.degrees(math.atan2(-velocity.y, velocity.x)) - 90.0
    return pygame.transform.rotozoom(sprite, angle, 1.0)
```

**Обоснование**: Корабли выглядят как движутся туда, куда летят, что улучшает визуальный feedback.

---

### 11. **views/hud.py** — Интерфейс и миникарты

**Класс: `HUD`**

#### Основные элементы:

1. **Полосы статуса** (`_draw_bar`):
   - Корпус, щиты, энергия, скорость
   - Визуальное представление: полоса + текст с числами

2. **Миникарта** (`_draw_minimap`):
   - Масштабированное представление текущей системы
   - Астероиды (серые точки), враги (оранжевые квадраты), планета (зелёный круг), игрок (голубой круг)

3. **Карта галактики** (`draw_hyperjump_map`):
   - Интерактивная карта звёздных систем
   - Цветовое кодирование: серая (непосещённая), голубая (посещённая), зелёная (достижимая), жёлтая (текущая)
   - Линии показывают соединения между системами
   - Клик мышью или клавиши 1-9 для прыжка

#### Масштабирование координат:

```python
def _galaxy_position(self, rect: pygame.Rect, map_position: tuple[int, int]) -> tuple[int, int]:
    return (
        rect.x + int(map_position[0] / GALAXY_WIDTH * rect.width),
        rect.y + int(map_position[1] / GALAXY_HEIGHT * rect.height)
    )
```

**Назначение**: Преобразует координаты BSP галактики (100×60) в экранный прямоугольник.

---

### 12. **views/menu.py** — Система меню

**Класс: `MenuSystem`** + **Dataclass: `Button`**

#### Типы меню:

| Меню | Назначение |
|------|-----------|
| `main` | Новая игра, продолжить, настройки, выход |
| `pause` | Продолжить, сохранить, загрузить, настройки, меню |
| `settings` | Апгрейды (куплены ресурсы) и навигация |

#### Обработка кнопок:

```python
def _buttons(self, menu_name: str, has_save: bool, player_data: PlayerData | None = None) -> list[Button]:
    # Каждая кнопка имеет label, action ID, rect, и флаг enabled
    # enabled = False автоматически отключает кнопку если:
    # - "continue" но нет сохранения
    # - upgrade недоступен (не хватает ресурсов)
```

#### Диалоги планет:

```python
def draw_dialog(self, surface, title: str, lines: list[str], page: int):
    # Показывает 3 строки текста за раз
    # Кнопка мыши / Space / E: следующая страница
    # Esc: закрыть
```

**Обоснование пагинации**: Экран слишком маленький для всего текста квеста сразу.

---

### 13. **views/background.py** — Процедурный фон

**Класс: `BackgroundGenerator`**

#### Алгоритм:

1. **Создание малого изображения** (96×80 пикселей при BACKGROUND_CELL_SIZE=6)
2. **Perlin Noise для небулы**:
   - Два слоя шума разных масштабов
   - Синий канал доминирует для "космоса"
3. **Звёзды** (второй слой шума, threshold 0.84):
   - Яркие пиксели для звёзд
4. **Масштабирование** обратно до размера мира (smooth scaling)

#### Кэширование:

```python
def get(self, seed: int, size: tuple[int, int]) -> pygame.Surface:
    if seed not in self._cache:
        self._cache[seed] = self._generate(seed, size)
    return self._cache[seed]
```

**Обоснование**: Фон генерируется один раз на систему и переиспользуется, сохраняя консистентность визуалов.

---

### 14. **utils/bsp.py** — Binary Space Partitioning

**Класс: `BspGenerator`**

#### Алгоритм:

1. **Инициализация**: Корневой прямоугольник (100×60)
2. **Рекурсивное разбиение** (`_split`):
   - На каждом уровне решить: разбить вертикально или горизонтально
   - Вертикальное разбиение, если ширина > высоты × 1.25 (иначе горизонтальное)
   - Если оба размера подходят, выбрать случайно (50%)
3. **Создание комнат** (`_create_rooms`):
   - В каждом листе создать случайную комнату (1/3 до полного размера листа)
4. **Соединение** (`_connect_nearest_rooms`):
   - Соединить соседние комнаты коридорами
   - Коридоры отслеживаются в дереве

#### Параметры:

- `MIN_LEAF_SIZE = 14`: Минимальный размер листа
- `MAX_DEPTH = 5`: Максимальная глубина рекурсии

**Обоснование**: Гарантирует интересную структуру с разнообразными размерами комнат и разумным количеством врагов (8-15 систем).

---

### 15. **utils/quad_tree.py** — Пространственный индекс QuadTree

**Класс: `QuadTree[T]`** (Generic)

#### Протокол:

```python
class HasBounds(Protocol):
    def bounds(self) -> Rect:  # Объект должен предоставить AABB
```

#### Основные методы:

| Метод | Назначение |
|-------|-----------|
| `insert(obj)` | Вставить объект, автоматически subdivide если переполнено |
| `query(area)` | Вернуть все объекты, чьи bounds пересекают area |
| `clear()` | Очистить всё содержимое |

#### Алгоритм подразделения:

```python
def _subdivide(self):
    # Разбить на 4 квадранта: TL, TR, BL, BR
    half_width = self._boundary.width / 2.0
    half_height = self._boundary.height / 2.0
    # Рекреировать дочерние узлы и перераспределить объекты
```

#### Параметры:

- `QUADTREE_CAPACITY = 6`: Порог для subdivision
- `QUADTREE_MAX_DEPTH = 7`: Максимальная глубина

**Обоснование**: QuadTree обеспечивает O(log n) поиск потенциальных коллизий вместо O(n²) н��ивного алгоритма.

---

### 16. **utils/perlin.py** — Perlin Noise 2D

**Класс: `PerlinNoise`**

#### Классический алгоритм Перлина (Ken Perlin):

1. **Инициализация**: Сетка градиентных векторов (256×256 по умолчанию)
2. **Вычисление шума** (`noise`):
   - Найти 4 соседних узла сетки для точки (x, y)
   - Вычислить dot product между градиентом и дистанцией к точке
   - Интерполяция между dot products с smooth fade функцией

#### Fade функция (полиномиальная интерполяция):

```python
@staticmethod
def _fade(t: float) -> float:
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)  # 6t^5 - 15t^4 + 10t^3
```

**Обоснование**: Гладкая функция третьего порядка с нулевыми производными в начале/конце (C² непрерывность).

#### Методы:

| Метод | Назначение |
|-------|-----------|
| `noise(x, y)` | Шум в диапазоне примерно [-1, 1] |
| `normalized(x, y)` | Шум в диапазоне [0, 1] |

**Применение**: Генерация фонов, процедурных ландшафтов, процедурной генерации контента.

---

### 17. **utils/save_load.py** — Сохранение/загрузка

#### Функции:

```python
def save_game(path: str | Path, universe_seed: int, player_data: PlayerData) -> None:
    """Persist to JSON."""
    payload = {
        "version": 1,
        "universe_seed": universe_seed,
        "player": player_data.to_dict()
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")

def load_game(path: str | Path) -> tuple[int, PlayerData] | None:
    """Load from JSON or return None on error."""
    # Чтение и парсинг с обработкой ошибок
```

**Обоснование**: JSON для человекочитаемости, UTF-8 для поддержки русского текста, кэширование ошибок для устойчивости к повреждённым сохранениям.

---

## Системные интеграции

### Игровой цикл (Frame-to-Frame):

```
1. Input Poll (InputHandler.poll)
   ↓
2. Input Processing (GameLoop._run_playing)
   ↓
3. Fixed Timestep Accumulation (dt accumulator)
   ↓
4. Physics Update (Ship.accelerate, Entity.update)
   ↓
5. AI Update (AIController.update)
   ↓
6. Collision Resolution (CollisionManager.resolve)
   ↓
7. Entity Cleanup (remove dead entities)
   ↓
8. Rendering (Renderer.draw_system)
   ↓
9. UI Rendering (HUD.draw)
   ↓
10. Display Flip
    ↓
    Repeat
```

### Инициализация игры:

```
GameLoop.__init__
  ↓
Pygame initialization
  ↓
Universe generation (BSP)
  ↓
StarSystem creation (set up player, enemies, asteroids)
  ↓
GameLoop.run (enters main loop)
```

### Гиперпрыжок между системами:

```
Player clears system
  ↓
Press H to open galaxy map
  ↓
Select connected system (1-9 or mouse)
  ↓
Universe.create_star_system (deterministic generation)
  ↓
New system ready
```

---

## Производительность и оптимизация

### Узкие места:

1. **Collision detection**: QuadTree O(log n) broad-phase вместо O(n²)
2. **Rendering**: Спрайты кэшированы и масштабированы один раз
3. **Background generation**: Кэшируется по seed
4. **Physics**: Фиксированный timestep (60 Hz) позволяет пропустить frame updates при лагах

### Ограничения параметров:

- **MAX_FRAME_TIME = 0.25s**: Предотвращает проваливание при лагах > 250 мс
- **FPS_LIMIT = 120**: Ограничение частоты кадров для снижения нагрузки
- **ANCIENT_DETECTION_RADIUS = 620**: Враги видят игрока только в радиусе ~620 пикселей
- **QUADTREE_MAX_DEPTH = 7**: Балансирует глубину vs. количество объектов на лист

---

## Constants.py — Конфигурация

### Категории констант:

| Категория | Примеры |
|-----------|---------|
| **Экран** | SCREEN_WIDTH=1280, SCREEN_HEIGHT=720 |
| **Время** | FPS_LIMIT=120, FIXED_TIME_STEP=1/60 |
| **Мир** | WORLD_WIDTH=2400, WORLD_HEIGHT=1600 |
| **Галактика** | SYSTEM_COUNT_MIN=8, MAX=15, BSP_MIN_LEAF_SIZE=14 |
| **Игрок** | PLAYER_RADIUS=22, MAX_HEALTH=140, MAX_SHIELDS=90, MAX_ENERGY=100 |
| **Враги** | ANCIENT_RADIUS=24, MAX_HEALTH=85, DETECTION_RADIUS=620 |
| **Оружие** | PLAYER_FIRE_COOLDOWN=0.16, урон, скорость, время жизни |
| **Апгрейды** | UPGRADE_COSTS={hull: 60, shields: 55, engine: 70, reactor: 65, weapons: 80} |
| **Перлин** | BACKGROUND_CELL_SIZE=6, BACKGROUND_NOISE_SCALE=0.013 |

**Обоснование**: Централизованная конфигурация позволяет быстро балансировать механику без поиска по коду.

---

## Расширяемость и будущие улучшения

### Текущие точки расширения:

1. **Новые типы врагов**: Добавить новые классы врагов через наследование `AncientShip` и создание новых деревьев поведения
2. **Системы оружия**: Новые профили в `PLAYER_WEAPONS` с различными параметрами
3. **Типы препятствий**: Новые типы астероидов через наследование `Asteroid`
4. **Сюжет**: Расширять диалоги планет и questlines через `SystemNode.dialog_lines`
5. **Новые апгрейды**: Добавить ключи в `UPGRADE_COSTS` и `UPGRADE_LABELS`

### Возможные архитектурные улучшения:

- **Event system**: Эмиттер событий вместо прямых вызовов методов
- **Component system**: ECS (Entity Component System) вместо наследования для большей гибкости
- **Save versioning**: Обработка обратной совместимости между версиями сохранений
- **Audio system**: Подсистема звуков с 2D позиционированием
- **Particle system**: Система частиц для эффектов взрывов

---

## Выводы

**Исход Обречённых** демонстрирует чистую архитектуру MVC с:

- **Детерминированной генерацией контента** через BSP и Perlin Noise
- **Оптимизированной обработкой коллизий** через QuadTree
- **Поведенческими деревьями** для масштабируемой AI
- **Roguelite системой прогрессии** с постоянными апгрейдами
- **Процедурно-генерируемым контентом** для переиграемости

Код хорошо структурирован для расширения и модификации, с четкой разделением ответственности между компонентами.
