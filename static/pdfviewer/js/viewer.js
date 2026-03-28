/**
 * 전자칠판 웹 PDF 뷰어 — 완전판
 * pdf_viewer.py (PyQt6) 전 기능 JavaScript/Canvas 포팅
 */
document.addEventListener('DOMContentLoaded', function() {
'use strict';

// ========== PDF.js 초기화 ==========
if (!window.pdfjsLib) {
    console.error('PDF.js not loaded'); return;
}
const pdfjs = window.pdfjsLib;
pdfjs.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

// ========== 상태 ==========
const state = {
    pdfDoc: null,
    pages: [],           // [{pdfCanvas, drawCanvas, pdfCtx, drawCtx, viewport, wrapper, rendered}]
    totalPages: 0,
    currentPage: 1,
    zoom: 1.0,
    fitMode: 'width',

    tool: 'pen',
    color: '#ff0000',
    width: 3,
    drawing: false,
    lastPoint: null,
    currentPath: [],

    drawItems: {},       // { pageNum: [{path, color, width, tool, path2d}] }
    chalkItems: [],

    chalkboardMode: false,
    chalkTexture: null,
    chalkBrushPattern: null, // 분필 텍스처 패턴

    // 지우개
    eraserDragging: false,
    eraserOffset: { x: 0, y: 0 },
    eraserRecentDx: [],  // 와이퍼 기울기용
    eraserAngle: 0,      // 현재 기울기 각도
    eraserWobble: 0,     // 흔들림 각도

    // 핀치 줌
    pinchStartDist: 0,
    pinchStartZoom: 1.0,
    pointers: new Map(),

    // 썸네일
    thumbsVisible: false,

    // 상태 저장
    savedColor: '#ff0000',
    savedTool: 'pen',
};

// ========== DOM ==========
const $ = id => document.getElementById(id);
const pdfMode = $('pdf-mode');
const chalkMode = $('chalk-mode');
const scrollContainer = $('pdf-scroll-container');
const pagesContainer = $('pdf-pages-container');
const chalkCanvas = $('chalk-canvas');
const chalkCtx = chalkCanvas.getContext('2d');
const chalkDate = $('chalk-date');
const eraserPanel = $('eraser-panel');
const toolbar = $('toolbar');
const pageInput = $('page-input');
const totalPagesSpan = $('total-pages');
const zoomLabel = $('zoom-label');
const colorDot = $('color-dot');
const colorPopup = $('color-popup');
const widthPopup = $('width-popup');
const thumbPanel = $('thumb-panel');

// ========== 유틸 ==========
function mulberry32(seed) {
    return function () {
        seed |= 0; seed = seed + 0x6D2B79F5 | 0;
        let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
}
function gaussRandom(rng) {
    let u = 0, v = 0;
    while (u === 0) u = rng();
    while (v === 0) v = rng();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

// ========== localStorage 상태 저장/복원 ==========
function saveState() {
    try {
        localStorage.setItem('pdfviewer_color', state.color);
        localStorage.setItem('pdfviewer_width', state.width);
        localStorage.setItem('pdfviewer_tool', state.tool);
    } catch (e) {}
}
function restoreState() {
    try {
        const c = localStorage.getItem('pdfviewer_color');
        const w = localStorage.getItem('pdfviewer_width');
        const t = localStorage.getItem('pdfviewer_tool');
        if (c) state.color = c;
        if (w) state.width = parseInt(w);
        if (t && ['pen', 'highlighter', 'chalk'].includes(t)) state.tool = t;
    } catch (e) {}
}

// ========== PDF 로드 (가상화: 보이는 페이지만 렌더) ==========
async function loadPDF() {
    const loadingTask = pdfjs.getDocument(window.PDF_URL);
    state.pdfDoc = await loadingTask.promise;
    state.totalPages = state.pdfDoc.numPages;
    totalPagesSpan.textContent = state.totalPages;
    pageInput.max = state.totalPages;

    // 모든 placeholder를 순서대로 생성 (await)
    for (let i = 1; i <= state.totalPages; i++) {
        await createPagePlaceholder(i);
    }

    fitToWidth();
    scrollContainer.scrollTop = 0;

    // 처음 보이는 5페이지는 즉시 렌더링
    for (let i = 1; i <= Math.min(5, state.totalPages); i++) {
        await renderPageIfNeeded(i);
    }

    // 나머지는 IntersectionObserver로 lazy 렌더링
    setupIntersectionObserver();

    // 스크롤 이벤트로 현재 페이지 추적
    scrollContainer.addEventListener('scroll', updateCurrentPage);

    // 썸네일 생성 (비동기)
    generateThumbnails();
}

async function createPagePlaceholder(pageNum) {
    const page = await state.pdfDoc.getPage(pageNum);
    const viewport = page.getViewport({ scale: 1.0 });

    const wrapper = document.createElement('div');
    wrapper.className = 'pdf-page-wrapper';
    wrapper.dataset.page = pageNum;
    wrapper.style.width = viewport.width + 'px';
    wrapper.style.height = viewport.height + 'px';

    // 아직 캔버스는 안 만듦 (placeholder 흰색 박스)
    pagesContainer.appendChild(wrapper);

    state.pages.push({ wrapper, viewport, rendered: false, pdfCanvas: null, drawCanvas: null, pdfCtx: null, drawCtx: null });
    if (!state.drawItems[pageNum]) state.drawItems[pageNum] = [];
}

// IntersectionObserver: 뷰포트 ± 3페이지 사전 렌더링
function setupIntersectionObserver() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const pageNum = parseInt(entry.target.dataset.page);
            if (entry.isIntersecting) {
                renderPageIfNeeded(pageNum);
                // 전후 3페이지 사전 렌더링
                for (let d = 1; d <= 3; d++) {
                    renderPageIfNeeded(pageNum - d);
                    renderPageIfNeeded(pageNum + d);
                }
            }
        });
    }, { root: scrollContainer, rootMargin: '200px 0px' });

    state.pages.forEach(p => observer.observe(p.wrapper));
}

