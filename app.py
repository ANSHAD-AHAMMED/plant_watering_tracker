from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plants.db'
db = SQLAlchemy(app)

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.Integer, nullable=False)  # days
    last_watered = db.Column(db.Date, default=datetime.date.today)

class WateringHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.date.today)

    plant = db.relationship("Plant", backref=db.backref("history", lazy=True))


@app.route('/')
def index():
    plants = Plant.query.all()
    today = datetime.date.today()
    alerts = []
    for plant in plants:
        due = plant.last_watered + datetime.timedelta(days=plant.frequency)
        if today >= due:
            alerts.append(plant.name)
    return render_template("index.html", plants=plants, alerts=alerts)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form['name']
        freq = int(request.form['frequency'])
        new_plant = Plant(name=name, frequency=freq)
        db.session.add(new_plant)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template("add_plant.html")


@app.route('/water/<int:id>')
def water(id):
    plant = Plant.query.get_or_404(id)
    plant.last_watered = datetime.date.today()

    # Save watering history
    history = WateringHistory(plant_id=plant.id, date=datetime.date.today())
    db.session.add(history)

    db.session.commit()
    return redirect(url_for('index'))

@app.route('/history/<int:id>')
def history(id):
    plant = Plant.query.get_or_404(id)
    return render_template("history.html", plant=plant)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
