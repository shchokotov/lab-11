import os
from flask import Flask, render_template, url_for, flash, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from jinja2 import Template
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'QWERTY123456'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static\photos'
ALLOWED_EXTENSIONS = {'webp', 'jpg', 'png'}
users = SQLAlchemy(app)
albums = SQLAlchemy(app)



# with app.app_context():
#     albums.create_all()

class Users(users.Model):
    id = users.Column(users.Integer, primary_key=True)
    name = users.Column(users.String(50), nullable=False)
    login = users.Column(users.String(50), nullable=False)
    password = users.Column(users.String(15), nullable=False)

    def __repr__(self):
        return '<User %r>' %self.id
    
class Albums(albums.Model):
    id = albums.Column(albums.Integer, primary_key=True)
    title = albums.Column(albums.String(100), nullable=False)
    dateOfRelease = albums.Column(albums.String(20), nullable=False)
    picture = albums.Column(albums.String(100), nullable=False)
    discription = albums.Column(albums.Text, nullable=False)

    def __repr__(self):
        return '<Album %r>' %self.id  

@app.route('/')
@app.route('/main')
def main():
    return render_template("main.html", title="Головна сторінка")

@app.route('/logout') 
def logout(): 
    if 'authorisation' in session: 
        session.pop('authorisation', None) 
    return redirect(url_for('main'))


@app.route('/about')
def about():
    return render_template("about.html", title="Про виконавця")


@app.route('/history')
def history():
    return render_template("history.html", title="Історія")


@app.route('/albums')
def albumLoad():
    albums = Albums.query.order_by(Albums.dateOfRelease.desc()).all()
    return render_template("albums.html", title="Альбоми", albums=albums, error=False)

@app.route('/albums/<int:id>/edit',  methods=['POST', 'GET'])
def albumEdit(id):
    if request.method == "POST":
        album = Albums.query.get(id)
        titles = [album2.title  for album2 in Albums.query.all() if album2.title != album.title]
        if (request.form['title'] in titles): 
            flash("Помилка! Такий альбом вже інсує.", category='error')
            return redirect(f'/albums/{id}')
        else:
            file = request.files['picture']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            album.title = request.form['title']
            album.dateOfRelease = request.form['dateOfRelease']
            album.picture=file.filename
            album.discription=request.form['discription']
            try: 
                albums.session.commit()
                flash(f'Альбом успішно змінено!', category='good')
                return redirect(f'/albums/{id}')
            except:
                flash('Помилка зміни альбому! Перевірте введені дані, або зверніться до адміністратора!', category='error')
    albums2 = Albums.query.order_by(Albums.dateOfRelease.desc()).all()
    return render_template("albums.html", title="Альбоми", albums=albums2, error=True)


@app.route('/albums/<int:id>/delete')
def albumDelete(id):
    album = Albums.query.get_or_404(id)
    try:
        albums.session.delete(album)
        albums.session.commit()
        return redirect('/albums')
    except:
        flash('Помилка видалення альбому! Перевірте введені дані, або зверніться до адміністратора!', category='error')


@app.route('/albums_add',  methods=['POST', 'GET'])
def addAlbums():
    if request.method == "POST":
        titles = [album.title for album in Albums.query.all()]
        if (request.form['title'] in titles): 
            flash("Помилка! Такий альбом вже інсує.", category='error')
        else:
            try: 
                file = request.files['picture']
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                album = Albums(title=request.form['title'], dateOfRelease=request.form['dateOfRelease'], picture=file.filename, discription=request.form['discription'])
                albums.session.add(album)
                albums.session.commit()
                flash(f'Альбом успішно додано!', category='good')
                return redirect('/albums')
            except:
                flash('Помилка додавання альбому! Перевірте введені дані, або зверніться до адміністратора!', category='error')
    albums2 = Albums.query.order_by(Albums.dateOfRelease.desc()).all()
    return render_template("albums.html", title="Альбоми", albums=albums2, error=True)



@app.route('/register',  methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        logins = [user.login for user in Users.query.all()]
        if (request.form['login'] in logins): 
            flash("Помилка! Користувач з таким логіном вже інсує.", category='error')
        else:
            if (request.form['password'] != request.form['repeatPassword']):
                flash("Помилка! Паролі не співпадають.", category='error')
            else:
                user = Users(name=request.form['name'], login=request.form['login'], password=request.form['password'])
                try: 
                    users.session.add(user)
                    users.session.commit()
                    flash(f'Реєстрація пройшла успішно!', category='good')
                    return redirect('/register')
                except:
                    flash('Помилка реєстрації! Перевірте введені дані!', category='error')
    return render_template("register.html", title="Реєстрація")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        user = Users.query.filter_by(login=request.form['login']).first()
        if (user is None): 
            flash(f"Користувача не знайдено! Пройдіть реєстарцію.", category='error')
        else:
            if (request.form['password'] != user.password):
                flash("Помилка! Невірний пароль.", category='error')
            else:
                try:
                    session['authorisation'] = user.login
                    return redirect(url_for('main', methods=['POST'], auth=session['authorisation']))
                except:
                    flash('Помилка сайту! Зверніться до підтримки!', category='error')
    return render_template("login.html", title="Авторизація")

@app.route('/albums/<int:id>')
def albumEditPage(id):
    album = Albums.query.get(id)
    return render_template("albumsEdit.html", title="Альбом", album=album)

@app.route('/albums/details/<int:id>')
def albumDetails(id):
    album = Albums.query.get(id)
    return render_template("albumsDetails.html", title="Альбом", album=album)

@app.errorhandler(404)
def pageNotFound(error):
    return render_template("page404.html", title="Сторінку не знайдено!")

if __name__ == "__main__":
    app.run(debug=True)