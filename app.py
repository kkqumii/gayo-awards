import os
from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'gayo_awards_super_secret_key'

# Настройка базы данных (создаст файл gayo.db в папке проекта)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gayo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Модель (таблица) для хранения голосов
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nomination = db.Column(db.String(100), nullable=False)
    artist = db.Column(db.String(100), nullable=False)


# Список номинаций и артистов (как и раньше)
nominations_data = {
    "Best Group of the Year": ["Группа А", "Группа Б", "Группа В"],
    "Best Solo Artist of the Year (Female)": ["Солистка 1", "Солистка 2"],
    "Best Solo Artist of the Year (Male)": ["Солист 1", "Солист 2"],
    "Fan Choice": ["Артист X", "Артист Y", "Артист Z"],
    "Best Prod Team of the Year": ["Прод-команда 1", "Прод-команда 2"],
    "Best Solo Prod of the Year": ["Продюсер 1", "Продюсер 2"],
    "Best Project of the Year": ["Проект 1", "Проект 2"],
    "Best Author Song of the Year": ["Автор 1", "Автор 2"],
    "Best Cover of the Year": ["Кавер 1", "Кавер 2"],
    "Best New Year Cover of the Year": ["Новогодний кавер 1", "Новогодний кавер 2"],
    "Best Collaboration of the Year": ["Коллаб 1", "Коллаб 2"],
    "Best Rookie Group of the Year": ["Новички 1", "Новички 2"],
    "Best Rookie Solo of the Year": ["Соло-новичок 1", "Соло-новичок 2"],
    "GAYO Winner of the Year": ["Легенда 1", "Легенда 2"]
}

# Создаем таблицу в базе данных при первом запуске
with app.app_context():
    db.create_all()


@app.route('/')
def about():
    return render_template('about.html')


@app.route('/nominations')
def nominations():
    # Нам не нужно передавать голоса сюда, только список названий номинаций
    return render_template('nominations.html', nominations=nominations_data)


@app.route('/vote/<nomination>', methods=['GET', 'POST'])
def vote(nomination):
    if nomination not in nominations_data:
        return "Номинация не найдена", 404

    if request.method == 'POST':
        artist = request.form.get('artist')

        if 'voted' not in session:
            session['voted'] = []

        # Если пользователь еще не голосовал в этой номинации
        if nomination not in session['voted']:
            if artist in nominations_data[nomination]:
                # Сохраняем голос в базу данных!
                new_vote = Vote(nomination=nomination, artist=artist)
                db.session.add(new_vote)
                db.session.commit()

                # Запоминаем в сессии, что голос отдан
                session['voted'].append(nomination)
                session.modified = True
                return redirect(url_for('vote', nomination=nomination, success=1))
        else:
            return redirect(url_for('vote', nomination=nomination, error="Вы уже проголосовали в этой номинации!"))

    # Считаем голоса для каждого артиста в этой номинации из базы данных
    artists = nominations_data[nomination]
    votes = {}
    for artist in artists:
        # Ищем в базе все записи с этой номинацией и этим артистом и считаем их количество
        count = Vote.query.filter_by(nomination=nomination, artist=artist).count()
        votes[artist] = count

    has_voted = 'voted' in session and nomination in session['voted']

    return render_template('vote.html',
                           nomination=nomination,
                           artists=artists,
                           votes=votes,
                           has_voted=has_voted)


# Пароль для входа в админку (по умолчанию 'admin123', но лучше поменяй!)
# Список админов: логин - пароль
ADMINS = {
    "Dora": "doradura123",
    "Reo": "aaaagayoblin123",
    "Jenna": "reopidoras123"
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
    # Проверка, что это админ
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    # Собираем всю статистику для панели
    stats = {}
    for nom, artists in nominations_data.items():
        stats[nom] = {}
        for artist in artists:
            count = Vote.query.filter_by(nomination=nom, artist=artist).count()
            stats[nom][artist] = count

    return render_template('admin_panel.html', stats=stats)


# --- МАРШРУТЫ ДЛЯ УДАЛЕНИЯ ГОЛОСОВ ---

@app.route('/admin/reset/artist/<nomination>/<artist>', methods=['POST'])
def reset_artist(nomination, artist):
    if not session.get('is_admin'): return abort(403)

    # Удаляем все записи этого артиста в этой номинации
    Vote.query.filter_by(nomination=nomination, artist=artist).delete()
    db.session.commit()
    return redirect(url_for('admin_panel'))


@app.route('/admin/reset/nomination/<nomination>', methods=['POST'])
def reset_nomination(nomination):
    if not session.get('is_admin'): return abort(403)

    # Удаляем все записи в этой номинации
    Vote.query.filter_by(nomination=nomination).delete()
    db.session.commit()
    return redirect(url_for('admin_panel'))


@app.route('/admin/reset/all', methods=['POST'])
def reset_all():
    if not session.get('is_admin'): return abort(403)

    # Удаляем вообще ВСЕ голоса из базы (сброс премии)
    Vote.query.delete()
    db.session.commit()
    return redirect(url_for('admin_panel'))


if __name__ == '__main__':
    app.run(debug=True)