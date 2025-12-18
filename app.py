import re
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'hack_sns_secure_key'

# [Supabase 설정]
SUPABASE_URL = "https://porctgadcosjzgpkxiqw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBvcmN0Z2FkY29zanpncGt4aXF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwMzc4MjYsImV4cCI6MjA4MTYxMzgyNn0.QmB0BnyLAYY0Rt3-fffExHQt4BGgWWr7USc5V9qbA2c"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===========================
# [메인 페이지]
# ===========================
@app.route('/')
def index():
    try:
        # 공지사항
        notices_res = supabase.table("notices").select("*").order("id", desc=True).execute()
        
        # 게시글 (작성자의 grade 포함)
        # users(username, is_admin, grade) <- grade 추가됨
        response = supabase.table("posts").select("*, users(username, is_admin, grade)").order("id", desc=True).execute()
        posts = response.data
    except Exception as e:
        print(e)
        posts = []
        notices_res = type('obj', (object,), {'data': []})
        
    return render_template('index.html', posts=posts, notices=notices_res.data)

# ===========================
# [상세 페이지]
# ===========================
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    # 작성자 정보에 grade 추가
    post_res = supabase.table("posts").select("*, users(username, is_admin, grade)").eq("id", post_id).execute()
    if not post_res.data: return "글이 삭제되었거나 없습니다."
    post = post_res.data[0]

    # 조회수 증가 (새로고침 제외)
    if 't' not in request.args:
        new_views = post.get('view_count', 0) + 1
        supabase.table("posts").update({"view_count": new_views}).eq("id", post_id).execute()
        post['view_count'] = new_views

    # 좋아요 정보
    votes_res = supabase.table("likes").select("*").eq("post_id", post_id).execute()
    votes = votes_res.data
    like_count = len([v for v in votes if v['vote_type'] == 'like'])
    dislike_count = len([v for v in votes if v['vote_type'] == 'dislike'])
    
    my_vote = None
    if 'user_id' in session:
        for v in votes:
            if v['user_id'] == session['user_id']:
                my_vote = v['vote_type']
                break
    
    # 댓글 (작성자의 grade 포함)
    comment_res = supabase.table("comments").select("*, users(username, is_admin, grade)").eq("post_id", post_id).order("id").execute()
    all_comments = comment_res.data
    parents = [c for c in all_comments if c['parent_id'] is None]
    replies = [c for c in all_comments if c['parent_id'] is not None]
    
    return render_template('detail.html', post=post, parents=parents, replies=replies, 
                           like_count=like_count, dislike_count=dislike_count, my_vote=my_vote)

# ===========================
# [관리자 기능]
# ===========================
@app.route('/admin')
def admin_list():
    if not session.get('is_admin'): return redirect(url_for('index'))
    query = request.args.get('q', '')
    if query:
        res = supabase.table("users").select("*").ilike("username", f"%{query}%").order("id").execute()
    else:
        res = supabase.table("users").select("*").order("id").execute()
    return render_template('admin_list.html', users=res.data, query=query)

