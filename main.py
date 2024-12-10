# Import modules
from flask import Flask, flash, redirect, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, Integer, String, Float

from polygon import RESTClient
import pandas as pd
import numpy as np
import sqlite3

#flask app instance
app = Flask(__name__)
app.config['SECRET_KEY'] = '93aa0c631b766e9ac2f59351a7cb7d6fbf6dc0ee1bfc59e8'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'

db = SQLAlchemy(app)

#declaration of model


class Players(db.Model):
    __tablename__ = 'players'
    player_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_name = db.Column(db.String, nullable=False)
    hall_team = db.Column(db.String, nullable=False)
    position = db.Column(db.String, nullable=False)
    debut = db.Column(db.Integer, nullable=False)
    retired = db.Column(db.Integer, nullable=False)

class Career_Stats_Hitting(db.Model):
    __tablename__ = 'career_stats_hitting'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.player_id'), nullable=False)
    batting_average = db.Column(db.Float, nullable=True)
    hits = db.Column(db.Integer, nullable=True)
    home_runs = db.Column(db.Integer, nullable=True)
    stolen_bases = db.Column(db.Integer, nullable=True)
    walks = db.Column(db.Integer, nullable=True)
    strikeouts = db.Column(db.Integer, nullable=True)
    h_war = db.Column(db.Float, nullable=True)
    
    # Add cascade delete in the relationship
    player = db.relationship('Players', backref=db.backref('hitting_stats', cascade='all, delete-orphan'))


  
class Career_Stats_Pitching(db.Model):
    __tablename__ = 'career_stats_pitching'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.player_id'), nullable=False)
   # player_name = db.Column(db.String, db.ForeignKey('players.player_name'), nullable=False)
    earned_run_average = db.Column(db.Float, nullable=True)
    innings = db.Column(db.Integer, nullable=True)
    wins = db.Column(db.Integer, nullable=True)
    walks = db.Column(db.Integer, nullable=True)
    strikeouts = db.Column(db.Integer, nullable=True)
    saves = db.Column(db.Integer, nullable=True)
    p_war = db.Column(db.Float, nullable=True)
    
    # Add cascade delete in the relationship
    player = db.relationship('Players', backref=db.backref('pitching_stats', cascade='all, delete-orphan'))

@app.route('/index')
def player():
    players = Players.query.all()  # Retrieve all players
    return render_template('index.html', players=players)
@app.route('/')
def home():
    players = Players.query.all()  # Query all players from the Players table
    return render_template('home.html', players=players)
@app.route('/hitting_stats')
def hitting_stats():
     stats = db.session.query(
        Career_Stats_Hitting.id,
        Career_Stats_Hitting.player_id,
        Players.player_name,
        Career_Stats_Hitting.batting_average,
        Career_Stats_Hitting.hits,
        Career_Stats_Hitting.home_runs,
        Career_Stats_Hitting.walks,
        Career_Stats_Hitting.strikeouts,
        Career_Stats_Hitting.stolen_bases,
        Career_Stats_Hitting.h_war
    ).join(Players, Players.player_id == Career_Stats_Hitting.player_id).all()
     return render_template('hitting_stats.html', career_stats_hitting=stats)

   

@app.route('/pitching_stats')
def pitching_stats():
    # Perform a join between Players and Career_Stats_Pitching
    stats = db.session.query(
        Career_Stats_Pitching.id,
        Career_Stats_Pitching.player_id,
        Players.player_name,
        Career_Stats_Pitching.earned_run_average,
        Career_Stats_Pitching.saves,
        Career_Stats_Pitching.wins,
        Career_Stats_Pitching.walks,
        Career_Stats_Pitching.strikeouts,
        Career_Stats_Pitching.innings,
        Career_Stats_Pitching.p_war
    ).join(Players, Players.player_id == Career_Stats_Pitching.player_id).all()

    # Pass the data directly to the template
    return render_template('pitching_stats.html', career_stats_pitching=stats)


