import React, { useState, useRef } from 'react';
// [필수 확인] 실제 프로젝트에서는 아래 import 문 주석을 해제하고 터미널에 'npm install @emailjs/browser'를 입력해 설치하세요.
import emailjs from '@emailjs/browser'; 
import { BookOpen, Star, Phone, Mail, MapPin, Menu, X, ChevronRight, Send, User, Check } from 'lucide-react';

const GreenGablesStudent = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('elementary');

  // 1. 폼을 선택하기 위한 변수 설정
  const form = useRef();

  const scrollToSection = (id) => {
    setIsMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // 2. 이메일 보내는 함수
  const sendEmail = (e) => {
    e.preventDefault();

    // [미리보기용 알림] - 실제 환경에서는 이 부분을 지우셔도 됩니다.
    if (typeof emailjs === 'undefined') {
      alert('EmailJS가 설치되지 않았습니다. VS Code에서 npm install @emailjs/browser 후 import 주석을 해제해주세요.\n(전송 성공 시뮬레이션)');
      window.location.reload();
      return;
    }

    // [실제 전송 코드] - import 주석을 해제하면 아래 코드가 작동합니다.
    
    emailjs
      .sendForm(
        'service_5aqys7k',   // EmailJS 서비스 ID
        'template_6rh8g75',  // EmailJS 템플릿 ID
        form.current,
        {
          publicKey: 'ecgmkdF6Ofi7WQjke', // EmailJS Public Key
        }
      )
      .then(
        () => {
          alert('상담 신청이 완료되었습니다! 선생님이 곧 연락드릴게요 😊');
          window.location.reload();
        },
        (error) => {
          alert('전송 실패... 다시 시도해주세요.');
          console.log('FAILED...', error.text);
        },
      );
    
  };

  return (
    <div className="font-sans text-gray-800 bg-[#fdfdf0] min-h-screen">
      {/* Navigation */}
      <nav className="bg-green-600 text-white p-4 sticky top-0 z-50 shadow-md">
        <div className="container mx-auto flex justify-between items-center">
          <div 
            className="text-xl md:text-2xl font-black flex items-center gap-2 cursor-pointer hover:scale-105 transition-transform"
            onClick={() => window.scrollTo(0,0)}
          >
            <BookOpen fill="white" />
            <span>Green Gables</span>
          </div>
          
          {/* Desktop Menu */}
          <div className="hidden md:flex space-x-6 font-bold">
            {['학원소개', '커리큘럼', '수강후기', 'FAQ'].map((item, idx) => (
              <button 
                key={idx}
                onClick={() => scrollToSection(['about', 'curriculum', 'reviews', 'faq'][idx])}
                className="hover:text-yellow-300 transition-colors"
              >
                {item}
              </button>
            ))}
            <button 
              onClick={() => scrollToSection('contact')}
              className="bg-yellow-400 text-green-900 px-4 py-2 rounded-full hover:bg-yellow-300 transition-colors shadow-sm"
            >
              상담신청 Go!
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button className="md:hidden" onClick={() => setIsMenuOpen(!isMenuOpen)}>
            {isMenuOpen ? <X /> : <Menu />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="absolute top-full left-0 w-full bg-green-500 border-t border-green-400">
            {['학원소개', '커리큘럼', '수강후기', 'FAQ', '상담신청'].map((item, idx) => (
              <button 
                key={idx}
                onClick={() => scrollToSection(['about', 'curriculum', 'reviews', 'faq', 'contact'][idx])}
                className="block w-full text-left py-3 px-6 font-bold hover:bg-green-600 border-b border-green-400 last:border-none"
              >
                {item}
              </button>
            ))}
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <header className="bg-green-100 py-16 px-6 text-center border-b-4 border-green-200">
        <div className="container mx-auto max-w-4xl">
          <span className="inline-block bg-white text-green-700 px-4 py-1 rounded-full text-sm font-bold mb-4 shadow-sm border border-green-200">
            🌱 영어 실력이 쑥쑥 자라는 곳
          </span>
          <h1 className="text-4xl md:text-6xl font-black text-green-800 mb-6 leading-tight">
            Green Gables에서<br/>
            <span className="text-green-600 bg-yellow-000 px-2 rounded-lg">영어의 재미</span>를 찾다!
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            균형잡힌 수업으로 영어 실력을 올리고, 꼼꼼한 문법으로 내신까지 잡아요.<br/>
            선생님과 학생이 함께 성장하는 즐거운 영어 교실입니다. :)
          </p>
          
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <button 
              onClick={() => scrollToSection('contact')}
              className="bg-green-600 text-white text-lg font-bold px-8 py-4 rounded-xl shadow-lg hover:bg-green-700 hover:-translate-y-1 transition-all flex items-center justify-center gap-2"
            >
              레벨테스트 신청하기 <Send size={20} />
            </button>
            <button 
              onClick={() => scrollToSection('curriculum')}
              className="bg-white text-green-700 border-2 border-green-600 text-lg font-bold px-8 py-4 rounded-xl hover:bg-green-50 transition-all"
            >
              수업 구경하기
            </button>
          </div>

          {/* Simple Image Card */}
          <div className="mt-12 mx-auto max-w-3xl bg-white p-3 rounded-3xl shadow-xl border-4 border-green-200 rotate-1 hover:rotate-0 transition-transform duration-500">
            <img 
              src="https://images.unsplash.com/photo-1503676260728-1c00da094a0b?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80" 
              alt="Classroom" 
              className="w-full h-64 md:h-96 object-cover rounded-2xl"
            />
            <div className="pt-3 font-bold text-green-800 flex justify-center items-center gap-2">
              <span>Since 2018</span>
              <span className="text-gray-300">|</span>
              <span>즐거운 영어 교실 🏫</span>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Section */}
      <section className="py-12 container mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "공부 집중도", value: "200%" },
            { label: "내신 1등급", value: "45%" },
            { label: "등급 성장률", value: "1~2등급" },
            { label: "학생 만족도", value: "98%" },
          ].map((stat, idx) => (
            <div key={idx} className="bg-white p-6 rounded-2xl border-2 border-gray-100 shadow-md text-center hover:border-green-300 transition-colors">
              <p className="text-3xl font-black text-green-600 mb-1">{stat.value}</p>
              <p className="text-gray-500 font-bold text-sm">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-black text-gray-800 mb-3">Green Gables는 이렇게 달라요!</h2>
            <div className="w-20 h-2 bg-green-500 mx-auto rounded-full"></div>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: "📚", title: "리딩 클럽", desc: "재미있는 리딩을 읽으며 자연스럽게 실력을 키워요." },
              { icon: "✍️", title: "1:1 문법 클리닉", desc: "모르는 건 알 때까지! 학생마다 부족한 부분을 콕 집어서 알려줍니다." },
              { icon: "💯", title: "철저한 내신 대비", desc: "우리 학교 시험 문제 완벽 분석! 교과서 암기부터 변형 문제까지 책임져요." }
            ].map((item, idx) => (
              <div key={idx} className="bg-green-50 p-8 rounded-3xl border border-green-100 hover:shadow-xl hover:bg-green-100 transition-all duration-300 group">
                <div className="text-5xl mb-4 group-hover:scale-110 transition-transform duration-300">{item.icon}</div>
                <h3 className="text-xl font-bold text-green-900 mb-3">{item.title}</h3>
                <p className="text-gray-700 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Curriculum Section */}
      <section id="curriculum" className="py-16 bg-green-800 text-white">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl font-black text-center mb-10">단계별 커리큘럼 📝</h2>
          
          <div className="flex justify-center gap-2 mb-8 flex-wrap">
            {['elementary', 'middle', 'high'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-3 rounded-full font-bold text-lg transition-all border-2 ${
                  activeTab === tab 
                    ? 'bg-yellow-400 text-green-900 border-yellow-400' 
                    : 'bg-transparent text-white border-green-600 hover:bg-green-700'
                }`}
              >
                {tab === 'elementary' ? '초등부' : tab === 'middle' ? '중등부' : '고등부'}
              </button>
            ))}
          </div>

          <div className="bg-white text-gray-800 rounded-3xl p-8 md:p-12 shadow-2xl max-w-4xl mx-auto">
            {activeTab === 'elementary' && (
              <div className="animate-fade-in text-center md:text-left">
                <h3 className="text-2xl font-black text-green-600 mb-4 border-b-2 border-gray-100 pb-2">Passionate Class (열정 영어)</h3>
                <ul className="space-y-4 text-lg">
                  <li className="flex items-center gap-3">
                    <Check className="text-green-500" /> <span><b>재밌는 리딩</b></span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="text-green-500" /> <span>암송으로 회화 연습</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="text-green-500" /> <span>매일매일 <b>단어</b> 쓰기</span>
                  </li>
                </ul>
              </div>
            )}
            {activeTab === 'middle' && (
              <div className="animate-fade-in text-center md:text-left">
                <h3 className="text-2xl font-black text-indigo-600 mb-4 border-b-2 border-gray-100 pb-2">Intensive Course (내신 집중)</h3>
                <ul className="space-y-4 text-lg">
                  <li className="flex items-center gap-3">
                    <Check className="text-indigo-500" /> <span>중등 필수 영문법 <b>3번 반복</b> 완성</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="text-indigo-500" /> <span>수행평가 완벽 대비 (감점 제로 도전!)</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="text-indigo-500" /> <span>매주 단어 100+개 암기 테스트</span>
                  </li>
                </ul>
              </div>
            )}
            {activeTab === 'high' && (
              <div className="animate-fade-in text-center md:text-left">
                <h3 className="text-2xl font-black text-red-500 mb-4 border-b-2 border-gray-100 pb-2">Master Course (수능 실전)</h3>
                <ul className="space-y-4 text-lg">
                  <li className="flex items-center gap-3">
                    <Check className="text-red-500" /> <span>고3 평가원 모의고사 기출 분석</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="text-red-500" /> <span>빈칸, 순서 등 <b>킬러 유형</b> 집중 공략</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="text-red-500" /> <span>E변형 문제 풀이</span>
                  </li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Reviews Section */}
      <section id="reviews" className="py-16 bg-[#fdfdf0]">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl font-black text-center mb-12">학생들의 생생 후기 💬</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                text: "우와 정말 좋아요!",
                author: "중2 안OO 학생",
                color: "bg-yellow-100"
              },
              {
                text: "분위기가 좋아요",
                author: "중2 우OO 학생",
                color: "bg-blue-100"
              },
              {
                text: "고등 올라가서 막막했는데 유형별로 푸는 법 알려주셔서 1등급 유지 중입니다.",
                author: "고2 김OO 학생",
                color: "bg-pink-100"
              }
            ].map((review, idx) => (
              <div key={idx} className={`${review.color} p-6 shadow-lg transform hover:-translate-y-2 transition-transform duration-300`} style={{ borderRadius: '4px 20px 4px 20px' }}>
                <div className="flex text-yellow-500 mb-3">
                  {[...Array(5)].map((_, i) => <Star key={i} size={18} fill="currentColor" />)}
                </div>
                <p className="text-gray-700 font-medium mb-4 leading-relaxed">"{review.text}"</p>
                <div className="border-t border-black/10 pt-3">
                  <p className="font-bold text-gray-900 text-right">- {review.author}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-16 bg-white border-t-4 border-green-100">
        <div className="container mx-auto px-6 max-w-3xl">
          <h2 className="text-3xl font-black text-center mb-10">궁금한 점이 있나요?</h2>
          <div className="space-y-4">
            {[
              { q: "한 반 정원은 몇 명인가요?", a: "최대 3~4명 꼼꼼하게 봐드립니다." },
              { q: "입학 테스트가 있나요?", a: "네, 간단한 레벨 테스트 후 반 배정이 됩니다." },
              { q: "시험 기간에는요?", a: "4주 전부터 학교별 내신 대비 모드로 전환됩니다!" }
            ].map((item, idx) => (
              <details key={idx} className="bg-gray-50 p-5 rounded-xl border border-gray-200 cursor-pointer hover:bg-gray-100">
                <summary className="flex items-center justify-between font-bold text-lg text-gray-800 list-none">
                  Q. {item.q}
                  <ChevronRight size={20} className="text-gray-400" />
                </summary>
                <p className="mt-3 text-gray-600 pl-4 border-l-4 border-green-400">
                  A. {item.a}
                </p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section - EmailJS 적용 부분 */}
      <section id="contact" className="py-16 bg-green-900 text-white">
        <div className="container mx-auto px-6">
          <div className="flex flex-col lg:flex-row gap-12 items-center">
            <div className="lg:w-1/2 text-center lg:text-left">
              <h2 className="text-4xl font-black mb-6 text-yellow-300">Green Gables에서 시작하세요!</h2>
              <p className="text-green-100 mb-8 text-xl">
                상담 예약하고 방문하시면<br/>
                <b>레벨 테스트가 무료</b>입니다! 🎉
              </p>
              
              <div className="bg-green-800 p-6 rounded-2xl inline-block w-full max-w-md border border-green-700">
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="bg-white text-green-800 p-3 rounded-full"><Phone size={24} /></div>
                    <div className="text-left">
                      <p className="text-green-300 text-sm">상담 문의</p>
                      <p className="text-2xl font-bold">010-2598-0550</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="bg-white text-green-800 p-3 rounded-full"><MapPin size={24} /></div>
                    <div className="text-left">
                      <p className="text-green-300 text-sm">오시는 길</p>
                      <p className="text-lg font-bold">서울 종로구 이화동 대학로5가길 근처</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:w-1/2 w-full max-w-md bg-white text-gray-800 p-8 rounded-3xl shadow-2xl">
              <h3 className="text-2xl font-black mb-6 text-center">🚀 상담 예약하기</h3>
              
              {/* 3. form 태그에 ref와 onSubmit 연결 */}
              <form ref={form} className="space-y-4" onSubmit={sendEmail}>
                <div>
                  <label className="block text-sm font-bold text-gray-600 mb-1">학생 이름</label>
                  {/* name 속성이 중요합니다! EmailJS 템플릿의 변수명과 일치해야 함 */}
                  <input type="text" name="user_name" className="w-full px-4 py-3 bg-gray-100 border-2 border-transparent focus:border-green-500 rounded-lg outline-none transition-colors" placeholder="이름 입력" required />
                </div>
                <div>
                  <label className="block text-sm font-bold text-gray-600 mb-1">학년</label>
                  <select name="user_grade" className="w-full px-4 py-3 bg-gray-100 border-2 border-transparent focus:border-green-500 rounded-lg outline-none">
                    <option value="초등부">초등부</option>
                    <option value="중등부">중등부</option>
                    <option value="고등부">고등부</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-bold text-gray-600 mb-1">연락처</label>
                  <input type="tel" name="user_phone" className="w-full px-4 py-3 bg-gray-100 border-2 border-transparent focus:border-green-500 rounded-lg outline-none" placeholder="010-0000-0000" required />
                </div>
                <button type="submit" className="w-full bg-green-600 text-white font-black py-4 rounded-xl hover:bg-green-700 hover:shadow-lg transition-all text-lg">
                  상담 신청하기
                </button>
              </form>
            </div>
          </div>
        </div>
      </section>

      <footer className="bg-black text-gray-500 py-8 text-center text-sm">
        <p>&copy; 2025 Green Gables & English Class. All rights reserved.</p>
        <p className="mt-2">Made by ANTAEHOON</p>
      </footer>
    </div>
  );
};

export default GreenGablesStudent;