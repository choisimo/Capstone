/**
 * Frontend Dashboard 메인 엔트리 포인트
 * 
 * React 애플리케이션의 진입점입니다.
 * 라우팅과 전역 스타일을 설정하고 App 컴포넌트를 렌더링합니다.
 */

import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.tsx";
import "./index.css"; // 전역 CSS 스타일

// React 18의 createRoot API를 사용하여 애플리케이션 렌더링
// root 엘리먼트에 React 앱을 마운트
createRoot(document.getElementById("root")!).render(
  <BrowserRouter> {/* React Router를 위한 BrowserRouter 래퍼 */}
    <App /> {/* 메인 App 컴포넌트 */}
  </BrowserRouter>
);
