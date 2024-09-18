# Телеграм-бот для помощи студентам СПбГУ в отслеживании расписания занятий

# Как запустить проект?

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/LaGGgggg/spbu_schedule_tg_bot.git
cd spbu_schedule_tg_bot
```

### 2. Создайте виртуальное окружение

#### С помощью [pipenv](https://pipenv.pypa.io/en/latest/):

```bash
pip install --user pipenv
pipenv shell  # create and activate
```

#### Или классическим методом:

```bash
python -m venv .venv  # create
.venv\Scripts\activate.bat  # activate
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Установите переменные окружения (environment variables)

Создайте файл `.env`. После скопируйте это в него

```dotenv
BOT_TOKEN=<your_token_for_tg_bot>
SCHEDULE_BASE_URL=<https://timetable.spbu.ru/AMCP/StudentGroupEvents/Primary/394872/>
ENGLISH_TEACHER=<"Семенова Ю. О.">
```
_**Не забудьте поменять значения на свои! (поставьте их после "=")**_

#### Больше о переменных:
BOT_TOKEN - токен telegram-бота<br>
SCHEDULE_BASE_URL - URL для просмотра расписания, аналогично этому: `https://timetable.spbu.ru/AMCP/StudentGroupEvents/Primary/394872/`
, но для нужной группы<br>
ENGLISH_TEACHER - точное ФИО учителя по английскому языку, скопированное из расписания
(нужно для удаления чужих пар по английскому)<br>

### 5. Запустите проект

```bash
python main.py
```

# Продакшен настройка

### 1. Установите [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

### 2. Установите [docker](https://docs.docker.com/engine/install/)

### 3. Установите [docker compose plugin](https://docs.docker.com/compose/install/linux/)

### 4. Клонируйте репозиторий

```bash
git clone https://github.com/LaGGgggg/spbu_schedule_tg_bot.git
cd spbu_schedule_tg_bot
```

### 5. Установите переменные окружения (environment variables)

Создайте файл `.env`. После скопируйте это в него

```dotenv
BOT_TOKEN=<your_token_for_tg_bot>
SCHEDULE_BASE_URL=<https://timetable.spbu.ru/AMCP/StudentGroupEvents/Primary/394872/>
ENGLISH_TEACHER=<"Семенова Ю. О.">
```
_**Не забудьте поменять значения на свои! (поставьте их после "=")**_

#### Больше о переменных:
BOT_TOKEN - токен telegram-бота<br>
SCHEDULE_BASE_URL - URL для просмотра расписания, аналогично этому: `https://timetable.spbu.ru/AMCP/StudentGroupEvents/Primary/394872/`
, но для нужной группы<br>
ENGLISH_TEACHER - точное ФИО учителя по английскому языку, скопированное из расписания
(нужно для удаления чужих пар по английскому)<br>

### 6. Запустите docker compose

```bash
docker compose up -d
```

### 7. После успешного запуска проверьте сервер

```bash
docker compose logs -f
```
