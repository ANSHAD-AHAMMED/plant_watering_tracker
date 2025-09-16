from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import datetime

# ------------------------------
# App setup
# ------------------------------
app = Flask(__name__)

# Tell Flask to use a SQLite database file called "plants.db"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plants.db'

# Initialize SQLAlchemy (this handles our database work)
db = SQLAlchemy(app)


# ------------------------------
# Database Models (Tables)
# ------------------------------
class Plant(db.Model):
    """
    This table stores information about each plant:
    - name: plant name (e.g., Rose)
    - frequency: how often it needs water (in days)
    - last_watered: the last date we watered it
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.Integer, nullable=False)  # watering frequency in days
    last_watered = db.Column(db.Date, default=datetime.date.today)


class WateringHistory(db.Model):
    """
    This table stores a log/history of watering events:
    - plant_id: which plant was watered
    - date: when it was watered
    """
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.date.today)

    # Relationship: connect each history entry to the plant
    plant = db.relationship("Plant", backref=db.backref("history", lazy=True))


# ------------------------------
# Routes (Web Pages)
# ------------------------------

@app.route('/')
def index():
    """
    Homepage: shows all plants with their status.
    Status can be: Healthy, Due Soon, Due Today, or Overdue.
    """
    plants = Plant.query.all()  # get all plants
    today = datetime.date.today()
    alerts = []  # to highlight plants that need attention
    plant_data = []  # store processed plant info

    for plant in plants:
        # Next watering date
        due_date = plant.last_watered + datetime.timedelta(days=plant.frequency)
        days_until_due = (due_date - today).days

        # Decide the plant's status
        if days_until_due < 0:
            status = 'overdue'
            status_text = f'{abs(days_until_due)} days overdue'
            alerts.append(plant.name)  # alert for this plant
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

        # Check if plant already watered today
        watered_today = plant.last_watered == today

        # Collect info about this plant
        plant_info = {
            'plant': plant,
            'due_date': due_date,
            'days_until_due': days_until_due,
            'status': status,
            'status_text': status_text,
            'watered_today': watered_today,
            'last_watered_human': plant.last_watered.strftime('%B %d, %Y')  # readable format
        }
        plant_data.append(plant_info)

    # Send data to HTML template
    return render_template("index.html", plant_data=plant_data, alerts=alerts)


@app.route('/add', methods=['GET', 'POST'])
def add():
    """
    Add a new plant to the database.
    - If GET: show the form
    - If POST: save plant info
    """
    if request.method == 'POST':
        name = request.form['name']
        freq = int(request.form['frequency'])

        # Create a new plant entry
        new_plant = Plant(name=name, frequency=freq)

        db.session.add(new_plant)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template("add_plant.html")


@app.route('/water/<int:id>')
def water(id):
    """
    Mark a plant as watered today.
    Also add an entry into the watering history table.
    """
    plant = Plant.query.get_or_404(id)
    plant.last_watered = datetime.date.today()

    # Add history record
    history = WateringHistory(plant_id=plant.id, date=datetime.date.today())
    db.session.add(history)

    db.session.commit()
    return redirect(url_for('index'))


@app.route('/history/<int:id>')
def history(id):
    """
    Show the watering history for one plant.
    """
    plant = Plant.query.get_or_404(id)
    due_date = plant.last_watered + datetime.timedelta(days=plant.frequency)

    return render_template("history.html", plant=plant, due_date=due_date)


@app.route('/about')
def about():
    """
    Show stats:
    - How many plants in total
    - How many waterings done
    """
    total_plants = Plant.query.count()
    total_waterings = WateringHistory.query.count()

    return render_template("about.html", total_plants=total_plants, total_waterings=total_waterings)


# ------------------------------
# Error Handlers
# ------------------------------

@app.errorhandler(404)
def not_found_error(error):
    """Show a custom 404 page if page not found"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Show custom 500 page if server error"""
    db.session.rollback()  # rollback in case of DB error
    return render_template('500.html'), 500


# ------------------------------
# Run the app
# ------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables if not already created
    app.run(debug=True, port=5000)
