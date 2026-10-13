const wordList = document.getElementById("wordList");
const pageInfo = document.getElementById("pageInfo");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const backHomeBtn = document.getElementById("backHomeBtn");

let currentPage = 1;
const limit = 10;
let totalPages = 1;

async function fetchWords(page) {
  try {
    wordList.innerHTML = `<div class="loading-text">불러오는 중...</div>`;

    const response = await fetch(`/api/words?page=${page}&limit=${limit}`);
    if (!response.ok) {
      throw new Error("데이터를 불러오지 못했습니다.");
    }

    const data = await response.json();

    currentPage = data.page;
    totalPages = data.total_pages;

    renderWords(data.items);
    renderPagination();
  } catch (error) {
    wordList.innerHTML = `<div class="error-text">오류가 발생했습니다.</div>`;
    pageInfo.textContent = "- / -";
    prevBtn.disabled = true;
    nextBtn.disabled = true;
    console.error(error);
  }
}

function renderWords(items) {
  if (!items || items.length === 0) {
    wordList.innerHTML = `<div class="empty-text">표시할 단어가 없습니다.</div>`;
    return;
  }

  wordList.innerHTML = "";

  items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "word-card";

    const safeReading = item.reading || "-";
    const safeMeaning = item.meaning || "-";
    const safeKanji = item.kanji || "-";

    card.innerHTML = `
      <div class="word-inner">
        <div class="word-left">
          <div class="yomi">${escapeHtml(safeReading)}</div>
          <div class="kanji">${escapeHtml(safeKanji)}</div>
        </div>
        <div class="meaning">${escapeHtml(safeMeaning)}</div>
      </div>
    `;

    const yomiEl = card.querySelector(".yomi");
    const meaningEl = card.querySelector(".meaning");

    yomiEl.addEventListener("click", () => {
      yomiEl.classList.toggle("hidden-text");
    });

    meaningEl.addEventListener("click", () => {
      meaningEl.classList.toggle("hidden-text");
    });

    wordList.appendChild(card);
  });
}

function renderPagination() {
  pageInfo.textContent = `${currentPage} / ${totalPages}`;
  prevBtn.disabled = currentPage <= 1;
  nextBtn.disabled = currentPage >= totalPages;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

prevBtn.addEventListener("click", () => {
  if (currentPage > 1) {
    fetchWords(currentPage - 1);
  }
});

nextBtn.addEventListener("click", () => {
  if (currentPage < totalPages) {
    fetchWords(currentPage + 1);
  }
});

backHomeBtn.addEventListener("click", () => {
  window.location.href = "/";
});

fetchWords(1);