async function renderPageIfNeeded(pageNum) {
    if (pageNum < 1 || pageNum > state.totalPages) return;
    const pageData = state.pages[pageNum - 1];
    if (pageData.rendered) return;
    pageData.rendered = true;

    const page = await state.pdfDoc.getPage(pageNum);
    const dpr = window.devicePixelRatio || 1;
    const vp = pageData.viewport;

    // PDF 캔버스
    const pdfCanvas = document.createElement('canvas');
    pdfCanvas.className = 'pdf-canvas';
    pdfCanvas.width = vp.width * dpr;
    pdfCanvas.height = vp.height * dpr;
    const pdfCtx = pdfCanvas.getContext('2d');
    pdfCtx.scale(dpr, dpr);
    await page.render({ canvasContext: pdfCtx, viewport: vp }).promise;

    // 그리기 캔버스
    const drawCanvas = document.createElement('canvas');
    drawCanvas.className = 'draw-canvas';
    drawCanvas.width = vp.width * dpr;
    drawCanvas.height = vp.height * dpr;
    const drawCtx = drawCanvas.getContext('2d');
    drawCtx.scale(dpr, dpr);

    pageData.wrapper.appendChild(pdfCanvas);
    pageData.wrapper.appendChild(drawCanvas);
    pageData.pdfCanvas = pdfCanvas;
    pageData.drawCanvas = drawCanvas;
    pageData.pdfCtx = pdfCtx;
    pageData.drawCtx = drawCtx;

    setupDrawEvents(drawCanvas, pageNum);
    redrawPage(pageNum);
}

// ========== 줌 ==========
function setZoom(z) {
    state.zoom = Math.max(0.3, Math.min(5.0, z));
    zoomLabel.textContent = Math.round(state.zoom * 100) + '%';
    state.pages.forEach(p => {
        const w = p.viewport.width * state.zoom;
        const h = p.viewport.height * state.zoom;
        p.wrapper.style.width = w + 'px';
        p.wrapper.style.height = h + 'px';
    });
}

function fitToWidth() {
    if (!state.pages.length) return;
    state.fitMode = 'width';
    const containerW = scrollContainer.clientWidth - 20;
    setZoom(containerW / state.pages[0].viewport.width);
}

function fitToPage() {
    if (!state.pages.length) return;
    state.fitMode = 'page';
    const containerW = scrollContainer.clientWidth - 20;
    const containerH = scrollContainer.clientHeight - 20;
    const vp = state.pages[0].viewport;
    setZoom(Math.min(containerW / vp.width, containerH / vp.height));
}

function updateCurrentPage() {
    const mid = scrollContainer.scrollTop + scrollContainer.clientHeight / 2;
    let cum = 0;
    for (let i = 0; i < state.pages.length; i++) {
        cum += state.pages[i].wrapper.offsetHeight + 12;
        if (cum > mid) { state.currentPage = i + 1; pageInput.value = i + 1; return; }
    }
}

