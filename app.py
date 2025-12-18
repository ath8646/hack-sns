import re
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'hack_sns_secure_key'

# [Supabase 설정] - 사용자분이 주신 키 적용
SUPABASE_URL = "https://porctgadcosjzgpkxiqw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBvcmN0Z2FkY29zanpncGt4aXF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwMzc4MjYsImV4cCI6MjA4MTYxMzgyNn0.QmB0BnyLAYY0Rt3-fffExHQt4BGgWWr7USc5V9qbA2c"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# [보안] 허용된 파일 확장자 (이미지 + 동영상)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===========================
# [메인 & 게시판]
# ===========================
@app.route('/')
def index():
    try:
        response = supabase.table("posts").select("*, users(username)").order("id", desc=True).execute()
        posts = response.data
    except Exception as e:
        print(e)
        posts = []
    return render_template('index.html', posts=posts)

# ===========================
# [글 상세 보기 (조회수 & 좋아요)]
# ===========================
# app.py 의 post_detail 함수 부분

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post_res = supabase.table("posts").select("*, users(username)").eq("id", post_id).execute()
    if not post_res.data: return "글이 삭제되었거나 없습니다."
    post = post_res.data[0]

    # 🔥 [수정됨] 무한 루프 방지 로직 🔥
    # 요청 주소에 't'(시간) 파라미터가 없을 때만 조회수를 올립니다.
    # 즉, 사람이 직접 들어왔을 때만 올리고, 기계가 새로고침할 때는 안 올립니다.
    if 't' not in request.args:
        new_views = post.get('view_count', 0) + 1
        supabase.table("posts").update({"view_count": new_views}).eq("id", post_id).execute()
        post['view_count'] = new_views # 화면 표시용 업데이트

    # ... (아래는 기존 코드와 동일) ...
    votes_res = supabase.table("likes").select("*").eq("post_id", post_id).execute()
    # ...
    votes = votes_res.data
    
    like_count = len([v for v in votes if v['vote_type'] == 'like'])
    dislike_count = len([v for v in votes if v['vote_type'] == 'dislike'])
    
    my_vote = None
    if 'user_id' in session:
        for v in votes:
            if v['user_id'] == session['user_id']:
                my_vote = v['vote_type']
                break
    
    # 댓글 가져오기
    comment_res = supabase.table("comments").select("*, users(username)").eq("post_id", post_id).order("id").execute()
    all_comments = comment_res.data
    parents = [c for c in all_comments if c['parent_id'] is None]
    replies = [c for c in all_comments if c['parent_id'] is not None]
    
    return render_template('detail.html', post=post, parents=parents, replies=replies, 
                           like_count=like_count, dislike_count=dislike_count, my_vote=my_vote)

# ===========================
# [투표 기능 (AJAX - 새로고침 없음)]
# ===========================
# ===========================
# [투표 기능 (로직 재정비)]
# ===========================
# app.py 의 vote 함수 수정

@app.route('/vote/<int:post_id>/<vote_type>')
def vote(post_id, vote_type):
    if 'user_id' not in session: 
        return jsonify({'result': 'fail', 'msg': 'login_required'}), 401
    
    user_id = session['user_id']
    
    # 1. 내 투표 기록 확인
    existing = supabase.table("likes").select("*").eq("user_id", user_id).eq("post_id", post_id).execute()
    
    if existing.data:
        # 이미 투표한 기록이 있음
        old_vote = existing.data[0]
        
        if old_vote['vote_type'] == vote_type:
            # [삭제] 똑같은 걸 또 누름 -> 취소
            # match를 사용하여 user_id와 post_id가 일치하는 것을 확실하게 삭제
            supabase.table("likes").delete().match({"user_id": user_id, "post_id": post_id}).execute()
            print(f"삭제 완료: {user_id} -> {post_id}") # 터미널 로그 확인용
        else:
            # [변경] 다른 걸 누름 (좋아요 <-> 싫어요)
            supabase.table("likes").update({"vote_type": vote_type}).eq("id", old_vote['id']).execute()
            print(f"변경 완료: {user_id} -> {post_id} -> {vote_type}")
    else:
        # [추가] 기록 없음 -> 새로 생성
        supabase.table("likes").insert({
            "user_id": user_id, "post_id": post_id, "vote_type": vote_type
        }).execute()
        print(f"추가 완료: {user_id} -> {post_id} -> {vote_type}")
    
    # 2. 최신 숫자 다시 세기
    votes_res = supabase.table("likes").select("*").eq("post_id", post_id).execute()
    votes = votes_res.data
    
    new_like_count = len([v for v in votes if v['vote_type'] == 'like'])
    new_dislike_count = len([v for v in votes if v['vote_type'] == 'dislike'])
    
    # 3. 내 현재 상태 확인
    current_my_vote = None
    for v in votes:
        if v['user_id'] == user_id:
            current_my_vote = v['vote_type']
            break

    return jsonify({
        'result': 'success',
        'like_count': new_like_count,
        'dislike_count': new_dislike_count,
        'my_vote': current_my_vote
    })

