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
    plant_data = []
    
    for plant in plants:
        due_date = plant.last_watered + datetime.timedelta(days=plant.frequency)
        days_until_due = (due_date - today).days
        
        # Calculate status
        if days_until_due < 0:
            status = 'overdue'
            status_text = f'{abs(days_until_due)} days overdue'
            alerts.append(plant.name)
        elif days_until_due == 0:
            status = 'due_today'
            status_text = 'Due today'
            alerts.append(plant.name)
        elif days_until_due <= 2:
            status = 'due_soon'
            status_text = f'Due in {days_until_due} day{"s" if days_until_due > 1 else ""}'
        else:
            status = 'healthy'
            status_text = f'Due in {days_until_due} days'
        
        # Check if watered today
        watered_today = plant.last_watered == today
        
        plant_info = {
            'plant': plant,
            'due_date': due_date,
            'days_until_due': days_until_due,
            'status': status,
            'status_text': status_text,
            'watered_today': watered_today,
            'last_watered_human': plant.last_watered.strftime('%B %d, %Y')
        }
        plant_data.append(plant_info)
    
    return render_template("index.html", plant_data=plant_data, alerts=alerts)

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
    due_date = plant.last_watered + datetime.timedelta(days=plant.frequency)
    return render_template("history.html", plant=plant, due_date=due_date)

@app.route('/about')
def about():
    # Get some stats for the about page
    total_plants = Plant.query.count()
    total_waterings = WateringHistory.query.count()
    return render_template("about.html", total_plants=total_plants, total_waterings=total_waterings)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