@app.route('/player_stats/<int:player_id>')
def player_stats(player_id):
    # Query the player's basic information
    player = Players.query.get(player_id)
    if not player:
        return f"Player with ID {player_id} not found", 404

    # Query hitting and pitching stats for the player
    hitting_stats = Career_Stats_Hitting.query.filter_by(player_id=player_id).first()
    pitching_stats = Career_Stats_Pitching.query.filter_by(player_id=player_id).first()

    # Render the stats in a dedicated template
    return render_template('player_stats.html', player=player, hitting_stats=hitting_stats, pitching_stats=pitching_stats)


@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        try:
            # Extract form data
            player_name = request.form['player_name']
            hall_team = request.form['hall_team']
            position = request.form['position']
            debut = int(request.form['debut'])
            retired = int(request.form['retired'])

            # Create a new Player instance with placeholders
            stmt = sa.text("""
                INSERT INTO players (player_name, hall_team, position, debut, retired)
                VALUES (:player_name, :hall_team, :position, :debut, :retired)
            """)

            # Execute the prepared statement
            db.session.execute(stmt, {
                'player_name': player_name,
                'hall_team': hall_team,
                'position': position,
                'debut': debut,
                'retired': retired
            })
            db.session.commit()

            # Retrieve the new player_id
            new_player = Players.query.filter_by(player_name=player_name, debut=debut).first()
            player_id = new_player.player_id

            # Insert hitting stats with placeholders
            hitting_stmt = sa.text("""
                INSERT INTO career_stats_hitting (player_id, batting_average, hits, home_runs, stolen_bases, walks, strikeouts, h_war)
                VALUES (:player_id, 0.0, 0, 0, 0, 0, 0, 0.0)
            """)
            db.session.execute(hitting_stmt, {'player_id': player_id})
            
            # Insert pitching stats with placeholders
            pitching_stmt = sa.text("""
                INSERT INTO career_stats_pitching (player_id, earned_run_average, saves, wins, walks, strikeouts, innings, p_war)
                VALUES (:player_id, 0.0, 0, 0, 0, 0, 0, 0.0)
            """)
            db.session.execute(pitching_stmt, {'player_id': player_id})
            
            db.session.commit()
            flash("Player and default stats successfully added!", "success")
            return redirect('/')
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding player: {e}", "error")
            return redirect('/add_player')

    return render_template('add_player.html')



@app.route('/add_hitting_stats/<int:player_id>', methods=['GET', 'POST'])
def add_hitting_stats(player_id):
    # Check if hitting stats already exist for the player
    hitting_stats = Career_Stats_Hitting.query.filter_by(player_id=player_id).first()

    if request.method == 'POST':
        # If stats already exist, update them
        if hitting_stats:
            hitting_stats.batting_average = float(request.form['batting_average'])
            hitting_stats.hits = int(request.form['hits'])
            hitting_stats.home_runs = int(request.form['home_runs'])
            hitting_stats.walks = int(request.form['walks'])
            hitting_stats.strikeouts = int(request.form['strikeouts'])
            hitting_stats.stolen_bases = int(request.form['stolen_bases'])
            hitting_stats.h_war = float(request.form['h_war'])
        else:
            # If no stats exist, create new ones
            hitting_stats = Career_Stats_Hitting(
                player_id=player_id,
                batting_average=float(request.form['batting_average']),
                hits=int(request.form['hits']),
                home_runs=int(request.form['home_runs']),
                walks=int(request.form['walks']),
                strikeouts=int(request.form['strikeouts']),
                stolen_bases=int(request.form['stolen_bases']),
                h_war=float(request.form['h_war'])
            )
            db.session.add(hitting_stats)

        # Commit the changes to the database
        db.session.commit()
        return redirect('/')

    # If it's a GET request, render the hitting stats form
    return render_template('add_hitting_stats.html', player_id=player_id, stats=hitting_stats)