function goToPage(num) {
    num = Math.max(1, Math.min(state.totalPages, num));
    state.currentPage = num;
    pageInput.value = num;
    state.pages[num - 1]?.wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ========== 분필 텍스처 브러시 (pdf_viewer.py _make_pen TOOL_CHALK 포팅) ==========
function createChalkBrushPattern(color) {
    const size = 32;
    const offscreen = document.createElement('canvas');
    offscreen.width = size; offscreen.height = size;
    const ctx = offscreen.getContext('2d');
    const rng = mulberry32(777);
    const cx = size / 2, cy = size / 2;
    const r = parseInt(color.slice(1, 3), 16) || 255;
    const g = parseInt(color.slice(3, 5), 16) || 255;
    const b = parseInt(color.slice(5, 7), 16) || 255;

    for (let ty = 0; ty < size; ty++) {
        for (let tx = 0; tx < size; tx++) {
            const dist = Math.sqrt((tx - cx) ** 2 + (ty - cy) ** 2) / (size / 2);
            const skipChance = 0.01 + dist * 0.35;
            if (rng() < skipChance) continue;
            const a = Math.max(60, Math.min(240, Math.floor(240 - dist * 120 + gaussRandom(rng) * 30)));
            ctx.fillStyle = `rgba(${r},${g},${b},${a / 255})`;
            ctx.fillRect(tx, ty, 1, 1);
        }
    }
    return ctx.createPattern(offscreen, 'repeat');
}

// ========== 그리기 (pdf_viewer.py 방식: 페이지 draw canvas에 직접 그리기) ==========
const fixedCanvas = $('fixed-draw-canvas');
// 이벤트 수신 + 터치 스크롤용 투명 오버레이 (canvas가 아닌 div)

// 화면 좌표 → 페이지 좌표 변환
function screenToPageCoord(clientX, clientY) {
    for (let i = 0; i < state.pages.length; i++) {
        const pd = state.pages[i];
        if (!pd.wrapper) continue;
        const rect = pd.wrapper.getBoundingClientRect();
        if (clientY >= rect.top && clientY <= rect.bottom && clientX >= rect.left && clientX <= rect.right) {
            return {
                pageNum: i + 1,
                x: (clientX - rect.left) * pd.viewport.width / rect.width,
                y: (clientY - rect.top) * pd.viewport.height / rect.height,
            };
        }
    }
    return null;
}

function getPagePoint(e, pageNum) {
    const pd = state.pages[pageNum - 1];
    if (!pd?.wrapper) return null;
    const rect = pd.wrapper.getBoundingClientRect();
    return {
        x: (e.clientX - rect.left) * pd.viewport.width / rect.width,
        y: (e.clientY - rect.top) * pd.viewport.height / rect.height,
        pressure: e.pressure || 0.5,
    };
}

// 손가락 터치로 스크롤
let _touchStartX = null, _touchStartY = null;
fixedCanvas.addEventListener('touchstart', e => {
    if (e.touches.length === 1) {
        _touchStartX = e.touches[0].clientX;
        _touchStartY = e.touches[0].clientY;
    }
}, { passive: true });
fixedCanvas.addEventListener('touchmove', e => {
    if (state.drawing) { e.preventDefault(); return; }
    if (e.touches.length === 1 && _touchStartY !== null) {
        const dx = _touchStartX - e.touches[0].clientX;
        const dy = _touchStartY - e.touches[0].clientY;
        scrollContainer.scrollLeft += dx;
        scrollContainer.scrollTop += dy;
        _touchStartX = e.touches[0].clientX;
        _touchStartY = e.touches[0].clientY;
        e.preventDefault();
    }
}, { passive: false });
fixedCanvas.addEventListener('touchend', () => { _touchStartX = null; _touchStartY = null; }, { passive: true });
fixedCanvas.addEventListener('touchcancel', () => { _touchStartX = null; _touchStartY = null; }, { passive: true });

// pointerdown: 그리기 시작
fixedCanvas.addEventListener('pointerdown', e => {
    if (e.pointerType === 'touch') return;
    e.preventDefault();
    if (isOverEraser(e.clientX, e.clientY)) { startEraserDrag(e); return; }
    const hit = screenToPageCoord(e.clientX, e.clientY);
    if (!hit) return;
    state.drawing = true;
    state._activePageNum = hit.pageNum;
    state.currentPath = [{ x: hit.x, y: hit.y, pressure: e.pressure || 0.5 }];

    // 기존 그림 백업 (offscreen canvas에 복사)
    const pd = state.pages[hit.pageNum - 1];
    if (pd?.drawCanvas) {
        if (!pd._backCanvas) {
            pd._backCanvas = document.createElement('canvas');
            pd._backCanvas.width = pd.drawCanvas.width;
            pd._backCanvas.height = pd.drawCanvas.height;
        }
        const bctx = pd._backCanvas.getContext('2d');
        bctx.clearRect(0, 0, pd._backCanvas.width, pd._backCanvas.height);
        bctx.drawImage(pd.drawCanvas, 0, 0);

        // draw context에 스타일 설정 (pointermove에서 재사용)
        const ctx = pd.drawCtx;
        const tool = state.tool, color = state.color, w = state.width;
        if (tool === 'highlighter') {
            ctx.globalAlpha = 80 / 255; ctx.strokeStyle = color; ctx.lineWidth = w * 4;
        } else if (tool === 'chalk') {
            ctx.globalAlpha = 0.9; ctx.strokeStyle = color; ctx.lineWidth = w * 2.5;
        } else {
            ctx.globalAlpha = 1.0; ctx.strokeStyle = color; ctx.lineWidth = w;
        }
        ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        // 시작 점 즉시 그리기
        ctx.beginPath();
        ctx.arc(hit.x, hit.y, ctx.lineWidth / 2, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
    }
    lockScroll();
}, { passive: false });

// pointermove: 세그먼트 추가 방식 (백업 복원 없음 — 고성능)
fixedCanvas.addEventListener('pointermove', e => {
    if (e.pointerType === 'touch') return;
    if (state.eraserDragging) {
        moveEraser(e);
        // 지우개: 5프레임에 1번만 판정 (성능)
        state._eraseCounter = (state._eraseCounter || 0) + 1;
        if (state._eraseCounter % 3 === 0) {
            const hit = screenToPageCoord(e.clientX, e.clientY);
            if (hit) eraseUnderEraser(hit.pageNum);
        }
        return;
    }
    if (!state.drawing || !state._activePageNum) return;
    e.preventDefault();
    const pt = getPagePoint(e, state._activePageNum);
    if (!pt) return;

    const prev = state.currentPath[state.currentPath.length - 1];
    state.currentPath.push(pt);

    // 이전 점 → 현재 점을 직접 stroke (전체 재그리기 없음)
    const pd = state.pages[state._activePageNum - 1];
    if (!pd?.drawCtx) return;
    const ctx = pd.drawCtx;
    ctx.beginPath();
    ctx.moveTo(prev.x, prev.y);
    ctx.lineTo(pt.x, pt.y);
    ctx.stroke();
}, { passive: false });

// pointerup: 아이템 저장 + 전체 경로를 베지어 곡선으로 다시 그려서 부드럽게
fixedCanvas.addEventListener('pointerup', e => {
    if (e.pointerType === 'touch') return;
    if (state.eraserDragging) { stopEraserDrag(); return; }
    if (!state.drawing) return;
    state.drawing = false;
    unlockScroll();
    const pageNum = state._activePageNum;
    // globalAlpha 복원
    const pd = state.pages[pageNum - 1];
    if (pd?.drawCtx) pd.drawCtx.globalAlpha = 1.0;

    if (state.currentPath.length > 1 && pageNum) {
        const item = { path: [...state.currentPath], color: state.color, width: state.width, tool: state.tool };
        item.path2d = buildPath2D(item.path, item.width);
        state.drawItems[pageNum].push(item);
        // lineTo로 그린 것을 베지어 곡선으로 교체 (부드럽게)
        redrawPage(pageNum);
    }
    state.currentPath = [];
    state._activePageNum = null;
    saveState();
});

fixedCanvas.addEventListener('pointerleave', e => {
    if (state.drawing) fixedCanvas.dispatchEvent(new PointerEvent('pointerup', e));
});
fixedCanvas.addEventListener('dragstart', e => e.preventDefault());
fixedCanvas.addEventListener('selectstart', e => e.preventDefault());
fixedCanvas.addEventListener('contextmenu', e => e.preventDefault());

function setupDrawEvents(canvas, pageNum) { /* 고정 캔버스가 처리 */ }
function lockScroll() {
    state._savedScrollTop = scrollContainer.scrollTop;
    state._savedScrollLeft = scrollContainer.scrollLeft;
}
function unlockScroll() {
    scrollContainer.scrollTop = state._savedScrollTop;
    scrollContainer.scrollLeft = state._savedScrollLeft;
}
// scroll 이벤트에서 그리기 중이면 즉시 복원
scrollContainer.addEventListener('scroll', () => {
    if (state.drawing) {
        scrollContainer.scrollTop = state._savedScrollTop;
        scrollContainer.scrollLeft = state._savedScrollLeft;
    }
});

// Path2D 빌드 (정밀 지우개 판정용)
function buildPath2D(path, width) {
    const p = new Path2D();
    if (path.length < 2) return p;
    p.moveTo(path[0].x, path[0].y);
    for (let i = 1; i < path.length; i++) {
        const prev = path[i - 1], curr = path[i];
        p.quadraticCurveTo(prev.x, prev.y, (prev.x + curr.x) / 2, (prev.y + curr.y) / 2);
    }
    p.lineTo(path[path.length - 1].x, path[path.length - 1].y);
    return p;
}

function drawPath(ctx, path, tool, color, width) {
    if (path.length < 2) return;
    ctx.save();

    if (tool === 'highlighter') {
        ctx.globalAlpha = 80 / 255; // pdf_viewer.py: alpha=80
        ctx.strokeStyle = color;
        ctx.lineWidth = width * 4;
    } else if (tool === 'chalk') {
        ctx.globalAlpha = 0.9;
        const pattern = createChalkBrushPattern(color);
        ctx.strokeStyle = pattern;
        ctx.lineWidth = width * 2.5;
    } else {
        ctx.globalAlpha = 1.0;
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
    }

    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(path[0].x, path[0].y);
    if (path.length === 2) {
        // 2포인트: 직선 연결 (베지어 곡선 불필요)
        ctx.lineTo(path[1].x, path[1].y);
    } else {
        // 3포인트 이상: 첫 세그먼트는 lineTo, 이후 베지어 곡선
        ctx.lineTo((path[0].x + path[1].x) / 2, (path[0].y + path[1].y) / 2);
        for (let i = 1; i < path.length - 1; i++) {
            const curr = path[i], next = path[i + 1];
            ctx.quadraticCurveTo(curr.x, curr.y, (curr.x + next.x) / 2, (curr.y + next.y) / 2);
        }
        const last = path[path.length - 1];
        ctx.lineTo(last.x, last.y);
    }
    ctx.stroke();
    ctx.restore();
}

function redrawPage(pageNum) {
    const pd = state.pages[pageNum - 1];
    if (!pd?.drawCtx) return;
    pd.drawCtx.clearRect(0, 0, pd.viewport.width, pd.viewport.height);
    for (const item of (state.drawItems[pageNum] || [])) {
        drawPath(pd.drawCtx, item.path, item.tool, item.color, item.width);
    }
}

// ========== 칠판 텍스처 (pdf_viewer.py _create_chalkboard_texture 포팅) ==========
function generateChalkTexture() {
    const size = 1024;
    const c = document.createElement('canvas');
    c.width = size; c.height = size;
    const ctx = c.getContext('2d');
    ctx.fillStyle = 'rgb(30,53,32)';
    ctx.fillRect(0, 0, size, size);

    const rng = mulberry32(42);
    const imgData = ctx.getImageData(0, 0, size, size);
    const d = imgData.data;
    for (let i = 0; i < 15000; i++) {
        const x = Math.floor(rng() * size), y = Math.floor(rng() * size);
        const v = gaussRandom(rng) * 6, a = Math.floor(rng() * 35 + 20);
        const idx = (y * size + x) * 4;
        const srcA = a / 255;
        d[idx] = Math.floor(d[idx] * (1 - srcA) + Math.max(0, Math.min(255, 42 + v)) * srcA);
        d[idx + 1] = Math.floor(d[idx + 1] * (1 - srcA) + Math.max(0, Math.min(255, 69 + v * 1.1)) * srcA);
        d[idx + 2] = Math.floor(d[idx + 2] * (1 - srcA) + Math.max(0, Math.min(255, 40 + v)) * srcA);
    }
    ctx.putImageData(imgData, 0, 0);

    ctx.strokeStyle = 'rgba(255,255,255,0.047)'; ctx.lineWidth = 1;
    for (let x = 0; x < size; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, size); ctx.stroke(); }
    for (let y = 0; y < size; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(size, y); ctx.stroke(); }

    for (let i = 0; i < 40; i++) {
        const x = rng() * (size - 40) + 20, y = rng() * (size - 40) + 20;
        const w = rng() * 42 + 8, h = rng() * 4 + 2;
        ctx.save(); ctx.translate(x, y); ctx.rotate((rng() - 0.5) * 40 * Math.PI / 180);
        ctx.fillStyle = `rgba(200,200,190,${(rng() * 7 + 3) / 255})`;
        ctx.beginPath(); ctx.ellipse(0, 0, w / 2, h / 2, 0, 0, Math.PI * 2); ctx.fill();
        ctx.restore();
    }
    for (let i = 0; i < 25; i++) {
        const x1 = rng() * (size - 20) + 10, y1 = rng() * (size - 20) + 10;
        const len = rng() * 30 + 5, ang = gaussRandom(rng) * 40 * Math.PI / 180;
        ctx.strokeStyle = `rgba(80,130,75,${(rng() * 12 + 8) / 255})`;
        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x1 + len * Math.cos(ang), y1 + len * Math.sin(ang)); ctx.stroke();
    }
    return c;
}

