from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Regexp
import requests
import os

db = SQLAlchemy()

MOVIE_API_KEY = os.environ.get('MOVIE_API_KEY')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

url = "https://api.themoviedb.org/3/search/movie"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///movies_DB.db'
Bootstrap5(app)
db.init_app(app)


class MovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired(), Regexp('(^[0-9]\.[0-9]+$)|(^[1-9]'
                                                                                              '$)|(^10$)', message="only numbers and '.' allowed")])
    review = StringField("your review", validators=[DataRequired()])
    submit = SubmitField()

class AddMovie(FlaskForm):
    moviename = StringField("Movie Title")
    submit = SubmitField(label="Add Movie")
class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    movies = db.session.execute(db.Select(Movies).order_by(Movies.rating.desc())).scalars()
    all_movies = movies.all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = i + 1
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit_page():
    form = MovieForm()
    if form.validate_on_submit():
        id_ = request.args.get('id_')
        get_movie = db.get_or_404(Movies, id_)
        get_movie.rating = float(form.rating.data)
        get_movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=form)


@app.route("/delete")
def delete_movie():
    id = request.args.get('id')
    get_movie = db.get_or_404(Movies, id)
    db.session.delete(get_movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods=["GET","POST"])
def add_page():
    new_movie = AddMovie()
    if new_movie.validate_on_submit():
        json = {
            "query": f"{new_movie.moviename.data}"
        }
        response = requests.get(url=url, params=json, headers=headers).json()
        print(response)
        return render_template('select.html', movies=response["results"])
    return render_template('add.html', form=new_movie)

@app.route("/add/ins")
def add_into_db():
    add_movie = Movies(
    title=request.args.get('title'),
    year=int(request.args.get('year').split('-')[0]),
    description=request.args.get('description'),
    img_url="https://image.tmdb.org/t/p/w500" + request.args.get('img_url')
    )
    db.session.add(add_movie)
    db.session.commit()
    id = db.session.execute(db.Select(Movies.id).where(Movies.title == request.args.get('title'))).scalar()
    return redirect(url_for('edit_page', id_=id))

if __name__ == '__main__':
    app.run(debug=True)