@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
def admin_user_detail(user_id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    
    # 닉네임 수정
    if request.method == 'POST':
        try: supabase.table("users").update({"username": request.form['username']}).eq("id", user_id).execute()
        except: pass
        return redirect(url_for('admin_user_detail', user_id=user_id))
    
    user_res = supabase.table("users").select("*").eq("id", user_id).execute()
    posts_res = supabase.table("posts").select("*").eq("author_id", user_id).order("id", desc=True).execute()
    return render_template('admin_user_detail.html', user=user_res.data[0], posts=posts_res.data)

# 🔥 [추가] 등급 변경 기능 🔥
# app.py 의 admin_update_grade 함수를 이것으로 교체하세요!

@app.route('/admin/update_grade/<int:user_id>', methods=['POST'])
def admin_update_grade(user_id):
    if not session.get('is_admin'): return "권한 없음", 403
    
    new_grade = request.form['grade']
    
    # 🔥 [핵심] 등급이 '관리자'면 is_admin=True, 아니면 False로 자동 설정 🔥
    is_admin_flag = (new_grade == '관리자')
    
    supabase.table("users").update({
        "grade": new_grade,
        "is_admin": is_admin_flag
    }).eq("id", user_id).execute()
    
    return redirect(url_for('admin_user_detail', user_id=user_id))
@app.route('/admin/toggle_admin/<int:user_id>')
def toggle_admin(user_id):
    if not session.get('is_admin'): return "권한 없음", 403
    user_res = supabase.table("users").select("is_admin").eq("id", user_id).execute()
    if user_res.data:
        current = user_res.data[0]['is_admin']
        supabase.table("users").update({"is_admin": not current}).eq("id", user_id).execute()
    return redirect(url_for('admin_user_detail', user_id=user_id))

@app.route('/notice/write', methods=['POST'])
def write_notice():
    if not session.get('is_admin'): return "권한 없음", 403
    supabase.table("notices").insert({"content": request.form['content']}).execute()
    return redirect(url_for('index'))

@app.route('/notice/delete/<int:notice_id>')
def delete_notice(notice_id):
    if not session.get('is_admin'): return "권한 없음", 403
    supabase.table("notices").delete().eq("id", notice_id).execute()
    return redirect(url_for('index'))

@app.route('/admin/delete_user/<int:user_id>')
def admin_delete_user(user_id):
    if not session.get('is_admin'): return "권한 없음", 403
    supabase.table("users").delete().eq("id", user_id).execute()
    return redirect(url_for('admin_list'))

@app.route('/admin/update_password/<int:user_id>', methods=['POST'])
def admin_update_password(user_id):
    if not session.get('is_admin'): return "권한 없음", 403
    hashed = generate_password_hash(request.form['new_password'])
    supabase.table("users").update({"password": hashed}).eq("id", user_id).execute()
    return redirect(url_for('admin_user_detail', user_id=user_id))

# ===========================
# [기본 기능 (로그인, 글쓰기 등)]
# ===========================
@app.route('/vote/<int:post_id>/<vote_type>')
def vote(post_id, vote_type):
    if 'user_id' not in session: return jsonify({'result': 'fail', 'msg': 'login_required'}), 401
    user_id = session['user_id']
    existing = supabase.table("likes").select("*").eq("user_id", user_id).eq("post_id", post_id).execute()
    if existing.data:
        old = existing.data[0]
        if old['vote_type'] == vote_type:
            supabase.table("likes").delete().match({"user_id": user_id, "post_id": post_id}).execute()
        else:
            supabase.table("likes").update({"vote_type": vote_type}).eq("id", old['id']).execute()
    else:
        supabase.table("likes").insert({"user_id": user_id, "post_id": post_id, "vote_type": vote_type}).execute()
    
    votes = supabase.table("likes").select("*").eq("post_id", post_id).execute().data
    like = len([v for v in votes if v['vote_type'] == 'like'])
    dislike = len([v for v in votes if v['vote_type'] == 'dislike'])
    my_vote = None
    for v in votes:
        if v['user_id'] == user_id: my_vote = v['vote_type']; break
    return jsonify({'result': 'success', 'like_count': like, 'dislike_count': dislike, 'my_vote': my_vote})

@app.route('/write', methods=['POST'])
def write():
    if 'user_id' not in session: return redirect(url_for('login'))
    title = request.form['title']; content = request.form['content']; file = request.files.get('file'); image_url = None
    if file and file.filename != '':
        if allowed_file(file.filename):
            try:
                fn = secure_filename(file.filename); ts = datetime.now().strftime("%Y%m%d%H%M%S")
                fp = f"{session['user_id']}_{ts}_{fn}"
                supabase.storage.from_("images").upload(fp, file.read(), {"content-type": file.content_type})
                image_url = supabase.storage.from_("images").get_public_url(fp)
            except Exception as e: print(e)
    supabase.table("posts").insert({"title": title, "content": content, "image_url": image_url, "author_id": session['user_id']}).execute()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']; password = request.form['password']
        
        # 1. 슈퍼 관리자 처리 (아이디가 ADMIN일 때)
        if username == 'ADMIN' and password == 'testpassword':
            session['user_id'] = 0
            session['username'] = '관리자(ADMIN)'
            session['is_admin'] = True
            session['grade'] = '관리자' # ✅ 추가: 슈퍼 관리자 등급 강제 지정
            return redirect(url_for('admin_list'))
            
        # 2. 일반 유저 및 관리자 유저 처리
        res = supabase.table("users").select("*").eq("username", username).execute()
        
        if res.data and check_password_hash(res.data[0]['password'], password):
            user = res.data[0]
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)
            
            # ✅ 이 부분을 아래 코드로 교체하세요 (등급 정보 가져오기)
            session['grade'] = user.get('grade') if user.get('grade') else '일반 회원'
            
            return redirect(url_for('index'))
        else: 
            return render_template('login.html', error="아이디 또는 비밀번호 오류")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    username_error = None; password_error = None
    if request.method == 'POST':
        username = request.form['username']; password = request.form['password']
        
        # 정규표현식 수정: a-z, A-Z, 가-힣 에 0-9(숫자)를 추가함
        if not re.match(r'^[a-zA-Z가-힣0-9]+$', username):
            username_error = "아이디는 영어, 한글, 숫자만 가능합니다!"
            return render_template('register.html', username_error=username_error, password_error=password_error, username=username)
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            password_error = "특수문자 필수!"
            return render_template('register.html', username_error=username_error, password_error=password_error, username=username)
        
        try:
            supabase.table("users").insert({"username": username, "password": generate_password_hash(password)}).execute()
            return redirect(url_for('login'))
        except: 
            username_error = "이미 사용 중인 아이디입니다."
            
    return render_template('register.html', username_error=username_error, password_error=password_error)

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session: return redirect(url_for('login'))
    if session['user_id'] == 0: return render_template('settings.html', msg="🔒 슈퍼 관리자는 비밀번호 변경 불가")
    msg = None
    if request.method == 'POST':
        cur = request.form['current_password']; new = request.form['new_password']
        user = supabase.table("users").select("*").eq("id", session['user_id']).execute().data[0]
        if not check_password_hash(user['password'], cur): msg = "❌ 현재 비밀번호 오류"
        elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', new): msg = "❌ 특수문자 필수"
        else:
            supabase.table("users").update({"password": generate_password_hash(new)}).eq("id", session['user_id']).execute()
            msg = "✅ 변경 완료!"
    return render_template('settings.html', msg=msg)

