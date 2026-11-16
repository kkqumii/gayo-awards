import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'gayo_awards_super_secret_key'
DEADLINE = datetime.fromisoformat("2026-12-04T21:00:00+03:00")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gayo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

CURRENT_VOTING_ROUND = "round_1"


# Модель (таблица) для хранения голосов
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nomination = db.Column(db.String(100), nullable=False)
    artist = db.Column(db.String(100), nullable=False)


# КЛАСС ДЛЯ ХРАНЕНИЯ НАСТРОЕК (включая раунд)
class Setting(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(100), nullable=False)


# Список номинаций и артистов (как и раньше)
nominations_data = {
    "Best Artist": {
        "desc": "Главный артист года по совокупности достижений",
        "criteria": [("Жюри", 50), ("Цифровая Активность", 30), ("Голосование", 20)],
        "artists": ["Артист 1", "Артист 2", "Артист 3"]
    },
    "Best Cover": {
        "desc": "Лучшая кавер-работа года",
        "criteria": [("Жюри", 50), ("Цифровая Активность", 30), ("Голосование", 20)],
        "artists": ["Артист 1", "Артист 2"]
    },
    "Best Author Song": {
        "desc": "Лучшая оригинальная песня, созданная участником ОИ",
        "criteria": [("Жюри", 50), ("Цифровая Активность", 30), ("Голосование", 20)],
        "artists": ["Артист 1", "Артист 2"]
    },
    "Best New Artist": {
        "desc": "Самый сильный новый артист, ведущий деятельность не более 6 месяцев (с 1 июня 2026 года)",
        "criteria": [("Жюри", 50), ("Цифровая Активность", 30), ("Голосование", 20)],
        "artists": ["Артист 1", "Артист 2"]
    },
    "Fan's Choice": {
        "desc": "Главная награда по выбору аудитории",
        "criteria": [("Голосование", 100)],
        "artists": ["Артист 1", "Артист 2"]
    },
    "Best Group": {
        "desc": "Лучшая группа по итогам года",
        "criteria": [("Жюри", 50), ("Цифровая Активность", 50)],  # Заглушка
        "artists": ["Группа 1", "Группа 2"]
    },
    "Best Soloist": {
        "desc": "Лучший солист по итогам года",
        "criteria": [("Жюри", 50), ("Голосование", 50)],  # Заглушка
        "artists": ["Солист 1", "Солист 2"]
    },
    "Best Musical Recording": {
        "desc": "Лучший результат работы всей команды над одной записью",
        "criteria": [("Жюри", 100)],  # Заглушка
        "artists": ["Запись 1", "Запись 2"]
    },
    "Best Vocal Performance": {
        "desc": "Лучшее вокальное исполнение",
        "criteria": [("Жюри", 100)],
        "artists": ["Вокалист 1", "Вокалист 2"]
    },
    "Best Rap Performance": {
        "desc": "Лучшее рэп-исполнение",
        "criteria": [("Жюри", 100)],
        "artists": ["Рэпер 1", "Рэпер 2"]
    },
    "Best Project": {
        "desc": "Самый значимый и успешный проект года",
        "criteria": [("Жюри", 100)],
        "artists": ["Проект 1", "Проект 2"]
    },
    "Best New Project": {
        "desc": "Сильнейший проект, ведущий деятельность не более 6 месяцев (с 1 июня 2026 года)",
        "criteria": [("Жюри", 100)],
        "artists": ["Проект 1", "Проект 2"]
    },
    "Best Creative Project": {
        "desc": "Проект с наиболее необычной и оригинальной идеей",
        "criteria": [("Жюри", 100)],
        "artists": ["Проект 1", "Проект 2"]
    },
    "Best Collaboration": {
        "desc": "Лучшая совместная работа двух или более артистов",
        "criteria": [("Жюри", 100)],
        "artists": ["Коллаб 1", "Коллаб 2"]
    },
    "Best Production Agency": {
        "desc": "Лучший лейбл или продюсерская команда, показавшая наиболее сильные результаты в развитии своих проектов",
        "criteria": [("Жюри", 100)],
        "artists": ["Агентство 1", "Агентство 2"]
    },
    "Best Producer": {
        "desc": "Человек, наиболее эффективно создававший и развивавший проекты",
        "criteria": [("Жюри", 100)],
        "artists": ["Продюсер 1", "Продюсер 2"]
    },
    "Best Journalist": {
        "desc": "Автор, наиболее заметно освещавший и анализирующий ОИ",
        "criteria": [("Жюри", 100)],
        "artists": ["Журналист 1", "Журналист 2"]
    },
    "Best Designer": {
        "desc": "Лучший создатель визуального оформления проектов",
        "criteria": [("Жюри", 100)],
        "artists": ["Дизайнер 1", "Дизайнер 2"]
    },
    "Best Video Editor": {
        "desc": "Специалист, создавший лучшие видеоработы года и наиболее качественно раскрывший материал через монтаж, динамику и визуальную подачу",
        "criteria": [("Жюри", 100)],
        "artists": ["Монтажер 1", "Монтажер 2"]
    },
    "Best Audio Engineer": {
        "desc": "Специалист, отвечавший за лучшее звуковое оформление записей и добившийся высокого качества сведения, баланса и финального звучания",
        "criteria": [("Жюри", 100)],
        "artists": ["Звукарь 1", "Звукарь 2"]
    }
}

