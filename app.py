from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash # 보안 모듈 추가

app = Flask(__name__)
app.secret_key = 'hack_sns_secure_key'

# ==========================================
# [설정] Supabase 키 (기존 키를 그대로 쓰세요)
# ==========================================
SUPABASE_URL = "https://porctgadcosjzgpkxiqw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBvcmN0Z2FkY29zanpncGt4aXF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwMzc4MjYsImV4cCI6MjA4MTYxMzgyNn0.QmB0BnyLAYY0Rt3-fffExHQt4BGgWWr7USc5V9qbA2c"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    # 게시글 목록 (최신순)
    try:
        # 댓글 개수도 세고 싶지만, Supabase 무료버전 쿼리 제한으로 일단 글만 가져옵니다.
        response = supabase.table("posts").select("*, users(username)").order("id", desc=True).execute()
        posts = response.data
    except Exception as e:
        print(e)
        posts = []
    return render_template('index.html', posts=posts)

# [상세 보기 페이지] 댓글 기능 추가됨
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    # 1. 게시글 내용 가져오기
    post_res = supabase.table("posts").select("*, users(username)").eq("id", post_id).execute()
    if not post_res.data: return "글이 삭제되었거나 없습니다."
    post = post_res.data[0]
    
    # 2. 이 글에 달린 댓글들 가져오기
    comment_res = supabase.table("comments").select("*, users(username)").eq("post_id", post_id).order("id").execute()
    comments = comment_res.data
    
    return render_template('detail.html', post=post, comments=comments)

# [댓글 달기 기능]
@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    content = request.form['content']
    supabase.table("comments").insert({
        "content": content,
        "post_id": post_id,
        "author_id": session['user_id']
    }).execute()
    
    return redirect(url_for('post_detail', post_id=post_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # [보안 업그레이드] 비밀번호 암호화 (Hash)
        hashed_pw = generate_password_hash(password)
        
        try:
            supabase.table("users").insert({"username": username, "password": hashed_pw}).execute()
            return redirect(url_for('login'))
        except:
            return "이미 존재하는 아이디입니다."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # ID로 사용자 찾기
        response = supabase.table("users").select("*").eq("username", username).execute()
        user = response.data[0] if response.data else None

        # [보안 업그레이드] 암호화된 비밀번호 비교
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="아이디 또는 비밀번호가 틀렸습니다.")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/write', methods=['POST'])
def write():
    if 'user_id' not in session: return redirect(url_for('login'))
    supabase.table("posts").insert({
        "title": request.form['title'],
        "content": request.form['content'], # 이제 XSS 방지를 위해 | safe는 템플릿에서 뺍니다.
        "author_id": session['user_id']
    }).execute()
    return redirect(url_for('index'))

@app.route('/delete/<int:post_id>')
def delete(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    supabase.table("posts").delete().eq("id", post_id).eq("author_id", session['user_id']).execute()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)