@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    content = request.form['content']; parent_id = request.form.get('parent_id') or None
    data = {"content": content, "post_id": post_id, "author_id": session['user_id']}
    if parent_id: data['parent_id'] = int(parent_id)
    supabase.table("comments").insert(data).execute()
    return redirect(url_for('post_detail', post_id=post_id))

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    post = supabase.table("posts").select("*").eq("id", post_id).execute().data[0]
    if post['author_id'] != session['user_id'] and not session.get('is_admin'): return "권한 없음", 403
    if request.method == 'POST':
        supabase.table("posts").update({"title": request.form['title'], "content": request.form['content']}).eq("id", post_id).execute()
        return redirect(url_for('index'))
    return render_template('edit.html', post=post)

@app.route('/delete/<int:post_id>')
def delete(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    post = supabase.table("posts").select("*").eq("id", post_id).execute().data[0]
    if post['author_id'] == session['user_id'] or session.get('is_admin'):
        supabase.table("posts").delete().eq("id", post_id).execute()
    if session.get('is_admin'): return redirect(url_for('admin_list'))
    return redirect(url_for('index'))

# ===========================
# [지렁이 게임 기능]
# ===========================
@app.route('/game')
def game_page():
    return render_template('snake.html')

@app.route('/api/save_score', methods=['POST'])
def save_score():
    if 'user_id' not in session: return jsonify({'result': 'fail', 'msg': '로그인 필요'})
    data = request.json
    score = data.get('score')
    
    # 최고 기록 갱신일 때만 저장하거나, 무조건 저장하거나 선택 (여기선 무조건 저장)
    supabase.table("snake_scores").insert({
        "user_id": session['user_id'],
        "score": score
    }).execute()
    return jsonify({'result': 'success'})

# app.py 의 get_rankings 함수 수정

@app.route('/api/get_rankings')
def get_rankings():
    # 🔥 [수정] leaderboard 뷰에서 가져오기 (이미 유저별 최고점수로 정리됨)
    res = supabase.table("leaderboard").select("*").order("score", desc=True).limit(10).execute()
    return jsonify(res.data)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)