@app.route('/add_pitching_stats/<int:player_id>', methods=['GET', 'POST'])
def add_pitching_stats(player_id):
    player = Players.query.get_or_404(player_id)  # Get player by ID
    pitching_stats = Career_Stats_Pitching.query.filter_by(player_id=player_id).first()

    if request.method == 'POST':
        # If stats already exist, update them
        if pitching_stats:
            pitching_stats.earned_run_average = float(request.form['earned_run_average'])
            pitching_stats.saves = int(request.form['saves'])
            pitching_stats.wins = int(request.form['wins'])
            pitching_stats.walks = int(request.form['walks'])
            pitching_stats.strikeouts = int(request.form['strikeouts'])
            pitching_stats.innings = int(request.form['innings'])
            pitching_stats.p_war = float(request.form['p_war'])
        else:
            # If no stats exist, create new ones
            pitching_stats = Career_Stats_Pitching(
                player_id=player_id,
             #   player_name=player.player_name,  # Ensure player_name is passed correctly
                earned_run_average=float(request.form['earned_run_average']),
                saves=int(request.form['saves']),
                wins=int(request.form['wins']),
                walks=int(request.form['walks']),
                strikeouts=int(request.form['strikeouts']),
                innings=int(request.form['innings']),
                p_war=float(request.form['p_war'])
            )
            db.session.add(pitching_stats)

        # Commit the changes to the database
        db.session.commit()
        return redirect(f'/')  # Redirect to player's page (adjust as needed)

    # Render the form with existing pitching stats or an empty form
    return render_template('add_pitching_stats.html', player_id=player_id, player_name=player.player_name, stats=pitching_stats)

@app.route('/delete_player/<int:player_id>', methods=['POST', 'GET'])
def delete_player(player_id):
    player_to_delete = Players.query.get_or_404(player_id)

    try:
        db.session.delete(player_to_delete)
        db.session.commit()
        flash("Player and associated stats successfully deleted!", "success")
        return redirect('/')
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        flash("There was an issue deleting the player.", "error")
        return redirect('/')


@app.route('/edit_hitting_stats/<int:player_id>', methods=['GET', 'POST'])
def edit_hitting_stats(player_id):
    career_stats_hitting = Career_Stats_Hitting.query.filter_by(player_id=player_id).first_or_404()

    if request.method == 'POST':
        try:
            # Update hitting stats with form values
            hitting_stats.batting_average = request.form['batting_average']
            hitting_stats.hits = request.form['hits']
            hitting_stats.home_runs = request.form['home_runs']
            hitting_stats.walks = request.form['walks']
            hitting_stats.strikeouts = request.form['strikeouts']
            hitting_stats.stolen_bases = request.form['stolen_bases']
            hitting_stats.h_war = request.form['h_war']

            db.session.commit()
            flash(f"Player {career_stats_hitting.player_id}'s hitting stats were successfully updated!", "success")
            return redirect('/')  # Assuming this is the correct redirect
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            flash("There was an issue updating the hitting stats.", "error")
            return redirect('/')

    # Render the editing form template with the hitting stats
    return render_template('edit_hitting_stats.html', stats=hitting_stats)

@app.route('/edit_pitching_stats/<int:player_id>', methods=['GET', 'POST'])
def edit_pitching_stats(player_id):
    career_stats_pitching = Career_Stats_Pitching.query.filter_by(player_id=player_id).first_or_404()

    if request.method == 'POST':
        try:
            # Update hitting stats with form values
            pitching_stats.earned_run_average = request.form['earned_run_average']
            pitching_stats.wins = request.form['wins']
            pitching_stats.saves = request.form['saves']
            pitching_stats.walks = request.form['walks']
            pitching_stats.strikeouts = request.form['strikeouts']
            pitching_stats.innings = request.form['innings']
            pitching_stats.p_war = request.form['p_war']

            db.session.commit()
            flash(f"Player {career_stats_pitching.player_id}'s pitting stats were successfully updated!", "success")
            return redirect('/')  # Assuming this is the correct redirect
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            flash("There was an issue updating the pittting stats.", "error")
            return redirect('/')

    # Render the editing form template with the hitting stats
    return render_template('edit_pitching_stats.html', stats=pitching_stats)
@app.route('/test_pitching_data')
def test_pitching_data():
    pitching_data = Career_Stats_Pitching.query.all()
    return jsonify([{
        'player_id': stat.player_id,
       # 'player_name': stat.player_name,
        'earned_run_average': stat.earned_run_average,
        'wins': stat.wins,
        'saves': stat.saves,
        'walks': stat.walks,
        'strikeouts': stat.strikeouts,
        'innings': stat.innings,
        'p_war': stat.p_war
    } for stat in pitching_data])

with app.app_context():
    db.create_all()

# Run the Flask app
if __name__ == '__main__':
    app.run()