# Создаем таблицу в базе данных при первом запуске
with app.app_context():
    db.create_all()


@app.route('/')
def about():
    return render_template('about.html')


@app.route('/nominations')
def nominations():
    return render_template('nominations.html', nominations=nominations_data)


@app.route('/vote/<nomination>', methods=['GET', 'POST'])
def vote(nomination):
    if nomination not in nominations_data:
        return "Номинация не найдена", 404

    artists_list = nominations_data[nomination]["artists"]

    # 1. Получаем текущий раунд из базы
    round_setting = Setting.query.get('current_round')
    if not round_setting:
        round_setting = Setting(key='current_round', value='round_1')
        db.session.add(round_setting)
        db.session.commit()
    current_round = round_setting.value

    # 2. Проверяем, не закончилось ли время (таймер)
    now = datetime.now(timezone.utc)
    is_closed = now > DEADLINE

    # 3. Обработка голосования
    if request.method == 'POST':
        if is_closed:
            return redirect(url_for('vote', nomination=nomination, error="Голосование уже завершено!"))

        artist = request.form.get('artist')

        # Очистка старых голосов, если админ менял раунд
        if session.get('session_round') != current_round:
            session['voted'] = []
            session['session_round'] = current_round

        if 'voted' not in session:
            session['voted'] = []

        vote_marker = f"{current_round}_{nomination}"

        if vote_marker not in session['voted']:
            if artist in artists_list:
                new_vote = Vote(nomination=nomination, artist=artist)
                db.session.add(new_vote)
                db.session.commit()
                session['voted'].append(vote_marker)
                session.modified = True
                return redirect(url_for('vote', nomination=nomination, success=1))
        else:
            return redirect(url_for('vote', nomination=nomination, error="Вы уже проголосовали!"))

    # 4. Считаем голоса и ПРОЦЕНТЫ для полосок
    votes = {}
    total_votes = 0
    for artist in artists_list:
        count = Vote.query.filter_by(nomination=nomination, artist=artist).count()
        votes[artist] = count
        total_votes += count

    percentages = {}
    for artist in artists_list:
        if total_votes > 0:
            percentages[artist] = round((votes[artist] / total_votes) * 100)
        else:
            percentages[artist] = 0

    # 5. Проверяем статус
    vote_marker = f"{current_round}_{nomination}"
    has_voted = 'voted' in session and vote_marker in session['voted']

    # 6. Передаем ВСЁ в шаблон
    return render_template('vote.html',
                           nomination=nomination,
                           artists=artists_list,
                           votes=votes,
                           percentages=percentages,
                           has_voted=has_voted,
                           is_closed=is_closed,
                           nominations_data=nominations_data)

@app.route('/academy')
def academy():
    return render_template('academy.html')

@app.route('/criteria')
def criteria():
    return render_template('criteria.html')

# Список админов: логин - пароль
ADMINS = {
    "Dora": "doradura123",
    "Reo": "aaaagayoblin123",
    "Jenna": "reopidoras123",
    "Arisu": "ahhhh123"
}



@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Проверяем, есть ли такой юзер и совпадает ли пароль
        if username in ADMINS and ADMINS[username] == password:
            session['is_admin'] = True
            session['admin_name'] = username  # Запоминаем, кто вошел!
            return redirect(url_for('admin_panel'))
        else:
            error = 'Неверный логин или пароль'

    return render_template('admin_login.html', error=error)


@app.route('/admin/panel')
def admin_panel():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    stats = {}
    for nom, data in nominations_data.items():
        stats[nom] = {}
        # Берем список артистов из ключа "artists"
        for artist in data["artists"]:
            count = Vote.query.filter_by(nomination=nom, artist=artist).count()
            stats[nom][artist] = count

    return render_template('admin_panel.html', stats=stats)


# --- МАРШРУТЫ ДЛЯ УДАЛЕНИЯ ГОЛОСОВ ---

@app.route('/admin/reset/artist/<nomination>/<artist>', methods=['POST'])
def reset_artist(nomination, artist):
    if not session.get('is_admin'): return abort(403)
    Vote.query.filter_by(nomination=nomination, artist=artist).delete()

    # Меняем раунд в базе
    round_setting = Setting.query.get('current_round')
    round_setting.value = f"round_{os.urandom(4).hex()}"

    db.session.commit()
    return redirect(url_for('admin_panel'))


@app.route('/admin/reset/nomination/<nomination>', methods=['POST'])
def reset_nomination(nomination):
    if not session.get('is_admin'): return abort(403)
    Vote.query.filter_by(nomination=nomination).delete()

    # Меняем раунд в базе
    round_setting = Setting.query.get('current_round')
    round_setting.value = f"round_{os.urandom(4).hex()}"

    db.session.commit()
    return redirect(url_for('admin_panel'))


@app.route('/admin/reset/all', methods=['POST'])
def reset_all():
    if not session.get('is_admin'): return abort(403)
    Vote.query.delete()

    # Меняем раунд в базе
    round_setting = Setting.query.get('current_round')
    round_setting.value = f"round_{os.urandom(4).hex()}"

    db.session.commit()
    return redirect(url_for('admin_panel'))
    # Удаляем вообще ВСЕ голоса из базы (сброс премии)
    Vote.query.delete()
    db.session.commit()
    return redirect(url_for('admin_panel'))


if __name__ == '__main__':
    app.run(debug=True)