function enterChalkboard() {
    state.chalkboardMode = true;
    document.body.classList.add('chalkboard-mode');
    pdfMode.classList.remove('active');
    chalkMode.classList.add('active');
    if ($('btn-chalkboard')) $('btn-chalkboard').textContent = '🟩ON';
    const ecb = $('eraser-chalk-btn');
    if (ecb) { ecb.textContent = 'ON'; ecb.classList.add('on'); }

    resizeChalkCanvas();
    if (!state.chalkTexture) state.chalkTexture = generateChalkTexture();
    redrawChalkboard();

    const now = new Date();
    chalkDate.textContent = `${now.getFullYear()}. ${now.getMonth() + 1}. ${now.getDate()}.`;

    state.savedColor = state.color;
    state.savedTool = state.tool;
    state.color = '#ffffff';
    state.tool = 'chalk';
    // 썸네일 숨김
    state._thumbsWasVisible = state.thumbsVisible;
    if (state.thumbsVisible) toggleThumbnails();
    updateUI();
    // 지우개가 숨겨져 있으면 표시만 (위치 유지)
    if (eraserPanel.style.display === 'none') showEraser();
}

function exitChalkboard() {
    state.chalkboardMode = false;
    document.body.classList.remove('chalkboard-mode');
    chalkMode.classList.remove('active');
    pdfMode.classList.add('active');
    if ($('btn-chalkboard')) $('btn-chalkboard').textContent = '🟩OFF';
    const ecb2 = $('eraser-chalk-btn');
    if (ecb2) { ecb2.textContent = 'OFF'; ecb2.classList.remove('on'); }
    state.color = state.savedColor || '#ff0000';
    state.tool = state.savedTool || 'pen';
    // 썸네일 복원
    if (state._thumbsWasVisible && !state.thumbsVisible) toggleThumbnails();
    updateUI();
}

