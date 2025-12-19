from flask import Blueprint, render_template, request, session, jsonify
from db_config import supabase

game_bp = Blueprint('game', __name__)

@game_bp.route('/game')
def game_page():
    return render_template('snake.html')

@game_bp.route('/api/save_score', methods=['POST'])
def save_score():
    if 'user_id' not in session: return jsonify({'result': 'fail'})
    data = request.json
    supabase.table("snake_scores").insert({"user_id": session['user_id'], "score": data.get('score')}).execute()
    return jsonify({'result': 'success'})

@game_bp.route('/api/get_rankings')
def get_rankings():
    res = supabase.table("leaderboard").select("*").order("score", desc=True).limit(10).execute()
    return jsonify(res.data)