# ===========================
# [글쓰기 (파일 업로드 보안 적용)]
# ===========================
@app.route('/write', methods=['POST'])
def write():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    title = request.form['title']
    content = request.form['content']
    file = request.files.get('file')
    image_url = None

    if file and file.filename != '':
        if allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                file_path = f"{session['user_id']}_{timestamp}_{filename}"
                file_content = file.read()
                
                # 파일 타입(MIME) 감지하여 업로드
                content_type = file.content_type
                supabase.storage.from_("images").upload(file_path, file_content, {"content-type": content_type})
                image_url = supabase.storage.from_("images").get_public_url(file_path)
            except Exception as e:
                print(f"업로드 에러: {e}")
        else:
            print("허용되지 않은 파일 형식입니다.")

    supabase.table("posts").insert({
        "title": title, "content": content, "image_url": image_url, "author_id": session['user_id']
    }).execute()
    
    return redirect(url_for('index'))

# ===========================
# [회원가입 / 로그인 / 기타]
# ===========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'ADMIN' and password == 'testpassword':
            session['user_id'] = 0; session['username'] = '관리자(ADMIN)'; session['is_admin'] = True
            return redirect(url_for('admin_list'))
        res = supabase.table("users").select("*").eq("username", username).execute()
        user = res.data[0] if res.data else None
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']; session['username'] = user['username']; session.pop('is_admin', None)
            return redirect(url_for('index'))
        else: return render_template('login.html', error="아이디 또는 비밀번호가 틀렸습니다.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    username_error = None; password_error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            password_error = "특수문자 필수!"; return render_template('register.html', username_error=username_error, password_error=password_error, username=username)
        hashed_pw = generate_password_hash(password)
        try:
            supabase.table("users").insert({"username": username, "password": hashed_pw}).execute()
            return redirect(url_for('login'))
        except: username_error = "이미 사용 중인 아이디입니다."
    return render_template('register.html', username_error=username_error, password_error=password_error)

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session: return redirect(url_for('login'))
    msg = None
    if request.method == 'POST':
        current_pw = request.form['current_password']; new_pw = request.form['new_password']
        res = supabase.table("users").select("*").eq("id", session['user_id']).execute(); user = res.data[0]
        if not check_password_hash(user['password'], current_pw): msg = "❌ 현재 비밀번호 오류"
        elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_pw): msg = "❌ 특수문자 필수"
        else:
            new_hashed = generate_password_hash(new_pw)
            supabase.table("users").update({"password": new_hashed}).eq("id", session['user_id']).execute()
            msg = "✅ 변경 완료!"
    return render_template('settings.html', msg=msg)

@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    content = request.form['content']; parent_id = request.form.get('parent_id')
    if parent_id == '': parent_id = None
    data = {"content": content, "post_id": post_id, "author_id": session['user_id']}
    if parent_id: data['parent_id'] = int(parent_id)
    supabase.table("comments").insert(data).execute()
    return redirect(url_for('post_detail', post_id=post_id))

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    res = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not res.data: return "글 없음"
    post = res.data[0]
    if post['author_id'] != session['user_id'] and not session.get('is_admin'): return "권한 없음", 403
    if request.method == 'POST':
        supabase.table("posts").update({"title": request.form['title'], "content": request.form['content']}).eq("id", post_id).execute()
        if session.get('is_admin'): return redirect(url_for('admin_user_detail', user_id=post['author_id']))
        return redirect(url_for('index'))
    return render_template('edit.html', post=post)

@app.route('/delete/<int:post_id>')
def delete(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    res = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not res.data: return redirect(url_for('index'))
    post = res.data[0]
    if post['author_id'] == session['user_id'] or session.get('is_admin'):
        supabase.table("posts").delete().eq("id", post_id).execute()
    if session.get('is_admin'): return redirect(url_for('admin_list'))
    return redirect(url_for('index'))

# 관리자 관련 (필요하면 추가/유지)
@app.route('/admin')
def admin_list():
    if not session.get('is_admin'): return redirect(url_for('index'))
    query = request.args.get('q', ''); res = supabase.table("users").select("*").ilike("username", f"%{query}%").order("id").execute() if query else supabase.table("users").select("*").order("id").execute()
    return render_template('admin_list.html', users=res.data, query=query)

@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
def admin_user_detail(user_id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    if request.method == 'POST':
        try: supabase.table("users").update({"username": request.form['username']}).eq("id", user_id).execute()
        except: pass
        return redirect(url_for('admin_user_detail', user_id=user_id))
    user_res = supabase.table("users").select("*").eq("id", user_id).execute(); posts_res = supabase.table("posts").select("*").eq("author_id", user_id).order("id", desc=True).execute()
    return render_template('admin_user_detail.html', user=user_res.data[0], posts=posts_res.data)

@app.route('/admin/delete_user/<int:user_id>')
def admin_delete_user(user_id):
    if not session.get('is_admin'): return "권한 없음", 403
    supabase.table("users").delete().eq("id", user_id).execute(); return redirect(url_for('admin_list'))

@app.route('/admin/update_password/<int:user_id>', methods=['POST'])
def admin_update_password(user_id):
    if not session.get('is_admin'): return "권한 없음", 403
    hashed_pw = generate_password_hash(request.form['new_password'])
    supabase.table("users").update({"password": hashed_pw}).eq("id", user_id).execute()
    return redirect(url_for('admin_user_detail', user_id=user_id))

if __name__ == '__main__':
    # 🔥 모바일(외부) 접속 허용을 위해 0.0.0.0 설정 🔥
    app.run(host='0.0.0.0', port=5000, debug=True)