function resizeChalkCanvas() {
    const frame = $('chalk-frame');
    const dpr = window.devicePixelRatio || 1;
    chalkCanvas.width = frame.clientWidth * dpr;
    chalkCanvas.height = frame.clientHeight * dpr;
    chalkCtx.scale(dpr, dpr);
    chalkCanvas.style.width = frame.clientWidth + 'px';
    chalkCanvas.style.height = frame.clientHeight + 'px';
}

function redrawChalkboard() {
    const dpr = window.devicePixelRatio || 1;
    const w = chalkCanvas.width / dpr, h = chalkCanvas.height / dpr;
    if (state.chalkTexture) {
        const pat = chalkCtx.createPattern(state.chalkTexture, 'repeat');
        chalkCtx.fillStyle = pat;
        chalkCtx.fillRect(0, 0, w, h);
    }
    for (const item of state.chalkItems) drawPath(chalkCtx, item.path, item.tool, item.color, item.width);
}

// 칠판 그리기 이벤트
function setupChalkEvents() {
    const onDown = e => {
        if (e.pointerType === 'touch') return;
        e.preventDefault();
        if (isOverEraser(e.clientX, e.clientY)) { startEraserDrag(e); return; }
        state.drawing = true;
        state.lastPoint = getChalkPoint(e);
        state.currentPath = [state.lastPoint];
        chalkCanvas.setPointerCapture(e.pointerId);
    };
    const onMove = e => {
        if (e.pointerType === 'touch') return;
        if (state.eraserDragging) { moveEraser(e); eraseUnderEraserChalk(); return; }
        if (!state.drawing) return;
        e.preventDefault();
        const pt = getChalkPoint(e);
        state.currentPath.push(pt);
        redrawChalkboard();
        drawPath(chalkCtx, state.currentPath, state.tool, state.color, state.width * Math.max(pt.pressure || 0.5, 0.3));
    };
    const endDraw = () => {
        if (state.eraserDragging) { stopEraserDrag(); return; }
        if (!state.drawing) return;
        state.drawing = false;
        if (state.currentPath.length > 1) {
            state.chalkItems.push({ path: [...state.currentPath], color: state.color, width: state.width, tool: state.tool });
        }
        state.currentPath = [];
        redrawChalkboard();
    };
    chalkCanvas.addEventListener('pointerdown', onDown);
    chalkCanvas.addEventListener('pointermove', onMove);
    chalkCanvas.addEventListener('pointerup', endDraw);
    chalkCanvas.addEventListener('pointerleave', endDraw);
}

function getChalkPoint(e) {
    const rect = chalkCanvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    return {
        x: (e.clientX - rect.left) * (chalkCanvas.width / dpr) / rect.width,
        y: (e.clientY - rect.top) * (chalkCanvas.height / dpr) / rect.height,
        pressure: e.pressure || 0.5,
    };
}

// ========== 지우개 (와이퍼 기울기 + 흔들림) ==========
function showEraser() {
    eraserPanel.style.display = 'block';
    const appRect = $('app').getBoundingClientRect();
    const ew = eraserPanel.offsetWidth || 600;
    eraserPanel.style.left = (appRect.right - ew - 20) + 'px';
    eraserPanel.style.top = '20px';
    updateEraserTransform();
}

function updateEraserTransform() {
    const angle = state.eraserAngle + state.eraserWobble;
    const img = $('eraser-img');
    if (img) img.style.transform = `rotate(${-10 + angle}deg)`;
}

function isOverEraser(cx, cy) {
    if (eraserPanel.style.display === 'none') return false;
    const r = eraserPanel.getBoundingClientRect();
    return cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom;
}

