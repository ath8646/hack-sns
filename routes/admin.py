from flask import Blueprint, render_template, request, redirect, url_for, session
from db_config import supabase
from werkzeug.security import generate_password_hash # 🔥 비밀번호 암호화를 위해 추가

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin_list():
    if not session.get('is_admin'): return redirect(url_for('main.index'))
    query = request.args.get('q', '')
    if query: res = supabase.table("users").select("*").ilike("username", f"%{query}%").order("id").execute()
    else: res = supabase.table("users").select("*").order("id").execute()
    return render_template('admin_list.html', users=res.data, query=query)

# 1. 유저 상세 페이지 (갤러리 목록 로드 기능 추가)
@admin_bp.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
def admin_user_detail(user_id):
    if not session.get('is_admin'): return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        supabase.table("users").update({"username": request.form['username']}).eq("id", user_id).execute()
        return redirect(url_for('admin.admin_user_detail', user_id=user_id))
    
    # 기본 정보 및 게시글 로드
    user = supabase.table("users").select("*").eq("id", user_id).execute().data[0]
    posts = supabase.table("posts").select("*").eq("author_id", user_id).order("id", desc=True).execute().data
    
    # 🔥 [추가] 유저가 만든 갤러리 목록 로드
    user_galleries = supabase.table("galleries").select("*").eq("creator_id", user_id).execute().data
    
    return render_template('admin_user_detail.html', user=user, posts=posts, user_galleries=user_galleries)

# 2. 유저 비밀번호 강제 재설정 (새로 추가)
@admin_bp.route('/admin/reset_pw/<int:user_id>')
def reset_pw(user_id):
    if not session.get('is_admin'): return "권한 없음", 403
    new_pw = request.args.get('new_pw')
    if not new_pw: return "비밀번호 없음", 400
    
    hashed_pw = generate_password_hash(new_pw)
    supabase.table("users").update({"password": hashed_pw}).eq("id", user_id).execute()
    
    return f"<script>alert('비밀번호가 변경되었습니다.'); location.href='/admin/user/{user_id}';</script>"

# 3. 유저가 만든 갤러리 강제 삭제 (새로 추가)
@admin_bp.route('/admin/delete_gallery/<int:gallery_id>')
def admin_delete_gallery(gallery_id):
    if not session.get('is_admin'): return "권한 없음", 403
    u_id = request.args.get('u_id') # 돌아올 유저 ID
    
    # 갤러리 삭제 (외래키 오류 방지를 위해 게시글 먼저 삭제 권장)
    supabase.table("posts").delete().eq("gallery_id", gallery_id).execute()
    supabase.table("galleries").delete().eq("id", gallery_id).execute()
    
    return f"<script>alert('해당 갤러리와 모든 게시글이 삭제되었습니다.'); location.href='/admin/user/{u_id}';</script>"

# 4. 유저가 만든 보안 갤러리 비밀번호 강제 변경 (새로 추가)
@admin_bp.route('/admin/gallery_pw/<int:gallery_id>')
def admin_gallery_pw(gallery_id):
    if not session.get('is_admin'): return "권한 없음", 403
    new_pw = request.args.get('new_pw')
    u_id = request.args.get('u_id')
    
    supabase.table("galleries").update({"password": new_pw}).eq("id", gallery_id).execute()
    return f"<script>alert('갤러리 비밀번호가 성공적으로 변경되었습니다.'); location.href='/admin/user/{u_id}';</script>"

@admin_bp.route('/admin/update_grade/<int:user_id>', methods=['POST'])
def admin_update_grade(user_id):
    if not session.get('is_admin'): 
        return "권한 없음", 403
    
    new_grade = request.form['grade']
    is_admin_flag = (new_grade == '관리자')

    # 1. DB 업데이트
    supabase.table("users").update({
        "grade": new_grade, 
        "is_admin": is_admin_flag
    }).eq("id", user_id).execute()

    # 2. 🔥 [추가] 만약 관리자가 '본인'의 등급을 수정 중이라면 세션도 즉시 갱신
    # (다른 유저의 등급을 수정하는 경우 그 유저의 세션을 서버에서 직접 건드리기는 어렵지만, 
    #  본인 확인용 로직은 아래와 같이 추가할 수 있습니다.)
    if session.get('user_id') == user_id:
        session['grade'] = new_grade
        session['is_admin'] = is_admin_flag

    return redirect(url_for('admin.admin_user_detail', user_id=user_id))
@admin_bp.route('/notice/write', methods=['POST'])
def write_notice():
    if not session.get('is_admin'): return "권한 없음", 403
    supabase.table("notices").insert({"content": request.form['content']}).execute()
    return redirect(url_for('main.index'))

@admin_bp.route('/notice/delete/<int:notice_id>')
def delete_notice(notice_id):
    if not session.get('is_admin'): return "권한 없음", 403
    supabase.table("notices").delete().eq("id", notice_id).execute()
    return redirect(url_for('main.index'))