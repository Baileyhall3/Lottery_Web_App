# IMPORTS
import copy
import logging
from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from app import db, requires_roles
from models import Draw, User
from sqlalchemy import desc

# CONFIG
lottery_blueprint = Blueprint('lottery', __name__, template_folder='templates')


# VIEWS
# view lottery page
@lottery_blueprint.route('/lottery')
@login_required
@requires_roles('user')
def lottery():
    return render_template('lottery.html')


@lottery_blueprint.route('/add_draw', methods=['POST'])
@login_required
@requires_roles('user')
def add_draw():
    submitted_draw = ''
    for i in range(6):
        submitted_draw += request.form.get('no' + str(i + 1)) + ' '
    submitted_draw.strip()

    # create a new draw with the form data.
    new_draw = Draw(user_id=current_user.id, draw=submitted_draw, win=False, round=0,
                    draw_key=current_user.draw_key)

    # add the new draw to the database
    db.session.add(new_draw)
    db.session.commit()

    # re-render lottery.page
    flash('Draw %s submitted.' % submitted_draw)
    return lottery()


# view all draws that have not been played
@lottery_blueprint.route('/view_draws', methods=['POST'])
@login_required
@requires_roles('user')
def view_draws():
    # get all draws that have not been played [played=0]
    playable_draws = Draw.query.filter_by(played=False, user_id=current_user.id).all()

    # if playable draws exist
    if len(playable_draws) != 0:

        # Shows draws in most recent order
        draws = Draw.query.order_by(desc('id')).all()

        # Empty list for decrypted and copied draw objects
        decrypted_draws = []

        # Decrypts each copied draw object to add to the decrypted_draws array
        for d in draws:
            user = User.query.filter_by(id=d.user_id).first()
            dec_draw = copy.deepcopy(d)
            dec_draw.view_draw(user.draw_key)
            decrypted_draws.append(dec_draw)

        # re-render lottery page with playable draws
        return render_template('lottery.html', playable_draws=decrypted_draws)
    else:
        flash('No playable draws.')
        return lottery()


# view lottery results
@lottery_blueprint.route('/check_draws', methods=['POST'])
@requires_roles('user')
def check_draws():
    # get played draws
    played_draws = Draw.query.filter_by(played=True, user_id=current_user.id).all()

    # if played draws exist
    if len(played_draws) != 0:

        draws = Draw.query.order_by(desc('id')).all()

        # Empty list for decrypted and copied draw objects
        decrypted_draws = []

        # Decrypts each copied draw object to add to the decrypted_draws array
        for d in draws:
            user = User.query.filter_by(id=d.user_id).first()
            dec_draw = copy.deepcopy(d)
            dec_draw.view_draw(user.draw_key)
            decrypted_draws.append(dec_draw)

        return render_template('lottery.html', results=decrypted_draws, played=True)

    # if no played draws exist [all draw entries have been played therefore wait for next lottery round]
    else:
        flash("Next round of lottery yet to play. Check you have playable draws.")
        return lottery()


# delete all played draws for current user
@lottery_blueprint.route('/play_again', methods=['POST'])
@requires_roles('user')
def play_again():
    # Deletes all draws for the current user once the winning draw has been submitted by admin
    delete_played = Draw.__table__.delete().where(Draw.played, Draw.user_id)
    db.session.execute(delete_played)
    db.session.commit()

    flash("All played draws deleted.")
    return lottery()