function startEraserDrag(e) {
    state.eraserDragging = true;
    const r = eraserPanel.getBoundingClientRect();
    state.eraserOffset = { x: e.clientX - r.left, y: e.clientY - r.top };
    state.eraserRecentDx = [];
    eraserPanel.style.cursor = 'grabbing';
}

function moveEraser(e) {
    const ew = eraserPanel.offsetWidth, eh = eraserPanel.offsetHeight;
    const maxX = window.innerWidth - ew, maxY = window.innerHeight - eh;
    let newLeft = e.clientX - state.eraserOffset.x;
    let newTop = e.clientY - state.eraserOffset.y;
    newLeft = Math.max(0, Math.min(maxX, newLeft));
    newTop = Math.max(0, Math.min(maxY, newTop));
    const oldLeft = parseFloat(eraserPanel.style.left) || 0;
    const dx = newLeft - oldLeft;
    eraserPanel.style.left = newLeft + 'px';
    eraserPanel.style.top = newTop + 'px';

    // 와이퍼 기울기 (pdf_viewer.py _move_drag 포팅)
    state.eraserRecentDx.push(dx);
    if (state.eraserRecentDx.length > 5) state.eraserRecentDx.shift();
    const avgDx = state.eraserRecentDx.reduce((a, b) => a + b, 0) / state.eraserRecentDx.length;
    const targetAngle = Math.max(-55, Math.min(55, avgDx * 5));
    state.eraserAngle += (targetAngle - state.eraserAngle) * 0.3;

    // 흔들림 (미세 진동)
    state.eraserWobble = Math.sin(Date.now() / 80) * 2;
    updateEraserTransform();
}

function stopEraserDrag() {
    state.eraserDragging = false;
    eraserPanel.style.cursor = 'grab';
    state.eraserAngle = 0;
    state.eraserWobble = 0;
    updateEraserTransform();
}

// 지우개 정밀 판정 (pdf_viewer.py 2단계: BoundingBox → shape().intersects)
function eraseUnderEraser(pageNum) {
    const er = eraserPanel.getBoundingClientRect();
    // 실제 이미지 영역만 판정 (중앙 50% 영역)
    const padX = er.width * 0.25, padY = er.height * 0.25;
    const hitRect = {
        left: er.left + padX, right: er.right - padX,
        top: er.top + padY, bottom: er.bottom - padY,
    };
    const pd = state.pages[pageNum - 1];
    if (!pd?.drawCanvas) return;
    const cr = pd.drawCanvas.getBoundingClientRect();
    const vp = pd.viewport;
    const sx = vp.width / cr.width, sy = vp.height / cr.height;

    const eLeft = (hitRect.left - cr.left) * sx, eRight = (hitRect.right - cr.left) * sx;
    const eTop = (hitRect.top - cr.top) * sy, eBottom = (hitRect.bottom - cr.top) * sy;

    state.drawItems[pageNum] = state.drawItems[pageNum].filter(item => {
        // BoundingBox 겹침 → 경로 점 하나라도 지우개 영역 안이면 삭제
        for (const pt of item.path) {
            if (pt.x >= eLeft && pt.x <= eRight && pt.y >= eTop && pt.y <= eBottom) return false;
        }
        return true;
    });
    redrawPage(pageNum);
}

function eraseUnderEraserChalk() {
    const er = eraserPanel.getBoundingClientRect();
    const padX = er.width * 0.25, padY = er.height * 0.25;
    const hitRect = {
        left: er.left + padX, right: er.right - padX,
        top: er.top + padY, bottom: er.bottom - padY,
    };
    const cr = chalkCanvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const w = chalkCanvas.width / dpr, h = chalkCanvas.height / dpr;
    const sx = w / cr.width, sy = h / cr.height;
    const eLeft = (hitRect.left - cr.left) * sx, eRight = (hitRect.right - cr.left) * sx;
    const eTop = (hitRect.top - cr.top) * sy, eBottom = (hitRect.bottom - cr.top) * sy;

    state.chalkItems = state.chalkItems.filter(item => {
        for (const pt of item.path) {
            if (pt.x >= eLeft && pt.x <= eRight && pt.y >= eTop && pt.y <= eBottom) return false;
        }
        return true;
    });
    redrawChalkboard();
}

// 지우개 패널 직접 드래그
eraserPanel.addEventListener('pointerdown', e => {
    e.preventDefault();
    startEraserDrag(e);
    const onMove = ev => {
        moveEraser(ev);
        if (state.chalkboardMode) { eraseUnderEraserChalk(); }
        else {
            for (let i = 0; i < state.pages.length; i++) {
                const r = state.pages[i].wrapper.getBoundingClientRect();
                if (ev.clientY >= r.top && ev.clientY <= r.bottom) { eraseUnderEraser(i + 1); break; }
            }
        }
    };
    const onUp = () => { stopEraserDrag(); document.removeEventListener('pointermove', onMove); document.removeEventListener('pointerup', onUp); };
    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp);
});

// ========== 핀치 줌 (Touch API — 손가락 중심 기준 줌) ==========
function touchDist(t) {
    return Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
}
function touchCenter(t) {
    return {
        x: (t[0].clientX + t[1].clientX) / 2,
        y: (t[0].clientY + t[1].clientY) / 2,
    };
}

document.addEventListener('touchstart', e => {
    if (e.touches.length === 2 && !state.chalkboardMode) {
        state.pinchStartDist = touchDist(e.touches);
        state.pinchStartZoom = state.zoom;
        // 핀치 중심의 스크롤 컨테이너 내 위치 저장
        const center = touchCenter(e.touches);
        const cr = scrollContainer.getBoundingClientRect();
        state._pinchCenterX = center.x - cr.left + scrollContainer.scrollLeft;
        state._pinchCenterY = center.y - cr.top + scrollContainer.scrollTop;
        state._pinchScreenX = center.x - cr.left;
        state._pinchScreenY = center.y - cr.top;
        state._eraserFixedLeft = eraserPanel.style.left;
        state._eraserFixedTop = eraserPanel.style.top;
        e.preventDefault();
    }
}, { passive: false });

document.addEventListener('touchmove', e => {
    if (e.touches.length === 2 && state.pinchStartDist > 0 && !state.chalkboardMode) {
        e.preventDefault();
        const dist = touchDist(e.touches);
        const newZoom = state.pinchStartZoom * dist / state.pinchStartDist;
        const oldZoom = state.zoom;
        state.fitMode = null;
        setZoom(newZoom);
        // 핀치 중심을 화면 같은 위치에 유지 (pdf_viewer.py centerOn 포팅)
        const ratio = state.zoom / state.pinchStartZoom;
        scrollContainer.scrollLeft = state._pinchCenterX * ratio - state._pinchScreenX;
        scrollContainer.scrollTop = state._pinchCenterY * ratio - state._pinchScreenY;
        eraserPanel.style.left = state._eraserFixedLeft;
        eraserPanel.style.top = state._eraserFixedTop;
    }
}, { passive: false });

document.addEventListener('touchend', e => {
    if (e.touches.length < 2) state.pinchStartDist = 0;
});
document.addEventListener('touchcancel', () => { state.pinchStartDist = 0; });

// ========== 전체화면 + 하단 터치 시 툴바 표시 ==========
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        $('app').requestFullscreen().catch(() => {});
        document.body.classList.add('fullscreen-mode');
    } else {
        document.exitFullscreen().catch(() => {});
        document.body.classList.remove('fullscreen-mode');
    }
}
document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement) document.body.classList.remove('fullscreen-mode');
});

// 전체화면 PDF 모드: 하단 5px 터치 시 툴바 표시
document.addEventListener('pointermove', e => {
    if (!document.fullscreenElement || state.chalkboardMode) return;
    const appH = $('app').getBoundingClientRect().bottom;
    if (appH - e.clientY < 5) {
        toolbar.style.display = 'flex';
    } else if (appH - e.clientY > 50 && toolbar.style.display === 'flex') {
        if (document.body.classList.contains('fullscreen-mode') && !state.chalkboardMode) {
            toolbar.style.display = '';
        }
    }
});

// ========== 칠판↔PDF 슬라이드 전환 애니메이션 ==========
function slideTransition(toChalk) {
    const from = toChalk ? pdfMode : chalkMode;
    const to = toChalk ? chalkMode : pdfMode;
    const dir = toChalk ? -1 : 1;

    // 지우개 위치 저장
    const eraserLeft = eraserPanel.style.left;
    const eraserTop = eraserPanel.style.top;

    to.classList.add('active');
    to.style.transform = `translateX(${-dir * 100}%)`;
    from.style.transition = 'transform 0.35s ease';
    to.style.transition = 'transform 0.35s ease';

    requestAnimationFrame(() => {
        from.style.transform = `translateX(${dir * 100}%)`;
        to.style.transform = 'translateX(0)';
    });

    setTimeout(() => {
        from.classList.remove('active');
        from.style.transform = '';
        from.style.transition = '';
        to.style.transition = '';
        // 지우개 위치 복원
        eraserPanel.style.left = eraserLeft;
        eraserPanel.style.top = eraserTop;
    }, 360);
}

// ========== 썸네일 패널 ==========
async function generateThumbnails() {
    if (!thumbPanel) return;
    thumbPanel.innerHTML = '';
    for (let i = 1; i <= state.totalPages; i++) {
        const page = await state.pdfDoc.getPage(i);
        const vp = page.getViewport({ scale: 0.2 }); // 저해상도
        const canvas = document.createElement('canvas');
        canvas.width = vp.width;
        canvas.height = vp.height;
        const ctx = canvas.getContext('2d');
        await page.render({ canvasContext: ctx, viewport: vp }).promise;

        const item = document.createElement('div');
        item.className = 'thumb-item';
        item.dataset.page = i;
        item.innerHTML = `<span class="thumb-num">${i}</span>`;
        item.prepend(canvas);
        item.addEventListener('click', () => goToPage(i));
        thumbPanel.appendChild(item);
    }
}

function toggleThumbnails() {
    state.thumbsVisible = !state.thumbsVisible;
    if (thumbPanel) thumbPanel.classList.toggle('visible', state.thumbsVisible);
    $('btn-thumbs')?.classList.toggle('active', state.thumbsVisible);
}

// ========== 이미지 PDF 변환 (클라이언트 단독) ==========
async function exportImagePDF() {
    if (!state.pdfDoc) return;
    // jsPDF 동적 로드
    if (!window.jspdf) {
        await new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.2/jspdf.umd.min.js';
            s.onload = resolve; s.onerror = reject;
            document.head.appendChild(s);
        });
    }
    const { jsPDF } = window.jspdf;

    const pdf = new jsPDF();
    for (let i = 1; i <= state.totalPages; i++) {
        const page = await state.pdfDoc.getPage(i);
        const vp = page.getViewport({ scale: 150 / 72 }); // 150 DPI
        const canvas = document.createElement('canvas');
        canvas.width = vp.width; canvas.height = vp.height;
        const ctx = canvas.getContext('2d');
        await page.render({ canvasContext: ctx, viewport: vp }).promise;

        const imgData = canvas.toDataURL('image/jpeg', 0.85);
        if (i > 1) pdf.addPage();
        const pdfW = pdf.internal.pageSize.getWidth();
        const pdfH = pdf.internal.pageSize.getHeight();
        pdf.addImage(imgData, 'JPEG', 0, 0, pdfW, pdfH);
    }
    pdf.save('이미지변환.pdf');
}

// ========== UI 업데이트 ==========
function updateUI() {
    colorDot.style.background = state.color;
    const bar = $('width-bar');
    if (bar) bar.style.height = Math.max(2, state.width) + 'px';
    document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
    const map = { pen: 'btn-pen', highlighter: 'btn-highlighter', chalk: 'btn-chalk' };
    $(map[state.tool])?.classList.add('active');
}

// ========== 이벤트 바인딩 ==========
$('btn-back').addEventListener('click', () => window.location.href = window.BACK_URL);
$('btn-zin').addEventListener('click', () => { state.fitMode = null; setZoom(state.zoom + 0.1); });
$('btn-zout').addEventListener('click', () => { state.fitMode = null; setZoom(state.zoom - 0.1); });
$('btn-fit-width').addEventListener('click', fitToWidth);
$('btn-fit-page').addEventListener('click', fitToPage);
pageInput.addEventListener('change', () => goToPage(parseInt(pageInput.value) || 1));

$('btn-pen').addEventListener('click', () => { state.tool = 'pen'; updateUI(); saveState(); });
$('btn-highlighter').addEventListener('click', () => { state.tool = 'highlighter'; updateUI(); saveState(); });
$('btn-chalk').addEventListener('click', () => { state.tool = 'chalk'; updateUI(); saveState(); });

$('btn-color').addEventListener('click', e => {
    e.stopPropagation(); widthPopup.style.display = 'none';
    colorPopup.style.display = colorPopup.style.display === 'none' ? 'block' : 'none';
    colorPopup.style.left = $('btn-color').getBoundingClientRect().left + 'px';
});
document.querySelectorAll('.color-swatch').forEach(btn => {
    btn.addEventListener('click', () => { state.color = btn.dataset.color; updateUI(); colorPopup.style.display = 'none'; saveState(); });
});

// 굵기 팝업
$('btn-width').addEventListener('click', e => {
    e.stopPropagation(); colorPopup.style.display = 'none';
    widthPopup.style.display = widthPopup.style.display === 'none' ? 'block' : 'none';
    widthPopup.style.left = $('btn-width').getBoundingClientRect().left + 'px';
    // 현재 선택 표시
    document.querySelectorAll('.width-option').forEach(opt => {
        opt.classList.toggle('active', parseInt(opt.dataset.width) === state.width);
    });
});
document.querySelectorAll('.width-option').forEach(opt => {
    opt.addEventListener('click', () => {
        state.width = parseInt(opt.dataset.width);
        // 버튼 아이콘 두께 업데이트
        const bar = $('width-bar');
        if (bar) bar.style.height = Math.max(2, state.width) + 'px';
        widthPopup.style.display = 'none';
        saveState();
    });
});

document.addEventListener('click', e => {
    if (!colorPopup.contains(e.target) && e.target !== $('btn-color')) colorPopup.style.display = 'none';
    if (!widthPopup.contains(e.target) && e.target !== $('btn-width')) widthPopup.style.display = 'none';
});

$('btn-clear').addEventListener('click', () => {
    if (!confirm('전체 지우기 하시겠습니까?')) return;
    if (state.chalkboardMode) { state.chalkItems = []; redrawChalkboard(); }
    else { for (const k of Object.keys(state.drawItems)) state.drawItems[k] = []; for (let i = 1; i <= state.totalPages; i++) redrawPage(i); }
});

function toggleChalkboard() {
    if (state.chalkboardMode) { exitChalkboard(); slideTransition(false); }
    else { enterChalkboard(); slideTransition(true); }
    // 지우개 위 버튼 상태 업데이트
    const btn = $('eraser-chalk-btn');
    if (btn) {
        btn.textContent = state.chalkboardMode ? 'ON' : 'OFF';
        btn.classList.toggle('on', state.chalkboardMode);
    }
}
if ($('btn-chalkboard')) $('btn-chalkboard').addEventListener('click', toggleChalkboard);

// 지우개 위 칠판 ON/OFF 버튼
$('eraser-chalk-btn').addEventListener('pointerdown', e => {
    e.stopPropagation(); // 지우개 드래그 방지
});
$('eraser-chalk-btn').addEventListener('click', e => {
    e.stopPropagation();
    toggleChalkboard();
});

$('btn-fullscreen').addEventListener('click', toggleFullscreen);
$('btn-thumbs')?.addEventListener('click', toggleThumbnails);
$('btn-export')?.addEventListener('click', exportImagePDF);

document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && document.fullscreenElement) document.exitFullscreen();
});

window.addEventListener('resize', () => {
    if (state.fitMode === 'width') fitToWidth();
    else if (state.fitMode === 'page') fitToPage();
    if (state.chalkboardMode) { resizeChalkCanvas(); redrawChalkboard(); }
    // fixedCanvas는 크기 조정 불필요 (이벤트 수신용)
});

// ========== 브라우저 기본 핀치 줌 차단 ==========
document.addEventListener('gesturestart', e => e.preventDefault(), { passive: false });  // Safari
document.addEventListener('gesturechange', e => e.preventDefault(), { passive: false });
document.addEventListener('touchmove', e => {
    if (e.touches.length >= 2) e.preventDefault();  // 2손가락 이상 = 핀치 → 차단
}, { passive: false });
document.addEventListener('wheel', e => {
    if (e.ctrlKey) e.preventDefault();  // Ctrl+휠 줌 차단
}, { passive: false });

// ========== 초기화 ==========
restoreState();
updateUI();
setupChalkEvents();
showEraser();
// fixedCanvas는 div이므로 리사이즈 불필요
// 처음 실행 시 썸네일 패널 표시
state.thumbsVisible = true;
if (thumbPanel) thumbPanel.classList.add('visible');
$('btn-thumbs')?.classList.add('active');
loadPDF().catch(err => console.error('PDF load error:', err));

}); // end DOMContentLoaded
